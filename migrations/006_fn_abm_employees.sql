-- ABM de clientes: un solo punto de entrada en la base.
-- p_accion: 'A' = alta, 'M' = modificación, 'B' = baja lógica (alterna habilitado / inhabilitado).
-- Las validaciones se hacen acá; los errores viajan a la API como excepciones con mensaje claro.
CREATE OR REPLACE FUNCTION fn_abm_employee(
    p_accion          text,
    p_id              int,
    p_lastname        text DEFAULT NULL,
    p_firstname       text DEFAULT NULL,
    p_title           text DEFAULT NULL,
    p_titleofcourtesy text DEFAULT NULL,
    p_birthdate       date DEFAULT NULL,
    p_hiredate        date DEFAULT NULL,
    p_address         text DEFAULT NULL,
    p_city            text DEFAULT NULL,
    p_region          text DEFAULT NULL,
    p_cp              text DEFAULT NULL,
    p_country         text DEFAULT NULL,
    p_homephone       text DEFAULT NULL,
    p_extension       text DEFAULT NULL,
    p_notes           text DEFAULT NULL,
    p_reportsto       int DEFAULT NULL,
    p_salary          numeric(10, 2) DEFAULT NULL,
    p_comission_pct   numeric(10, 2) DEFAULT NULL
) RETURNS text AS $$
DECLARE
    v_id        int;
    v_existe    boolean;
    v_disabled  boolean;
BEGIN
    -- 1) Acción válida
    p_accion := upper(trim(coalesce(p_accion, '')));
    IF p_accion NOT IN ('A', 'M', 'B') THEN
        RAISE EXCEPTION 'Acción inválida: "%". Use A (alta), M (modificación) o B (baja)', p_accion;
    END IF;

    -- 2) Código: obligatorio y entero positivo (serial)
    IF p_id IS NULL OR p_id <= 0 THEN
        RAISE EXCEPTION 'El ID del empleado debe ser un número entero positivo';
    END IF;

    v_id := p_id;
    v_existe := EXISTS(SELECT 1 FROM employees WHERE employeeid = v_id);
    SELECT disabled INTO v_disabled FROM employees WHERE employeeid = v_id;

    -- 3) Baja lógica: invierte el estado (inhabilitado <-> habilitado)
    IF p_accion = 'B' THEN
        IF NOT v_existe THEN
            RAISE EXCEPTION 'No existe el empleado %', v_id USING ERRCODE = 'no_data_found';
        END IF;

        UPDATE employees SET disabled = NOT disabled
        WHERE employeeid = v_id
        RETURNING disabled INTO v_disabled;
        RETURN format('Empleado %s %s', v_id, CASE WHEN v_disabled THEN 'inhabilitado' ELSE 'habilitado' END);
    END IF;

    -- 4) Alta y modificación: limpiar textos (espacios y vacíos -> NULL) y validar
    p_lastname        := nullif(trim(p_lastname), '');
    p_firstname       := nullif(trim(p_firstname), '');
    p_title           := nullif(trim(p_title), '');
    p_titleofcourtesy := nullif(trim(p_titleofcourtesy), '');
    p_address         := nullif(trim(p_address), '');
    p_city            := nullif(trim(p_city), '');
    p_region          := nullif(trim(p_region), '');
    p_cp              := nullif(trim(p_cp), '');
    p_country         := nullif(trim(p_country), '');
    p_homephone       := nullif(trim(p_homephone), '');
    p_extension       := nullif(trim(p_extension), '');
    p_notes           := nullif(trim(p_notes), '');

    -- 5) Validaciones
    IF p_firstname IS NULL THEN
        RAISE EXCEPTION 'El nombre del empleado es obligatorio';
    END IF;

    IF p_country IS NOT NULL AND length(p_country) > 3 THEN
        RAISE EXCEPTION 'El campo country admite como máximo 3 caracteres';
    END IF;

    IF p_salary IS NOT NULL AND p_salary < 0 THEN
        RAISE EXCEPTION 'El salario no puede ser negativo';
    END IF;

    IF p_birthdate IS NOT NULL AND p_birthdate > CURRENT_DATE THEN
        RAISE EXCEPTION 'La fecha de nacimiento no puede ser futura';
    END IF;

    IF p_hiredate IS NOT NULL AND p_hiredate > CURRENT_DATE THEN
        RAISE EXCEPTION 'La fecha de contratación no puede ser futura';
    END IF;

    IF p_reportsto IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employeeid = p_reportsto
        AND disabled = false
    ) THEN
        RAISE EXCEPTION 'El responsable indicado no existe o está inhabilitado';
    END IF;

    -- 6) Alta
    IF p_accion = 'A' THEN
        IF v_existe THEN
            RAISE EXCEPTION 'Ya existe un empleado con el código % (puede estar inhabilitado)', v_id
                USING ERRCODE = 'unique_violation';
        END IF;
        INSERT INTO employees(employeeid, lastname, firstname, title, titleofcourtesy, birthdate, hiredate, address, 
                            city, region, postalcode, country, homephone, extension, notes, reportsto, salary, comission_pct)        
        VALUES (v_id, p_lastname, p_firstname, p_title, p_titleofcourtesy, p_birthdate, p_hiredate, p_address, 
                p_city, p_region, p_cp, p_country, p_homephone, p_extension, p_notes, p_reportsto, p_salary, p_comission_pct);
        RETURN format('Empleado %s creado', v_id);
    END IF;

    -- 7) Modificación (solo empleados habilitados)
    IF NOT v_existe OR v_disabled THEN
        RAISE EXCEPTION 'No existe el empleado % o está inhabilitado', v_id USING ERRCODE = 'no_data_found';
    END IF;
    UPDATE employees
    SET lastname = p_lastname, firstname = p_firstname, title = p_title,
        titleofcourtesy = p_titleofcourtesy, birthdate = p_birthdate, hiredate = p_hiredate, address = p_address,
        city = p_city, region = p_region, postalcode = p_cp, country = p_country, homephone = p_homephone,
        extension = p_extension, notes = p_notes, reportsto = p_reportsto, salary = p_salary, comission_pct = p_comission_pct
    WHERE employeeid = v_id;
    RETURN format('Empleado %s modificado', v_id);
END;
$$ LANGUAGE plpgsql;
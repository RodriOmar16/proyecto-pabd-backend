-- ABM de clientes: un solo punto de entrada en la base.
-- p_accion: 'A' = alta, 'M' = modificación, 'B' = baja lógica (alterna habilitado / inhabilitado).
-- Las validaciones se hacen acá; los errores viajan a la API como excepciones con mensaje claro.
CREATE OR REPLACE FUNCTION fn_abm_cliente(
    p_accion    text,
    p_id        text,
    p_nombre    text DEFAULT NULL,
    p_contacto  text DEFAULT NULL,
    p_ciudad    text DEFAULT NULL,
    p_pais      text DEFAULT NULL,
    p_cargo     text DEFAULT NULL,
    p_direccion text DEFAULT NULL,
    p_region    text DEFAULT NULL,
    p_cp        text DEFAULT NULL,
    p_telefono  text DEFAULT NULL,
    p_fax       text DEFAULT NULL
) RETURNS text AS $$
DECLARE
    v_id        text;
    v_existe    boolean;
    v_disabled  boolean;
    -- Para validar largos máximos (mismos límites que las columnas de customers)
    v_campos    text[];
    v_valores   text[];
    v_maximos   int[] := ARRAY[40, 30, 15, 15, 30, 60, 15, 10, 24, 24];
BEGIN
    -- 1) Acción válida
    p_accion := upper(trim(coalesce(p_accion, '')));
    IF p_accion NOT IN ('A', 'M', 'B') THEN
        RAISE EXCEPTION 'Acción inválida: "%". Use A (alta), M (modificación) o B (baja)', p_accion;
    END IF;

    -- 2) Código: exactamente 5 letras
    v_id := upper(trim(coalesce(p_id, '')));
    IF v_id !~ '^[A-Z]{5}$' THEN
        RAISE EXCEPTION 'El código debe tener exactamente 5 letras';
    END IF;

    SELECT disabled INTO v_disabled FROM customers WHERE customerid = v_id;
    v_existe := FOUND;

    -- 3) Baja lógica: invierte el estado (inhabilitado <-> habilitado)
    IF p_accion = 'B' THEN
        IF NOT v_existe THEN
            RAISE EXCEPTION 'No existe el cliente %', v_id USING ERRCODE = 'no_data_found';
        END IF;
        UPDATE customers SET disabled = NOT disabled
        WHERE customerid = v_id
        RETURNING disabled INTO v_disabled;
        RETURN format('Cliente %s %s', v_id, CASE WHEN v_disabled THEN 'inhabilitado' ELSE 'habilitado' END);
    END IF;

    -- 4) Alta y modificación: limpiar textos (espacios y vacíos -> NULL) y validar
    p_nombre    := nullif(trim(p_nombre), '');
    p_contacto  := nullif(trim(p_contacto), '');
    p_ciudad    := nullif(trim(p_ciudad), '');
    p_pais      := nullif(trim(p_pais), '');
    p_cargo     := nullif(trim(p_cargo), '');
    p_direccion := nullif(trim(p_direccion), '');
    p_region    := nullif(trim(p_region), '');
    p_cp        := nullif(trim(p_cp), '');
    p_telefono  := nullif(trim(p_telefono), '');
    p_fax       := nullif(trim(p_fax), '');

    IF p_nombre IS NULL THEN
        RAISE EXCEPTION 'El nombre de la empresa es obligatorio';
    END IF;

    v_campos  := ARRAY['Empresa', 'Contacto', 'Ciudad', 'País', 'Cargo', 'Dirección',
                       'Región', 'Código postal', 'Teléfono', 'Fax'];
    v_valores := ARRAY[p_nombre, p_contacto, p_ciudad, p_pais, p_cargo, p_direccion,
                       p_region, p_cp, p_telefono, p_fax];
    FOR i IN 1 .. array_length(v_campos, 1) LOOP
        IF length(v_valores[i]) > v_maximos[i] THEN
            RAISE EXCEPTION 'El campo % admite como máximo % caracteres', v_campos[i], v_maximos[i];
        END IF;
    END LOOP;

    -- 5) Alta
    IF p_accion = 'A' THEN
        IF v_existe THEN
            RAISE EXCEPTION 'Ya existe un cliente con el código % (puede estar inhabilitado)', v_id
                USING ERRCODE = 'unique_violation';
        END IF;
        INSERT INTO customers (customerid, companyname, contactname, contacttitle, address,
                               city, region, postalcode, country, phone, fax)
        VALUES (v_id, p_nombre, p_contacto, p_cargo, p_direccion,
                p_ciudad, p_region, p_cp, p_pais, p_telefono, p_fax);
        RETURN format('Cliente %s creado', v_id);
    END IF;

    -- 6) Modificación (solo clientes habilitados)
    IF NOT v_existe OR v_disabled THEN
        RAISE EXCEPTION 'No existe el cliente % o está inhabilitado', v_id USING ERRCODE = 'no_data_found';
    END IF;
    UPDATE customers
    SET companyname = p_nombre, contactname = p_contacto, contacttitle = p_cargo,
        address = p_direccion, city = p_ciudad, region = p_region, postalcode = p_cp,
        country = p_pais, phone = p_telefono, fax = p_fax
    WHERE customerid = v_id;
    RETURN format('Cliente %s modificado', v_id);
END;
$$ LANGUAGE plpgsql;
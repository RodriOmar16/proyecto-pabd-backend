-- =====================================================================
-- 003: Consultas de clientes dentro de la base
--   * vw_clientes         -> QUÉ datos de un cliente ve la aplicación
--   * fn_consulta_cliente -> CÓMO se consultan (obtener uno / listar con
--                            filtros y paginado). Lee de la vista.
--   Las escrituras siguen en fn_abm_cliente (migración 002).
-- =====================================================================

-- ---------- Vista ----------
CREATE OR REPLACE VIEW vw_employees AS
SELECT
    e.employeeid,
    e.lastname,
    e.firstname,
    e.title,
    e.titleofcourtesy,
    e.birthdate,
    e.hiredate,
    e.address,
    e.city,
    e.region,
    e.postalcode  AS cp,
    e.country,
    e.homephone,
    e.extension,
    e.notes,
    e.reportsto,
    e.salary,
    e.comission_pct,
    e.disabled
FROM employees e;

-- ---------- Función de consulta ----------
-- Uso:
--   Obtener: SELECT * FROM fn_consulta_empleado(p_id => 1);
--   Listar:  SELECT * FROM fn_consulta_empleado(p_page => 1, p_size => 10, p_pais => 'mex');
-- Devuelve filas con las columnas de la vista + "total" (cantidad de registros
-- que cumplen los filtros, sin importar la página).
-- Filtros: NULL o texto vacío = no filtra. Se combinan con AND, sin distinguir mayúsculas.
CREATE OR REPLACE FUNCTION fn_consulta_empleado(
    p_id              int,
    p_disabled        boolean DEFAULT false,
    p_page            int DEFAULT 1,
    p_size            int DEFAULT 20,
    p_lastname        text DEFAULT NULL,
    p_firstname       text DEFAULT NULL,
    p_title           text DEFAULT NULL,
    p_titleofcourtesy text DEFAULT NULL,
    p_birthdate       date DEFAULT NULL,
    p_hiredate        date DEFAULT NULL,
    p_city            text DEFAULT NULL,
    p_region          text DEFAULT NULL,
    p_cp              text DEFAULT NULL,
    p_country         text DEFAULT NULL,
    p_reportsto       int DEFAULT NULL,
    p_comission_pct   numeric(10, 2) DEFAULT NULL
) RETURNS TABLE (
    employeeid      int,
    lastname        varchar,
    firstname       varchar,
    title           varchar,
    titleofcourtesy varchar,
    birthdate       date,
    hiredate        date,
    address         varchar,
    city            varchar,
    region          varchar,
    cp              varchar,
    country         varchar(3),
    homephone       varchar,
    extension       varchar,
    notes           text,
    reportsto       int,
    salary          numeric(12, 2),
    comission_pct   numeric(10, 2),
    disabled        boolean,
    total           bigint
) AS $$
-- las columnas de RETURNS TABLE (customerid, city…) 
-- también existen como variables dentro de la función. 
-- Esta línea le dice a PostgreSQL que, si un nombre es ambiguo, use la columna.
#variable_conflict use_column
BEGIN
    -- 1) Obtener un empleado (solo si está habilitado)
    IF p_id IS NOT NULL THEN
        RETURN QUERY
            SELECT v.employeeid, v.lastname, v.firstname,
                v.title, v.titleofcourtesy, v.birthdate, v.hiredate,
                v.address, v.city, v.region, v.cp,
                v.country, v.homephone, v.extension, v.notes,
                v.reportsto, v.salary, v.comission_pct,
                v.disabled, 1::bigint
            FROM vw_employees v
            WHERE v.employeeid = p_id AND NOT v.disabled;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'No existe el empleado % o está inhabilitado', p_id
                USING ERRCODE = 'no_data_found';
        END IF;
        RETURN;
    END IF;

    -- 2) Listar: validar paginación
    IF p_page IS NULL OR p_page < 1 THEN
        RAISE EXCEPTION 'La página debe ser mayor o igual a 1';
    END IF;
    IF p_size IS NULL OR p_size < 1 THEN
        RAISE EXCEPTION 'El tamaño de página debe ser mayor o igual a 1';
    END IF;
    p_size := least(p_size, 100);  -- máximo 100 registros por página

    -- Filtros vacíos -> NULL (no filtran)
    p_lastname        := nullif(trim(p_lastname), '');
    p_firstname       := nullif(trim(p_firstname), '');
    p_title           := nullif(trim(p_title), '');
    p_titleofcourtesy := nullif(trim(p_titleofcourtesy), '');
    p_city            := nullif(trim(p_city), '');
    p_region          := nullif(trim(p_region), '');
    p_cp              := nullif(trim(p_cp), '');
    p_country         := nullif(trim(p_country), '');

    -- count(*) OVER () se calcula antes del LIMIT: es el total filtrado, no el de la página
    RETURN QUERY
        SELECT v.employeeid, v.lastname, v.firstname,
            v.title, v.titleofcourtesy, v.birthdate, v.hiredate,
            v.address, v.city, v.region, v.cp,
            v.country, v.homephone, v.extension,
            v.notes, v.reportsto, v.salary, v.comission_pct,
            v.disabled, count(*) OVER ()
        FROM vw_employees v
        WHERE v.disabled = coalesce(p_disabled, false)
            AND (p_id              IS NULL OR v.employeeid    = p_id)
            AND (p_lastname        IS NULL OR v.lastname        ILIKE '%' || p_lastname        || '%')
            AND (p_firstname       IS NULL OR v.firstname       ILIKE '%' || p_firstname       || '%')
            AND (p_title           IS NULL OR v.title           ILIKE '%' || p_title           || '%')
            AND (p_titleofcourtesy IS NULL OR v.titleofcourtesy ILIKE '%' || p_titleofcourtesy || '%')
            AND (p_birthdate       IS NULL OR v.birthdate     = p_birthdate)
            AND (p_hiredate        IS NULL OR v.hiredate      = p_hiredate)
            AND (p_city            IS NULL OR v.city            ILIKE '%' || p_city            || '%')
            AND (p_region          IS NULL OR v.region          ILIKE '%' || p_region          || '%')
            AND (p_cp              IS NULL OR v.cp              ILIKE '%' || p_cp              || '%')
            AND (p_country         IS NULL OR v.country         ILIKE '%' || p_country         || '%')
            AND (p_reportsto       IS NULL OR v.reportsto     = p_reportsto)
            AND (p_comission_pct   IS NULL OR v.comission_pct = p_comission_pct)
        ORDER BY v.firstname, v.employeeid
        LIMIT p_size OFFSET (p_page - 1) * p_size;
END;
$$ LANGUAGE plpgsql;
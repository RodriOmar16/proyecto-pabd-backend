-- =====================================================================
-- 003: Consultas de clientes dentro de la base
--   * vw_clientes         -> QUÉ datos de un cliente ve la aplicación
--   * fn_consulta_cliente -> CÓMO se consultan (obtener uno / listar con
--                            filtros y paginado). Lee de la vista.
--   Las escrituras siguen en fn_abm_cliente (migración 002).
-- =====================================================================

-- ---------- Vista ----------
CREATE OR REPLACE VIEW vw_clientes AS
SELECT
    c.customerid,
    c.companyname,
    c.contactname,
    c.contacttitle,
    c.address,
    c.city,
    c.region,
    c.postalcode,
    c.country,
    c.phone,
    c.fax,
    c.disabled
FROM customers c;

-- ---------- Función de consulta ----------
-- Uso:
--   Obtener: SELECT * FROM fn_consulta_cliente(p_id => 'ALFKA');
--   Listar:  SELECT * FROM fn_consulta_cliente(p_page => 1, p_size => 10, p_pais => 'mex');
-- Devuelve filas con las columnas de la vista + "total" (cantidad de registros
-- que cumplen los filtros, sin importar la página).
-- Filtros: NULL o texto vacío = no filtra. Se combinan con AND, sin distinguir mayúsculas.
CREATE OR REPLACE FUNCTION fn_consulta_cliente(
    p_id        text    DEFAULT NULL,
    p_disabled  boolean DEFAULT false,
    p_page      integer DEFAULT 1,
    p_size      integer DEFAULT 20,
    p_codigo    text DEFAULT NULL,
    p_nombre    text DEFAULT NULL,
    p_contacto  text DEFAULT NULL,
    p_cargo     text DEFAULT NULL,
    p_direccion text DEFAULT NULL,
    p_ciudad    text DEFAULT NULL,
    p_region    text DEFAULT NULL,
    p_cp        text DEFAULT NULL,
    p_pais      text DEFAULT NULL,
    p_telefono  text DEFAULT NULL,
    p_fax       text DEFAULT NULL
) RETURNS TABLE (
    customerid   text,
    companyname  text,
    contactname  text,
    contacttitle text,
    address      text,
    city         text,
    region       text,
    postalcode   text,
    country      text,
    phone        text,
    fax          text,
    disabled     boolean,
    total        bigint
) AS $$
-- las columnas de RETURNS TABLE (customerid, city…) 
-- también existen como variables dentro de la función. 
-- Esta línea le dice a PostgreSQL que, si un nombre es ambiguo, use la columna.
#variable_conflict use_column
BEGIN
    -- 1) Obtener un cliente (solo si está habilitado)
    IF nullif(trim(p_id), '') IS NOT NULL THEN
        RETURN QUERY
            SELECT v.customerid::text, v.companyname::text, v.contactname::text,
                   v.contacttitle::text, v.address::text, v.city::text, v.region::text,
                   v.postalcode::text, v.country::text, v.phone::text, v.fax::text,
                   v.disabled, 1::bigint
            FROM vw_clientes v
            WHERE v.customerid = upper(trim(p_id)) AND NOT v.disabled;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'No existe el cliente % o está inhabilitado', upper(trim(p_id))
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
    p_codigo    := nullif(trim(p_codigo), '');
    p_nombre    := nullif(trim(p_nombre), '');
    p_contacto  := nullif(trim(p_contacto), '');
    p_cargo     := nullif(trim(p_cargo), '');
    p_direccion := nullif(trim(p_direccion), '');
    p_ciudad    := nullif(trim(p_ciudad), '');
    p_region    := nullif(trim(p_region), '');
    p_cp        := nullif(trim(p_cp), '');
    p_pais      := nullif(trim(p_pais), '');
    p_telefono  := nullif(trim(p_telefono), '');
    p_fax       := nullif(trim(p_fax), '');

    -- count(*) OVER () se calcula antes del LIMIT: es el total filtrado, no el de la página
    RETURN QUERY
        SELECT v.customerid::text, v.companyname::text, v.contactname::text,
               v.contacttitle::text, v.address::text, v.city::text, v.region::text,
               v.postalcode::text, v.country::text, v.phone::text, v.fax::text,
               v.disabled, count(*) OVER ()
        FROM vw_clientes v
        WHERE v.disabled = coalesce(p_disabled, false)
          AND (p_codigo    IS NULL OR v.customerid   ILIKE '%' || p_codigo    || '%')
          AND (p_nombre    IS NULL OR v.companyname  ILIKE '%' || p_nombre    || '%')
          AND (p_contacto  IS NULL OR v.contactname  ILIKE '%' || p_contacto  || '%')
          AND (p_cargo     IS NULL OR v.contacttitle ILIKE '%' || p_cargo     || '%')
          AND (p_direccion IS NULL OR v.address      ILIKE '%' || p_direccion || '%')
          AND (p_ciudad    IS NULL OR v.city         ILIKE '%' || p_ciudad    || '%')
          AND (p_region    IS NULL OR v.region       ILIKE '%' || p_region    || '%')
          AND (p_cp        IS NULL OR v.postalcode   ILIKE '%' || p_cp        || '%')
          AND (p_pais      IS NULL OR v.country      ILIKE '%' || p_pais      || '%')
          AND (p_telefono  IS NULL OR v.phone        ILIKE '%' || p_telefono  || '%')
          AND (p_fax       IS NULL OR v.fax          ILIKE '%' || p_fax       || '%')
        ORDER BY v.companyname, v.customerid
        LIMIT p_size OFFSET (p_page - 1) * p_size;
END;
$$ LANGUAGE plpgsql;
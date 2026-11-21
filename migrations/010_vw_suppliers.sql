-- =====================================================================
-- 003: Consultas de proveedores dentro de la base
--   * vw_suppliers         -> QUÉ datos de un proveedor ve la aplicación
--   * fn_consulta_supplier -> CÓMO se consultan (obtener uno / listar con
--                            filtros y paginado). Lee de la vista.
--   Las escrituras siguen en fn_abm_supplier (migración 010).
-- =====================================================================

-- ---------- Vista ----------
CREATE OR REPLACE VIEW vw_suppliers AS
SELECT
    s.supplierid,
    s.companyname,
    s.contactname,
    s.contacttitle,
    s.address,
    s.city,
    s.region,
    s.postalcode,
    s.country,
    s.phone,
    s.fax,
    s.homepage
FROM suppliers s;

-- ---------- Función de consulta ----------
-- Uso:
--   Obtener: SELECT * FROM fn_consulta_supplier(p_id => 1);
--   Listar:  SELECT * FROM fn_consulta_supplier(p_page => 1, p_size => 10, p_pais => 'mex');
-- Devuelve filas con las columnas de la vista + "total" (cantidad de registros
-- que cumplen los filtros, sin importar la página).
-- Filtros: NULL o texto vacío = no filtra. Se combinan con AND, sin distinguir mayúsculas.
CREATE OR REPLACE FUNCTION fn_consulta_supplier(
    p_id        integer DEFAULT NULL,
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
    p_fax       text DEFAULT NULL,
    p_homepage  text DEFAULT NULL
) RETURNS TABLE (
    supplierid   integer,
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
    homepage     text,
    total        bigint
) AS $$
-- las columnas de RETURNS TABLE (supplierid, city…) 
-- también existen como variables dentro de la función. 
-- Esta línea le dice a PostgreSQL que, si un nombre es ambiguo, use la columna.
#variable_conflict use_column
BEGIN
    -- 1) Obtener un proveedor
    IF p_id IS NOT NULL THEN
        RETURN QUERY
            SELECT v.supplierid, v.companyname::text, v.contactname::text,
                   v.contacttitle::text, v.address::text, v.city::text, v.region::text,
                   v.postalcode::text, v.country::text, v.phone::text, v.fax::text,
                   v.homepage::text, 1::bigint
            FROM vw_suppliers v
            WHERE v.supplierid = p_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'No existe el proveedor %', p_id
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
    p_homepage  := nullif(trim(p_homepage), '');

    -- count(*) OVER () se calcula antes del LIMIT: es el total filtrado, no el de la página
    RETURN QUERY
        SELECT v.supplierid, v.companyname::text, v.contactname::text,
               v.contacttitle::text, v.address::text, v.city::text, v.region::text,
               v.postalcode::text, v.country::text, v.phone::text, v.fax::text,
               v.homepage::text, count(*) OVER ()
        FROM vw_suppliers v
        WHERE (p_codigo    IS NULL OR v.supplierid::text   ILIKE '%' || p_codigo    || '%')
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
          AND (p_homepage  IS NULL OR v.homepage     ILIKE '%' || p_homepage  || '%')
        ORDER BY v.companyname, v.supplierid
        LIMIT p_size OFFSET (p_page - 1) * p_size;
END;
$$ LANGUAGE plpgsql;
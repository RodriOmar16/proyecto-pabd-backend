-- =====================================================================
-- 014: Listas de los filtros de órdenes con búsqueda (reemplaza a la 013)
--   * fn_listar_clientes(p_buscar, p_limite)
--   * fn_listar_empleados(p_buscar, p_limite)
--   * fn_listar_transportistas(p_buscar, p_limite)
--   Busca por id o nombre (contiene, sin mayúsculas). Máximo 50 resultados.
--   Se borran las versiones sin parámetros: PostgreSQL permite sobrecarga
--   y con ambas la llamada sería ambigua.
-- =====================================================================

DROP FUNCTION IF EXISTS fn_listar_clientes();
DROP FUNCTION IF EXISTS fn_listar_empleados();
DROP FUNCTION IF EXISTS fn_listar_transportistas();

CREATE OR REPLACE FUNCTION fn_listar_clientes(
    p_buscar text    DEFAULT NULL,
    p_limite integer DEFAULT 20
) RETURNS TABLE (customerid text, nombre text, disabled boolean) AS $$
#variable_conflict use_column
BEGIN
    p_buscar := nullif(trim(p_buscar), '');
    p_limite := least(greatest(coalesce(p_limite, 20), 1), 50);

    RETURN QUERY
        SELECT v.customerid::text, v.companyname::text, v.disabled
        FROM vw_clientes v
        WHERE p_buscar IS NULL
           OR v.companyname ILIKE '%' || p_buscar || '%'
           OR v.customerid  ILIKE '%' || p_buscar || '%'
        ORDER BY v.companyname
        LIMIT p_limite;
END;
$$ LANGUAGE plpgsql STABLE;
-------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_listar_empleados(
    p_buscar text    DEFAULT NULL,
    p_limite integer DEFAULT 20
) RETURNS TABLE (employeeid integer, nombre text, disabled boolean) AS $$
#variable_conflict use_column
BEGIN
    p_buscar := nullif(trim(p_buscar), '');
    p_limite := least(greatest(coalesce(p_limite, 20), 1), 50);

    RETURN QUERY
        SELECT v.employeeid::int, (v.lastname || ', ' || v.firstname)::text, v.disabled
        FROM vw_employees v
        WHERE p_buscar IS NULL
           OR (v.lastname || ', ' || v.firstname) ILIKE '%' || p_buscar || '%'
           OR v.employeeid::text = p_buscar
        ORDER BY v.lastname, v.firstname
        LIMIT p_limite;
END;
$$ LANGUAGE plpgsql STABLE;
------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_listar_transportistas(
    p_buscar text    DEFAULT NULL,
    p_limite integer DEFAULT 20
) RETURNS TABLE (shipperid integer, nombre text, disabled boolean) AS $$
#variable_conflict use_column
BEGIN
    p_buscar := nullif(trim(p_buscar), '');
    p_limite := least(greatest(coalesce(p_limite, 20), 1), 50);

    RETURN QUERY
        SELECT s.shipperid::int, s.companyname::text, false
        FROM shippers s
        WHERE p_buscar IS NULL
           OR s.companyname ILIKE '%' || p_buscar || '%'
           OR s.shipperid::text = p_buscar
        ORDER BY s.companyname
        LIMIT p_limite;
END;
$$ LANGUAGE plpgsql STABLE;
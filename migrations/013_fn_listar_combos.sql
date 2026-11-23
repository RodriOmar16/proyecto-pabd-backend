-- =====================================================================
-- 013: Listas para los seleccionables de los filtros de órdenes
--   * fn_listar_clientes       -> todos los clientes (id + nombre)
--   * fn_listar_empleados      -> todos los empleados (id + nombre)
--   * fn_listar_transportistas -> todos los shippers (id + nombre)
--   Traen también los inhabilitados: sus órdenes viejas se pueden buscar.
-- =====================================================================

CREATE OR REPLACE FUNCTION fn_listar_clientes()
RETURNS TABLE (customerid text, nombre text, disabled boolean) AS $$
    SELECT v.customerid::text, v.companyname::text, v.disabled
    FROM vw_clientes v
    ORDER BY v.companyname;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION fn_listar_empleados()
RETURNS TABLE (employeeid integer, nombre text, disabled boolean) AS $$
    SELECT v.employeeid::int, (v.lastname || ', ' || v.firstname)::text, v.disabled
    FROM vw_employees v
    ORDER BY v.lastname, v.firstname;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION fn_listar_transportistas()
RETURNS TABLE (shipperid integer, nombre text, disabled boolean) AS $$
    SELECT s.shipperid::int, s.companyname::text, false
    FROM shippers s
    ORDER BY s.companyname;
$$ LANGUAGE sql STABLE;
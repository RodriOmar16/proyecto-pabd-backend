-- ===============================================================================================
-- 012: Consulta de ordenes dentro de la base de datos
-- 	* vw_ordenes		  -> qué datos de las ordenes ve la aplicación
-- 	* fn_consulta_ordenes -> cómo se consulta, lee de la vista
--  * vw_detalles_orden    -> qué datos de cada línea de producto ve la aplicación
--  * fn_py_orden_detalles -> líneas de una orden con subtotal y total final. Lee de vw_detalles_orden
-- ===============================================================================================

----------EXTENSION----------------------
CREATE EXTENSION IF NOT EXISTS plpython3u;

---------------VISTA-----------------------
CREATE OR REPLACE VIEW vw_ordenes AS
SELECT
    o.orderid,
    o.orderdate,
    o.requireddate,
    o.shippeddate,
    o.customerid,
    c.companyname                    AS cliente,
    o.employeeid,
    e.lastname || ', ' || e.firstname AS empleado,
    o.shipvia                        AS shipperid,
    s.companyname                    AS transportista,
    o.freight,
    o.shipname,
    o.shipaddress,
    o.shipcity,
    o.shipregion,
    o.shippostalcode,
    o.shipcountry
FROM orders o
LEFT JOIN customers c ON c.customerid = o.customerid
LEFT JOIN employees e ON e.employeeid = o.employeeid
LEFT JOIN shippers  s ON s.shipperid  = o.shipvia;

------------------Funcion de consulta-------------------------------
-- Obtener: Select * from fn_consulta_ordenes(p_orderid => 102478)
-- Listar:  Select * from fn_consulta_

create or replace function fn_consulta_ordenes(
    p_orderid    integer DEFAULT NULL,
    p_desde      date    DEFAULT NULL,
    p_hasta      date    DEFAULT NULL,
    p_customerid text    DEFAULT NULL,
    p_employeeid integer DEFAULT NULL,
    p_shipperid  integer DEFAULT NULL,
    p_direccion  text    DEFAULT NULL,
    p_ciudad     text    DEFAULT NULL,
    p_pais       text    DEFAULT NULL,
    p_page       integer DEFAULT 1,
    p_size       integer DEFAULT 20
) returns table(
    orderid        integer,
    orderdate      date,
    requireddate   date,
    shippeddate    date,
    customerid     text,
    cliente        text,
    employeeid     integer,
    empleado       text,
    shipperid      integer,
    transportista  text,
    freight        numeric,
    shipname       text,
    shipaddress    text,
    shipcity       text,
    shipregion     text,
    shippostalcode text,
    shipcountry    text,
    total          bigint
) as 
$$
	COLUMNAS = """
	    v.orderid::int, v.orderdate::date, v.requireddate::date, v.shippeddate::date,
	    v.customerid::text, v.cliente::text, v.employeeid::int, v.empleado::text,
	    v.shipperid::int, v.transportista::text, v.freight::numeric,
	    v.shipname::text, v.shipaddress::text, v.shipcity::text, v.shipregion::text,
	    v.shippostalcode::text, v.shipcountry::text
	"""
	
	def limpio(texto):
	    """Texto vacío o con espacios -> None (no filtra)."""
	    return (texto or "").strip() or None
	
	# 1) Obtener una orden
	if p_orderid is not None:
	    plan = plpy.prepare(
	        f"SELECT {COLUMNAS}, 1::bigint AS total FROM vw_ordenes v WHERE v.orderid = $1",
	        ["int4"],
	    )
	    filas = plpy.execute(plan, [p_orderid])
	    if len(filas) == 0:
	        plpy.error(f"No existe la orden {p_orderid}", sqlstate="P0002")
	    return list(filas)
	    
	# 2) Listar: validar paginación
	if p_page is None or p_page < 1:
	    plpy.error("La página debe ser mayor o igual a 1")
	if p_size is None or p_size < 1:
	    plpy.error("El tamaño de página debe ser mayor o igual a 1")
	tamanio = min(p_size, 100)
	
	cliente = limpio(p_customerid)
	cliente = cliente.upper() if cliente else None
	
	plan = plpy.prepare(
    f"""
	    SELECT {COLUMNAS}, count(*) OVER () AS total
	    FROM vw_ordenes v
	    WHERE ($1 IS NULL OR v.orderdate::date >= $1)
	      AND ($2 IS NULL OR v.orderdate::date <= $2)
	      AND ($3 IS NULL OR v.customerid = $3)
	      AND ($4 IS NULL OR v.employeeid = $4)
	      AND ($5 IS NULL OR v.shipperid  = $5)
	      AND ($6 IS NULL OR v.shipaddress ILIKE '%' || $6 || '%')
	      AND ($7 IS NULL OR v.shipcity    ILIKE '%' || $7 || '%')
	      AND ($8 IS NULL OR v.shipcountry ILIKE '%' || $8 || '%')
	    ORDER BY v.orderdate DESC, v.orderid DESC
	    LIMIT $9 OFFSET ($10 - 1) * $9
	    """,
	    ["date", "date", "text", "int4", "int4", "text", "text", "text", "int4", "int4"],
	)
	return list(plpy.execute(plan, [
	    p_desde, p_hasta, cliente, p_employeeid, p_shipperid,
	    limpio(p_direccion), limpio(p_ciudad), limpio(p_pais),
	    tamanio, p_page,
	]))

$$
language plpython3u;


--------------VISTA DEL DETALLE----------------
CREATE OR REPLACE VIEW vw_detalles_orden as
select
	o.orderid,
	od.productid,
	p.productname as producto,
	od.quantity,
	od.unitprice,
	od.discount,
	o.freight,
	ROUND(od.quantity * od.unitprice * (1 - od.discount), 2)::numeric(10,2) as subtotal
FROM orders o
inner join orderdetails od using(orderid)
inner join products p using(productid);

-----------------fn_consulta_detalles------------------
create or replace function fn_py_orden_detalles(p_orderid int)
returns table (
	orderid int, productid int, producto varchar, quantity int, unitprice numeric, discount numeric, subtotal numeric, total_final numeric
) as 
$$
	plan_detalles = plpy.prepare(
		"""
			select
				v.*,
				sum(v.subtotal) over () + coalesce(v.freight, 0) as total_final
			FROM vw_detalles_orden v
			where v.orderid = $1 
			order by v.producto
		""",
		["int4"]
	)	
	rows = plpy.execute(plan_detalles, [p_orderid])
	for r in rows:
		yield(r["orderid"], r["productid"], r["producto"], r["quantity"], r["unitprice"], r["discount"], r["subtotal"], r["total_final"])
$$
language plpython3u;

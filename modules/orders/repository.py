import psycopg
from db import get_connection

# Filtros de texto que acepta el listado (los numéricos los valida el handler)
FILTROS_TEXTO = ["desde", "hasta", "customerid", "shipaddress", "shipcity", "shipcountry"]

# Columnas por las que se puede buscar (el front muesta un campo de búsqueda por cada uno)
COLUMNAS_BUSCABLES = [
    "orderid", "orderdate", "customerid", "employeeid", "shipperid", "shipaddress", "shipname", "shipcity"
    "shipcountry", "shipregion", "shippostalcode"
]

# Toda la lectura la resuelve la base, mirar la migracion 012

SQL_LISTAR = """
    SELECT * FROM fn_consulta_ordenes(
        p_desde      => %(desde)s::date,
        p_hasta      => %(hasta)s::date,
        p_customerid => %(customerid)s::text,
        p_employeeid => %(employeeid)s::integer,
        p_shipperid  => %(shipperid)s::integer,
        p_direccion  => %(shipaddress)s::text,
        p_ciudad     => %(shipcity)s::text,
        p_pais       => %(shipcountry)s::text,
        p_page       => %(page)s::integer,
        p_size       => %(size)s::integer
    )
"""
SQL_OBTENER = "select * from fn_consulta_ordenes(p_orderid => %s::integer)"
SQL_DETALLE = "SELECT * FROM fn_py_orden_detalles(p_orderid => %s::integer)"

def _sin_total(fila: dict) -> dict:
    """La columna total es de la paginación, no del orden."""
    fila.pop("total", None)
    return fila

def listar(page: int, size: int, filtros: dict, disabled: bool = False):
    """Devuelve (filas de la página pedida, total) """
    # Con número de orden, la función devuelve esa sola (o NoDataFound si no existe)
    if filtros.get("orderid") is not None:
        try:
            return [obtener(filtros["orderid"])], 1
        except psycopg.errors.NoDataFound:
            return [], 0

    params = {**filtros, "page": page, "size": size}
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_LISTAR, params)
        filas = cur.fetchall()
    total = filas[0]["total"] if filas else 0
    return [_sin_total(f) for f in filas], total


def obtener(orderid: int):
    """Devuelve el encabezado de la orden. Si no existe, la base lanza NoDataFound."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_OBTENER, (orderid,))
        return _sin_total(cur.fetchone())


def detalle(orderid: int):
    """Devuelve {orderid, lineas, total_final}. Sin líneas: lista vacía y total_final None."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_DETALLE, (orderid,))
        lineas = cur.fetchall()
    total_final = lineas[0]["total_final"] if lineas else None
    for linea in lineas:
        linea.pop("total_final", None)  # viaja repetido en cada fila: se devuelve una sola vez
    return {"orderid": orderid, "lineas": lineas, "total_final": total_final}
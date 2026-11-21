from db import get_connection

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = [
    "supplierid", 
    "companyname", 
    "contactname", 
    "contacttitle", 
    "address",
    "city", 
    "region", 
    "postalcode", 
    "country", 
    "phone", 
    "fax", 
    "homepage"
]

# Toda la lectura la resuelve la base (migrations/010_vw_suppliers.sql).
# Los filtros que no vienen van como NULL: la función los ignora.
SQL_LISTAR = """
  SELECT * FROM fn_consulta_supplier(
    p_page      => %(page)s::integer,
    p_size      => %(size)s::integer,
    p_codigo    => %(supplierid)s::text,
    p_nombre    => %(companyname)s::text,
    p_contacto  => %(contactname)s::text,
    p_cargo     => %(contacttitle)s::text,
    p_direccion => %(address)s::text,
    p_ciudad    => %(city)s::text,
    p_region    => %(region)s::text,
    p_cp        => %(postalcode)s::text,
    p_pais      => %(country)s::text,
    p_telefono  => %(phone)s::text,
    p_fax       => %(fax)s::text,
    p_homepage  => %(homepage)s::text
  )
"""

SQL_OBTENER = "SELECT * FROM fn_consulta_supplier(p_id => %s::integer)"

SQL_ABM = """SELECT fn_abm_supplier(
                   p_accion   => %s::text, p_id => %s::int,
                   p_nombre   => %s::text, p_contacto => %s::text,
                   p_ciudad   => %s::text, p_pais => %s::text,
                   p_cargo    => %s::text, p_direccion => %s::text,
                   p_region   => %s::text, p_cp => %s::text,
                   p_telefono => %s::text, p_fax => %s::text, p_homepage => %s::text
               ) AS mensaje"""

def _sin_total(fila: dict) -> dict:
    """La columna total es de la paginación, no del cliente."""
    fila.pop("total", None)
    return fila

def listar(page: int, size: int, filtros: dict):
    """
    Devuelve (filas de la página pedida, total) usando la funcion definida en SQL_LISTAR"""

    # Construimos el diccionario de parámetros que la función espera.
    params = {col: filtros.get(col) for col in COLUMNAS_BUSCABLES}
    params.update(page=page, size=size)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_LISTAR, params)
        filas = cur.fetchall()
    # La función siempre devuelve la columna `total` en cada fila.
    total = filas[0]["total"] if filas else 0
    return [_sin_total(f) for f in filas], total


def obtener(supplierid: int):
    """Devuelve el proveedor usando la funcion definida en SQL_OBTENER."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_OBTENER, (supplierid,))
        fila = cur.fetchone()
        return _sin_total(fila) if fila else None


def _abm(accion: str, supplierid: int, datos: dict | None = None) -> str:
    """Llama a la función de la base fn_abm_supplier y devuelve su mensaje.
    Las validaciones las hace la función: si rechaza la operación, psycopg lanza
    la excepción con el mensaje escrito en la base."""
    datos = datos or {}
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            SQL_ABM,
            [
                accion, 
                supplierid,
                datos.get("companyname"), 
                datos.get("contactname"),
                datos.get("city"), 
                datos.get("country"),
                datos.get("contacttitle"), 
                datos.get("address"),
                datos.get("region"), 
                datos.get("postalcode"),
                datos.get("phone"), 
                datos.get("fax"), 
                datos.get("homepage"),
            ],
        )
        return cur.fetchone()["mensaje"]


def crear(datos: dict):
    """Alta: fn_abm_supplier('A', ...). Devuelve el supplier tal como quedó en la base."""
    mensaje=_abm("A", None, datos)

    try:
        supplier_id = int(mensaje.split()[1])
    except (ValueError, IndexError):
        return None
    
    return obtener(supplier_id)


def actualizar(supplierid: int, datos: dict):
    """Modificación: fn_abm_supplier('M', ...). Devuelve el supplier actualizado."""
    _abm("M", supplierid, datos)
    return obtener(supplierid)


def eliminar(supplierid: int):
    """Baja física: fn_abm_supplier('B', ...) elimina de la BD.
    Devuelve {supplierid, companyname}."""
    actual=obtener(supplierid)
    _abm("B", supplierid)
    return {
        "supplierid": supplierid,
        "companyname": actual["companyname"] if actual else None,
    }
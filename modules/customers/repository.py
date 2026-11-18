from db import get_connection

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = ["customerid", "companyname", "contactname", "contacttitle", "address",
                      "city", "region", "postalcode", "country", "phone", "fax"]

# Toda la lectura la resuelve la base (migrations/003_vw_clientes.sql).
# Los filtros que no vienen van como NULL: la función los ignora.
SQL_LISTAR = """
  SELECT * FROM fn_consulta_cliente(
    p_disabled  => %(disabled)s::boolean,
    p_page      => %(page)s::integer,
    p_size      => %(size)s::integer,
    p_codigo    => %(customerid)s::text,
    p_nombre    => %(companyname)s::text,
    p_contacto  => %(contactname)s::text,
    p_cargo     => %(contacttitle)s::text,
    p_direccion => %(address)s::text,
    p_ciudad    => %(city)s::text,
    p_region    => %(region)s::text,
    p_cp        => %(postalcode)s::text,
    p_pais      => %(country)s::text,
    p_telefono  => %(phone)s::text,
    p_fax       => %(fax)s::text
  )
"""

SQL_OBTENER = "SELECT * FROM fn_consulta_cliente(p_id => %s::text)"


def _sin_total(fila: dict) -> dict:
    """La columna total es de la paginación, no del cliente."""
    fila.pop("total", None)
    return fila


def listar(page: int, size: int, filtros: dict, disabled: bool = False):
    """Devuelve (filas de la página pedida, total) usando fn_consulta_cliente."""
    params = {columna: filtros.get(columna) for columna in COLUMNAS_BUSCABLES}
    params.update(page=page, size=size, disabled=disabled)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_LISTAR, params)
        filas = cur.fetchall()
    total = filas[0]["total"] if filas else 0
    return [_sin_total(f) for f in filas], total


def obtener(customerid: str):
    """Devuelve el cliente. Si no existe o está inhabilitado, la base lanza NoDataFound."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_OBTENER, (customerid,))
        return _sin_total(cur.fetchone())


def _abm(accion: str, customerid: str, datos: dict | None = None) -> str:
    """Llama a la función de la base fn_abm_cliente y devuelve su mensaje.
    Las validaciones las hace la función: si rechaza la operación, psycopg lanza
    la excepción con el mensaje escrito en la base."""
    datos = datos or {}
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT fn_abm_cliente(
                   p_accion   => %s::text, p_id => %s::text,
                   p_nombre   => %s::text, p_contacto => %s::text,
                   p_ciudad   => %s::text, p_pais => %s::text,
                   p_cargo    => %s::text, p_direccion => %s::text,
                   p_region   => %s::text, p_cp => %s::text,
                   p_telefono => %s::text, p_fax => %s::text
               ) AS mensaje""",
            [
                accion, customerid,
                datos.get("companyname"), datos.get("contactname"),
                datos.get("city"), datos.get("country"),
                datos.get("contacttitle"), datos.get("address"),
                datos.get("region"), datos.get("postalcode"),
                datos.get("phone"), datos.get("fax"),
            ],
        )
        return cur.fetchone()["mensaje"]


def crear(customerid: str, datos: dict):
    """Alta: fn_abm_cliente('A', ...). Devuelve el cliente tal como quedó en la base."""
    _abm("A", customerid, datos)
    return obtener(customerid)


def actualizar(customerid: str, datos: dict):
    """Modificación: fn_abm_cliente('M', ...). Devuelve el cliente actualizado."""
    _abm("M", customerid, datos)
    return obtener(customerid)


def cambiar_estado(customerid: str):
    """Baja lógica: fn_abm_cliente('B', ...) invierte el estado.
    Devuelve {customerid, mensaje} con el mensaje de la base."""
    mensaje = _abm("B", customerid)
    return {"customerid": customerid.strip().upper(), "mensaje": mensaje}
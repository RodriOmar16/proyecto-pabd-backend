from db import get_connection

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = ["supplierid", "companyname", "contactname", "contacttitle", "address",
                      "city", "region", "postalcode", "country", "phone", "fax", "homepage"]


def listar(page: int, size: int, filtros: dict):
    """Devuelve (filas de la página pedida, total).
    filtros: {columna: texto a buscar};"""
    condiciones = []
    params = {}
    for columna in COLUMNAS_BUSCABLES:
        valor = filtros.get(columna)
        if valor:
            # El nombre de la columna sale de la lista fija de arriba (seguro);
            # el texto buscado va siempre como parámetro
            condiciones.append(f"{columna}::text ILIKE %({columna})s")
            params[columna] = f"%{valor}%"
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS total FROM suppliers {where}", params)
        total = cur.fetchone()["total"]  # se calcula para la paginación

        cur.execute(
            f"""SELECT * FROM suppliers {where}
                ORDER BY companyname
                LIMIT %(limite)s OFFSET %(desde)s""",
            {**params, "limite": size, "desde": (page - 1) * size},
        )
        return cur.fetchall(), total


def obtener(supplierid: int):
    """Devuelve el cliente."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM suppliers WHERE supplierid = %s", (supplierid,))
        return cur.fetchone()


def _abm(accion: str, supplierid: int, datos: dict | None = None) -> str:
    """Llama a la función de la base fn_abm_supplier y devuelve su mensaje.
    Las validaciones las hace la función: si rechaza la operación, psycopg lanza
    la excepción con el mensaje escrito en la base."""
    datos = datos or {}
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT fn_abm_supplier(
                   p_accion   => %s::text, p_id => %s::int,
                   p_nombre   => %s::text, p_contacto => %s::text,
                   p_ciudad   => %s::text, p_pais => %s::text,
                   p_cargo    => %s::text, p_direccion => %s::text,
                   p_region   => %s::text, p_cp => %s::text,
                   p_telefono => %s::text, p_fax => %s::text, p_homepage => %s::text
               ) AS mensaje""",
            [
                accion, supplierid,
                datos.get("companyname"), datos.get("contactname"),
                datos.get("city"), datos.get("country"),
                datos.get("contacttitle"), datos.get("address"),
                datos.get("region"), datos.get("postalcode"),
                datos.get("phone"), datos.get("fax"), datos.get("homepage"),
            ],
        )
        return cur.fetchone()["mensaje"]


def crear(datos: dict):
    """Alta: fn_abm_supplier('A', ...). Devuelve el supplier tal como quedó en la base."""
    mensaje=_abm("A", None, datos)
    return obtener(int(mensaje.split()[1]))


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
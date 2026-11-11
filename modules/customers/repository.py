from db import get_connection

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = ["customerid", "companyname", "contactname", "contacttitle", "address",
                      "city", "region", "postalcode", "country", "phone", "fax"]


def listar(page: int, size: int, filtros: dict, disabled: bool = False):
    """Devuelve (filas de la página pedida, total).
    filtros: {columna: texto a buscar}; disabled=False lista habilitados, True inhabilitados."""
    condiciones = ["disabled = %(disabled)s"]
    params = {"disabled": disabled}
    for columna in COLUMNAS_BUSCABLES:
        valor = filtros.get(columna)
        if valor:
            # El nombre de la columna sale de la lista fija de arriba (seguro);
            # el texto buscado va siempre como parámetro
            condiciones.append(f"{columna} ILIKE %({columna})s")
            params[columna] = f"%{valor}%"
    where = "WHERE " + " AND ".join(condiciones)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS total FROM customers {where}", params)
        total = cur.fetchone()["total"]  # se calcula para la paginación

        cur.execute(
            f"""SELECT * FROM customers {where}
                ORDER BY companyname
                LIMIT %(limite)s OFFSET %(desde)s""",
            {**params, "limite": size, "desde": (page - 1) * size},
        )
        return cur.fetchall(), total


def obtener(customerid: str):
    """Devuelve el cliente habilitado o None si no existe (o está inhabilitado)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE customerid = %s AND NOT disabled", (customerid,))
        return cur.fetchone()


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
    return obtener(customerid.strip().upper())


def actualizar(customerid: str, datos: dict):
    """Modificación: fn_abm_cliente('M', ...). Devuelve el cliente actualizado."""
    _abm("M", customerid, datos)
    return obtener(customerid)


def cambiar_estado(customerid: str):
    """Baja lógica: fn_abm_cliente('B', ...) invierte el estado.
    Devuelve {customerid, companyname, disabled}."""
    _abm("B", customerid)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT customerid, companyname, disabled FROM customers WHERE customerid = %s",
            (customerid,),
        )
        return cur.fetchone()
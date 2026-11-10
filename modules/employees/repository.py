from db import get_connection

# Columnas que se cargan/editan desde la API
# ordersquantity y ordersamount no se tocan: las mantiene la base de datos
COLUMNAS = [
    "lastname",
    "firstname",
    "title",
    "titleofcourtesy",
    "birthdate",
    "hiredate",
    "address",
    "city",
    "region",
    "postalcode",
    "country",
    "homephone",
    "extension",
    "notes",
    "reportsto",
    "salary",
    "comission_pct",
]

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = [
    "employeeid",
    "lastname",
    "firstname",
    "title",
    "birthdate",
    "hiredate",
    "city",
    "region",
    "postalcode",
    "country",
]


def listar(page: int, size: int, filtros: dict, disabled: bool = False):
    """Devuelve (filas de la página pedida, total).
    filtros: {columna: texto a buscar}; disabled=False lista habilitados,
    True inhabilitados."""
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
        cur.execute(f"SELECT count(*) AS total FROM employees {where}", params)
        total = cur.fetchone()["total"]  # se calcula para la paginación

        cur.execute(
            f"""SELECT * FROM employees {where}
                ORDER BY employees
                LIMIT %(limite)s OFFSET %(desde)s""",
            {**params, "limite": size, "desde": (page - 1) * size},
        )
        return cur.fetchall(), total


def obtener(employeeid: str):
    """Devuelve el empleado habilitado o None si no existe (o esta deshabilitado)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM employees WHERE employeeid = %s AND NOT disabled",
            (employeeid,),
        )
        return cur.fetchone()


def crear(employeeid: str, datos: dict):
    """Inserta un empleado y lo devuelve tal como quedó en la base."""
    valores = [employeeid] + [datos.get(c) for c in COLUMNAS]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ INSERT INTO employees(employeeid, lastname, firstname, title, titleofcourtesy, birthdate, hiredate, address, 
                                    city, region, postalcode, country, homephone, extension, notes, reportsto, salary, comission_pct) 
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *""",
            valores,
        )
        return cur.fetchone()


def actualizar(employeeid: str, datos: dict):
    """Reemplaza los datos del cliente. Devuelve el cliente actualizado o None si no existe."""
    valores = [datos.get(c) for c in COLUMNAS] + [employeeid]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ UPDATE employees
                SET lastname        = %s,
                    firstname       = %s,
                    title           = %s,
                    titleofcourtesy = %s,
                    birthdate       = %s,
                    hiredate        = %s,
                    address         = %s,
                    city            = %s,
                    region          = %s,
                    postalcode      = %s,
                    country         = %s,
                    homephone       = %s,
                    extension       = %s,
                    notes           = %s,
                    reportsto       = %s,
                    salary          = %s,
                    comission_pct   = %s
                WHERE employeeid = %s AND NOT disabled
                RETURNING *""",
            valores,
        )
        return cur.fetchone()


def eliminar(employeeid: str) -> bool:
    """Borra el cliente. Devuelve True si existía."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM employees WHERE employeeid = %s", (employeeid,))
        return cur.rowcount > 0


def cambiar_estado(employeeid: str):
    """Habilita o inhabilita el empleado invirtiendo 'disabled'.
    Devuelve { employeeid, lastname, firstname, disabled } o None si no existe."""

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ UPDATE employees
                SET disabled = NOT disabled
                WHERE employeeid = %s
                RETURNING employeeid, lastname, firstname, disabled """,
            (employeeid,),
        )
        return cur.fetchone()

from db import get_connection

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = [
    "employeeid",
    "lastname",
    "firstname",
    "title",
    "titleofcourtesy",
    "birthdate",
    "hiredate",
    "city",
    "region",
    "postalcode",
    "country",
    "reportsto",
    "comission_pct",
]

# Toda la lectura la resuelve la base (migrations/003_vw_empleados.sql).
# Los filtros que no vienen van como NULL: la función los ignora.
SQL_LISTAR = """
    SELECT * FROM fn_consulta_empleado(
        p_disabled        => %(disabled)s::boolean,
        p_page            => %(page)s::integer,
        p_size            => %(size)s::integer,
        p_id              => %(employeeid)s::integer,
        p_lastname        => %(lastname)s::text,
        p_firstname       => %(firstname)s::text,
        p_title           => %(title)s::text,
        p_titleofcourtesy => %(titleofcourtesy)s::text,
        p_birthdate       => %(birthdate)s::date,
        p_hiredate        => %(hiredate)s::date,
        p_city            => %(city)s::text,
        p_region          => %(region)s::text,
        p_cp              => %(postalcode)s::text,
        p_country         => %(country)s::text,
        p_reportsto       => %(reportsto)s::integer,
        p_comission_pct   => %(comission_pct)s::numeric
    )
"""

SQL_OBTENER = "SELECT * FROM fn_consulta_empleado(p_id => %s::integer)"

SQL_ABM = """
    SELECT fn_abm_employee(
        p_accion          => %s::text,
        p_id              => %s::integer,
        p_lastname        => %s::text,
        p_firstname       => %s::text,
        p_title           => %s::text,
        p_titleofcourtesy => %s::text,
        p_birthdate       => %s::date,
        p_hiredate        => %s::date,
        p_address         => %s::text,
        p_city            => %s::text,
        p_region          => %s::text,
        p_cp              => %s::text,
        p_country         => %s::text,
        p_homephone       => %s::text,
        p_extension       => %s::text,
        p_notes           => %s::text,
        p_reportsto       => %s::integer,
        p_salary          => %s::numeric,
        p_comission_pct   => %s::numeric
    ) AS mensaje
"""

def _normalizar_datos(datos: dict | None) -> dict:
    if not datos:
        return {}

    return {
        campo: None if valor == "" else valor
        for campo, valor in datos.items()
    }

def _sin_total(fila: dict) -> dict:
    """La columna total es de la paginación, no del empleado."""
    fila.pop("total", None)
    return fila

def listar(page: int, size: int, filtros: dict, disabled: bool = False):
    """Devuelve (filas de la página pedida, total) usando fn_consulta_empleado."""
    params = {columna: filtros.get(columna) for columna in COLUMNAS_BUSCABLES}
    params.update(page=page, size=size, disabled=disabled)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_LISTAR, params)
        filas = cur.fetchall()
    total = filas[0]["total"] if filas else 0
    return [_sin_total(f) for f in filas], total

def obtener(employeeid: str):
    """Devuelve el empleado. Si no existe o está inhabilitado, la base lanza NoDataFound."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL_OBTENER, (employeeid,))
        return _sin_total(cur.fetchone())

def _abm(accion: str, employeeid: str, datos: dict | None = None) -> str:
    """Llama a la función de la base fn_abm_employee y devuelve su mensaje.
    Las validaciones las hace la función: si rechaza la operación, psycopg lanza
    la excepción con el mensaje escrito en la base."""
    datos = _normalizar_datos(datos)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            SQL_ABM,
            [
                accion, employeeid,
                datos.get("lastname"), datos.get("firstname"),
                datos.get("title"), datos.get("titleofcourtesy"),
                datos.get("birthdate"), datos.get("hiredate"),
                datos.get("address"), datos.get("city"),
                datos.get("region"), datos.get("postalcode"),
                datos.get("country"), datos.get("homephone"),
                datos.get("extension"), datos.get("notes"),
                datos.get("reportsto"), datos.get("salary"),
                datos.get("comission_pct")
            ],
        )
        return cur.fetchone()["mensaje"]

def crear(employeeid: str, datos: dict):
    """Alta: fn_abm_employee('A', ...). Devuelve el empleado tal como quedó en la base."""
    _abm("A", employeeid, datos)
    return obtener(employeeid)

def actualizar(employeeid: str, datos: dict):
    """Modificación: fn_abm_employee('M', ...). Devuelve el empleado actualizado."""
    _abm("M", employeeid, datos)
    return obtener(employeeid)


def cambiar_estado(employeeid: str):
    """Baja lógica: fn_abm_empleado('B', ...) invierte el estado.
    Devuelve {employeeid, mensaje} con el mensaje de la base."""
    mensaje = _abm("B", employeeid)
    return {"employeeid": employeeid, "mensaje": mensaje}
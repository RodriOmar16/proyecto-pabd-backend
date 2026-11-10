from db import get_connection

# Columnas que se cargan/editan desde la API
# ordersquantity y ordersamount no se tocan: las mantiene la base de datos
COLUMNAS = ["companyname", "contactname", "contacttitle", "address", "city",
            "region", "postalcode", "country", "phone", "fax"]

# Columnas por las que se puede buscar (el front muestra un campo de búsqueda por cada una)
COLUMNAS_BUSCABLES = ["customerid", "companyname", "contactname", "contacttitle", "address",
                      "city", "region", "postalcode", "country", "phone", "fax"]

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
    """ Devuelve el cliente habilitado o None si no existe (o esta deshabilitado). """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE customerid = %s AND NOT disabled", (customerid,))
        return cur.fetchone()

def crear(customerid: str, datos: dict):
    """ Inserta un cliente y lo devuelve tal como quedó en la base. """ 
    valores = [customerid] + [datos.get(c) for c in COLUMNAS]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ INSERT INTO customers(customerid, companyname, contactname, contacttitle,
                                    address, city, region, postalcode, country, phone, fax) 
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *""",
            valores
        )
        return cur.fetchone()

def actualizar(customerid: str, datos: dict):
    """ Reemplaza los datos del cliente. Devuelve el cliente actualizado o None si no existe. """
    valores = [datos.get(c) for c in COLUMNAS] + [customerid]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ UPDATE customers
                SET companyname  = %s,
                    contactname  = %s,
                    contacttitle = %s,
                    address      = %s,
                    city         = %s,
                    region       = %s,
                    postalcode   = %s,
                    country      = %s,
                    phone        = %s,
                    fax          = %s
                WHERE customerid = %s AND NOT disabled
                RETURNING *""",
            valores
        )
        return cur.fetchone()

def eliminar(customerid: str) -> bool:
    """ Borra el cliente. Devuelve True si existía. """
    with get_connection() as conn, conn.cursor() as  cur:
        cur.execute("DELETE FROM customers WHERE customerid = %s", (customerid,))
        return cur.rowcount > 0

def cambiar_estado(customerid: str):
    """ Habilita o inhabilita el cliente invirtiendo 'disabled'. 
        Devuelve { customerid, companyname, disabled } o None si no existe. """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """ UPDATE customers
                SET disabled = NOT disabled
                WHERE customerid = %s
                RETURNING customerid, companyname, disabled """,
                (customerid,),
        )
        return cur.fetchone()
from db import get_connection

# Columnas que se cargan/editan desde la API
# ordersquantity y ordersamount no se tocan: las mantiene la base de datos
COLUMNAS = [ "companyname", "contactname", "contacttitle", "address", "city", 
            "region", "postalcode", "country", "phone", "fax" ]

def listar(page: int, size: int, q: str=""):
    """ Devuelve (filas de la página pedida, total de registros que cumplen la búsqueda). """
    # El filtro es texto fijo del código; el valor buscado va siempre como parámetro %(q)s
    filtro = ""
    params_filtro = {}
    if q:
        filtro = """WHERE companyname ILIKE %(q)s OR contactname ILIKE %(q)s
                   OR city ILIKE %(q)s OR country ILIKE %(q)s
                  """
        params_filtro = {"q": f"%{q}%"}

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as Total from customers c {filtro}", params_filtro or None)
        total = cur.fetchone()["total"] #se calcula para la paginación

        cur.execute(
            f"""SELECT * FROM customers {filtro}
                ORDER BY companyname
                LIMIT %(limite)s OFFSET %(desde)s""",
            {**params_filtro, "limite": size, "desde": (page - 1) * size},
        )
        return cur.fetchall(), total

def obtener(customerid: str):
    """ Devuelve el cliente o None si no existe. """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE customerid = %s", (customerid,))
        return cur.fetchone()

def crear(customerid: str, datos: dict):
    """ Inserta un cliente y lo devuelve tal como quedó en la base. """ 
    valores = [customerid] + [datos.get(c) for c in COLUMNAS]
    with get_connection as conn, conn.cursor() as cur:
        cur.execute(
            """ INSERT INTO customers(customerid, companyname, contactname, contacttitle,
                                    address, city, region, postalcode, country, phone, fax) 
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,)
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
                WHERE customerid = %s
                RETURNING *""",
            valores
        )
        return cur.fetchone()

def eliminar(customerid: str) -> bool:
    """ Borra el cliente. Devuelve True si existía. """
    with get_connection() as conn, conn.cursor() as  cur:
        cur.execute("DELETE FROM customers WHERE customerid = %s", (customerid,))
        return cur.rowcount > 0
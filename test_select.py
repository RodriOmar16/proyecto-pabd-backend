from db import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT customerid, companyname, city, country "
            "FROM customers ORDER BY companyname LIMIT %s",
            (5,),
        )
        for fila in cur.fetchall():
            print(fila)

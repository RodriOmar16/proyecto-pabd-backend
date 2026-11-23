import psycopg

from core.http import HttpError, Request, Response
from modules.orders import repository

# Errores que lanza fn_consulta_ordenes (migracion 012 vw_ordenes)
ERRORES_DE_LA_BASE = (
    psycopg.errors.RaiseException, 
    psycopg.errors.NoDataFound, #P0002: no existe la orden
    psycopg.errors.DataError,  
)

def _error_http(e: psycopg.Error) -> HttpError:
    """ Convierte el error de la función de la base en la respuesta HTTP, con el mismo mensaje. """
    mensaje = e.diag.message_primary or "La base de datos rechazó la operación"
    if isinstance(e, psycopg.errors.NoDataFound):
        return HttpError(404, mensaje)
    return HttpError(400, mensaje)

def _id_orden(req: Request) -> int:
    """ El id de la URL es texto: lo convierto a nro o responde 400 """
    try:
        return int(req.params["id"])
    except ValueError:
        raise HttpError(400, "El nro de orden debe ser un entero")
    
def listar(req: Request) -> Response:
    page = req.query_int("page", 1)
    size = req.query_int("size", 20, maximo=100)
    # Toma de la URL solo las columnas buscables que vengan con texto
    filtros = {
        "orderid": req.query_int("orderid", None),
        "employeeid": req.query_int("employeeid", None),
        "shipperid": req.query_int("shipperid", None),
    }
    for nombre in repository.FILTROS_TEXTO:
        filtros[nombre] = req.query.get(nombre, "").strip() or None
    try:
        filas, total = repository.listar(page, size, filtros)
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(200, { "data": filas, "page": page, "size": size, "total": total })

def obtener(req: Request) -> Response:
    orderid = _id_orden(req)
    try:
        orden = repository.obtener(orderid)
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(200, orden)


def detalle(req: Request) -> Response:
    orderid = _id_orden(req)
    try:
        resultado = repository.detalle(orderid)
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(200, resultado)


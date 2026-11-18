import psycopg

from core.http import HttpError, Request, Response
from modules.suppliers import repository

# Errores que lanza fn_abm_cliente (ver migrations/002_fn_abm_cliente.sql)
ERRORES_DE_LA_BASE = (
    psycopg.errors.RaiseException,   # P0001: validación (RAISE EXCEPTION)       -> 400
    psycopg.errors.NoDataFound,      # P0002: no existe o está inhabilitado       -> 404
    psycopg.errors.UniqueViolation,  # 23505: código repetido                     -> 409
)


def _error_http(e: psycopg.Error) -> HttpError:
    """Convierte el error de la función de la base en la respuesta HTTP, con el mismo mensaje."""
    mensaje = e.diag.message_primary or "La base de datos rechazó la operación"
    if isinstance(e, psycopg.errors.NoDataFound):
        return HttpError(404, mensaje)
    if isinstance(e, psycopg.errors.UniqueViolation):
        return HttpError(409, mensaje)
    return HttpError(400, mensaje)


def listar(req: Request) -> Response:
    page = req.query_int("page", 1)
    size = req.query_int("size", 20, maximo=100)
    # Toma de la URL solo las columnas buscables que vengan con texto
    filtros = {
        columna: req.query[columna].strip()
        for columna in repository.COLUMNAS_BUSCABLES
        if req.query.get(columna, "").strip()
    }
    filas, total = repository.listar(page, size, filtros)
    return Response(200, {"data": filas, "page": page, "size": size, "total": total})


def obtener(req: Request) -> Response:
    supplier = repository.obtener(int(req.params["id"]))
    if supplier is None:
        raise HttpError(404, "Supplier no encontrado")
    return Response(200, supplier)


def crear(req: Request) -> Response:
    datos = req.json()
    try:
        supplier = repository.crear(datos)
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(201, supplier)


def actualizar(req: Request) -> Response:
    try:
        supplier = repository.actualizar(int(req.params["id"]), req.json())
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(200, supplier)


def eliminar(req: Request) -> Response:
    try:
        resultado = repository.eliminar(int(req.params["id"]))
    except ERRORES_DE_LA_BASE as e:
        raise _error_http(e)
    return Response(200, resultado)
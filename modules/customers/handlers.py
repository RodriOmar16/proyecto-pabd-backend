import psycopg
from core.http import HttpError, Request, Response
from modules.customers import repository

# Largo máximo de cada campo editable (según la tabla customers de Northwind)
LIMITES = {
    "companyname": 40, "contactname": 30, "contacttitle": 30, "address": 60,
    "city": 15, "region": 15, "postalcode": 10, "country": 15, "phone": 24, "fax": 24
}

def _limpiar(datos: dict) -> dict:
    """ Valida los campos del JSON y devuelve solo los permitidos, sin espacios sobrantes. """
    limpio = {}
    for campo, maximo in LIMITES.items():
        valor = datos.get(campo)
        if valor is None or str(valor).strip() == "":
            limpio[campo] = None
            continue
        valor = str(valor).strip()
        if len(valor) > maximo:
            raise HttpError(400, f"El campo '{campo}' admite como máximo {maximo} carácteres.")
        limpio[campo] = valor

    if not limpio["companyname"]:
        raise HttpError(400, "El campo 'companyname' es obligatorio")
    
    return limpio

def listar(req: Request) -> Response:
    page     = req.query_int("page", 1)
    size     = req.query_int("size", 20, maximo=100)
    disabled = req.query_bool("disabled", False)

    #Toma de la URL solo las columnas buscables que vengan con texto
    filtros = {
        columna: req.query[columna].strip()
        for columna in repository.COLUMNAS_BUSCABLES
        if req.query.get(columna, "").strip()
    }
    filas, total = repository.listar(page, size, filtros, disabled)
    return Response(200, { "data": filas, "page": page, "size": size, "total": total })

def obtener(req: Request) -> Response:
    cliente = repository.obtener(req.params["id"])
    if cliente is None:
        raise HttpError(404, "Cliente no encontrado")
    return Response(200, cliente)

def crear(req: Request) -> Response:
    datos = req.json()
    customerid = str(datos.get("customerid") or "").strip().upper()
    if not customerid or len(customerid) > 5:
        raise HttpError(400, "El campo 'customerid' es obligatorio y admite como máximo 5 caracteres.")
    limpio = _limpiar(datos)

    try:
        cliente = repository.crear(customerid, limpio)
    except psycopg.errors.UniqueViolation:
        raise HttpError(409, f"Ya existe un cliente con el código {customerid} (puede estar inhabilitado) ")
    except psycopg.errors.RaiseException as e:
        raise HttpError(400, e.diag.message_primary or "La base de datos rechazó la operación.")
    return Response(201, cliente)

def actualizar(req: Request) -> Response:
    limpio = _limpiar(req.json())
    try:
        cliente = repository.actualizar(req.params["id"], limpio)
    except psycopg.errors.RaiseException as e:
        raise HttpError(400, e.diag.message_primary or "La base de datos rechazó la operación")
    if cliente is None:
        raise HttpError(404, "Cliente no encontrado")
    return Response(200, cliente)

def cambiar_estado(req: Request) -> Response:
    resultado = repository.cambiar_estado(req.params["id"])
    if resultado is None:
        raise HttpError(404, "Cliente no encontrado")
    return Response(200, resultado)
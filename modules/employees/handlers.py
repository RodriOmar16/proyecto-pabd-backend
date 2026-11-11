import psycopg
from core.http import HttpError, Request, Response
from modules.employees import repository
from decimal import Decimal, InvalidOperation

def _limpiar(datos: dict) -> dict:
    """ Valida los campos del JSON y devuelve solo los permitidos, sin espacios sobrantes. """
    limpio = {}

    for campo, valor in datos.items():
        if valor is None or str(valor).strip() == "":
            limpio[campo] = None
            continue
        valor = str(valor).strip()

        if campo == 'country' and len(valor) > 3:
            raise HttpError(400, f"El campo country admite como máximo 3 carácteres.")
        elif campo == 'salary' and not _es_un_num_valido(valor):
            raise HttpError(400, f"El campo salary debe de ser un numero con maximo 10 digitos y 2 decimales.")
        
        limpio[campo] = valor

    if not limpio["lastname"] or not limpio["firstname"]:
        raise HttpError(400, "Los campos 'firstname' y 'lastname' son obligatorios" )
    
    return limpio

def _es_un_num_valido(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return False

        # Máximo 10 dígitos enteros
        if abs(numero) >= Decimal("10000000000"):
            return False

        # Máximo 2 decimales
        if numero != numero.quantize(Decimal("0.01")):
            return False

        return True

    except (InvalidOperation, ValueError):
        return False 

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
    empleado = repository.obtener(req.params["id"])
    if empleado is None:
        raise HttpError(404, "Empleado no encontrado")
    return Response(200, empleado)

def crear(req: Request) -> Response:
    datos = req.json()
    employeeid = str(datos.get("employeeid") or "").strip()
    if not employeeid:
        raise HttpError(400, "El campo 'employeeid' es obligatorio.")
    limpio = _limpiar(datos)

    try:
        empleado = repository.crear(employeeid, limpio)
    except psycopg.errors.UniqueViolation:
        raise HttpError(409, f"Ya existe un empleado con el código {employeeid} (puede estar inhabilitado) ")
    except psycopg.errors.RaiseException as e:
        raise HttpError(400, e.diag.message_primary or "La base de datos rechazó la operación.")
    return Response(201, empleado)

def actualizar(req: Request) -> Response:
    limpio = _limpiar(req.json())
    try:
        empleado = repository.actualizar(req.params["id"], limpio)
    except psycopg.errors.RaiseException as e:
        raise HttpError(400, e.diag.message_primary or "La base de datos rechazó la operación")
    if empleado is None:
        raise HttpError(404, "Empleado no encontrado")
    return Response(200, empleado)

def cambiar_estado(req: Request) -> Response:
    resultado = repository.cambiar_estado(req.params["id"])
    if resultado is None:
        raise HttpError(404, "Empleado no encontrado")
    return Response(200, resultado)
import json
from datetime import date, datetime
from decimal import Decimal
from http import HTTPStatus
from urllib.parse import parse_qs

#Encabezados CORS: permiten que el front (en otro puerto) consuma la API
CORS_HEADERS = {
  ("Access-Control-Allow-Origin", "*"),
  ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
  ("Access-Control-Allow-Headers", "Content-Type"),
}

class HttpError(Exception):
  """ Error que se convierte en respuesta HTTP con el formato { "error": mensaje }. """
  def __init__(self, status: int, mensaje: str):
    super().__init__(mensaje)
    self.status = status
    self.mensaje = mensaje

class Request:
  """ Envuelve el 'environ' de WSGI con lo que necesitan los handlers. """

  def __init__(self, environ: dict):
    self.method = environ["REQUEST_METHOD"]
    self.path = environ["PATH_INFO", "/"]
    # valores que se pegan a la url del nav. Ejemplo: ?page=2&q=berlin -> { "page": "2", "q":| "berlin" } 
    self.query = { k: v[0] for k, v in parse_qs(environ.get("QUERY_STRING", "")).items() }
    self.params = {} #parámetros de la ruta, ej: { "id": "ALFKI" }; los completa el router
    self.environ = environ

  def json(self) -> dict:
    """ Lee el cuerpo de la petición (POST/PUT) y lo devuelve como diccionario."""
    try:
      largo = int(self._environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
      largo = 0
    if largo == 0:
      raise HttpError(400, "El campo de la petición está vacío")
    cuerpo = self.environ["wsgi.input"].read(largo)
    try:
      datos = json.loads(cuerpo)
    except json.JSONDecodeError:
      raise HttpError(400, "El cuerpo de la petición no es un JSON válido")
    if not isinstance(datos, dict):
      raise HttpError(400, "El cuerpo de la petición debe ser un objeto JSON")
    return datos

  def query_int(self,nombre: str, defecto: int, minimo: int = 1, maximo: int | None = None) -> int:
    """ Lee un parámetro numérico de la URL (ej. page, size) y lo valida """
    valor = self.query.get(nombre, "")
    if valor == "":
      return defecto
    try:
      numero = int(valor)
    except ValueError:
      raise HttpError(400, f"El parámetro '{nombre}' debe ser un número entero")
    if numero < minimo:
      raise HttpError(400, f"El parámetro '{nombre}' debe ser mayor o igual a {minimo}")
    if maximo is not None and numero > maximo:
      numero = maximo
    return numero

class Response:
  """ Lo que devuelve cada handler: un código de estado y los datos a enviar como JSON """

  def __init__(self, status: int = 200, data=None):
    self.status = status
    self.data = data

def _a_json(valor):
  """ Convierte tipos que json no conoce: numeric de PostgreSQL y fechas. """
  if isinstance(valor, Decimal):
    return float(valor)
  if isinstance(valor, (date, datetime)):
    return valor.isoformat()
  raise TypeError(f"Tipo {type(valor)} no es serializable a JSON")

def enviar(start_response, respuesta: Response) -> list[bytes]:
  """ Transforma un Response en la respuesta HTTP que espera WSGI. """
  
  estado = f"{respuesta.status} {HTTPStatus(respuesta.status).phrase}"
  if respuesta.data is None:
    cuerpo = b""
  else:
    cuerpo = json.dumps(respuesta.data, default=_a_json, ensure_ascii=False).encode("utf-8")
  encabezados = [
    ("Content-Type", "application/json; charset=utf-8"),
    ("Content-Length", str(len(cuerpo))),
  ] + CORS_HEADERS
  start_response(estado, encabezados)
  return [cuerpo]


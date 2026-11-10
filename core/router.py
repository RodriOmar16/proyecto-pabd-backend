import re
import traceback

from core.http import HttpError, Request, Response

class Router:
  """ Asocia método + ruta con la función (handler) que la atiende. """
  def __init__(self):
    self.rutas = [] # lista de (método, regex, handler)

  def agregar(self, metodo: str, patron: str, handler):
    """ Registra una ruta. Ej: agregar("GET", "/api/customers/{id}", handlers.obtener). """

    # "/api/customers/{id}" -> regex "^/api/customers/(?P<id>[^/]+)$"
    regex = "^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", patron) + "$"
    self.rutas.append((metodo.upper(), re.compile(regex), handler))

  def despachar(self, request: Request) -> Response:
    """ Busca la ruta que coincide con la petición, ejecuta su handler y devuelve la respuesta. """
    #Petición previa que hace el navegador por CORS: solo responder que está permitido
    if request.method == "OPTIONS":
      return Response(204)

    ruta_existe = False
    for metodo, regex, handler in self.rutas:
      coincidencia = regex.match(request.path)
      if not coincidencia:
        continue
      ruta_existe = True
      if metodo != request.method:
        continue
      request.params = coincidencia.groupdict() # { "id": "ALFKI" }
      try:
        return handler(request)
      except HttpError as e:
        return Response(e.status, { "error": e.mensaje })
      except Exception as e:
        traceback.print_exc() #muestra el error en la consola del servidor
        return Response(500, { "error": "Error interno del servidor" })

    if ruta_existe:
      return Response(405, { "error": f"Método {request.method} no permitido para la ruta {request.path}" })
    else:
      return Response(404, { "error": f"No se encontró la ruta {request.path}" })
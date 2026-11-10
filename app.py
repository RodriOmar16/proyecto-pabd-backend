from wsgiref.simple_server import make_server
from config import API_PORT
from core.http import Request, enviar
from core.router import Router
from modules.customers import routes as customers_routes

# --- Registro de módulos: cada integrante agrega una línea de los módulos que vamos haciendo ---
router = Router()
customers_routes.registrar(router)
# products_routes.registrar(router)
# suppliers_routes.registrar(router)

def app(environ, start_response):
    """ Aplicación WSGI: convierte la petición en Request, la despacha y envía la respuesta. """
    respuesta = router.despachar(Request(environ))
    return enviar(start_response, respuesta)

if __name__ == "__main__":
    with make_server("", API_PORT, app) as servidor:
        print(f"API escuchando en http://localhost:{API_PORT} (ctrl + c para detener)")
        servidor.serve_forever()
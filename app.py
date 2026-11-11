import sys

from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server

from config import API_PORT
from core.http import Request, enviar
from core.router import Router
from modules.customers import routes as customers_routes

# --- Registro de módulos: cada integrante agrega una línea de los módulos que vamos haciendo ---
router = Router()
customers_routes.registrar(router)
# products_routes.registrar(router)
# suppliers_routes.registrar(router)

class ServidorConHilos(ThreadingMixIn, WSGIServer):
    """Atiende cada conexión en un hilo propio: el navegador abre varias a la vez
    y con un solo hilo una conexión vacía bloquea a las demás."""
    daemon_threads = True  # los hilos terminan junto con el servidor (Ctrl+C)
    # En Windows, reusar la dirección permite que DOS servidores tomen el mismo puerto
    # sin error. Así, si ya hay una API corriendo, la segunda falla y avisa.
    allow_reuse_address = sys.platform != "win32"

def app(environ, start_response):
    """ Aplicación WSGI: convierte la petición en Request, la despacha y envía la respuesta. """
    respuesta = router.despachar(Request(environ))
    return enviar(start_response, respuesta)

if __name__ == "__main__":
    with make_server("", API_PORT, app, server_class=ServidorConHilos) as servidor:
        print(f"API escuchando en http://localhost:{API_PORT}  (ctrl+c para detener)")
        servidor.serve_forever()
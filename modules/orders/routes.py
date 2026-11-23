from modules.orders import handlers

def registrar(router):
    """ Registrar las rutas del modulo de orders """
    router.agregar("GET", "/api/orders", handlers.listar)
    router.agregar("GET", "/api/orders/{id}", handlers.obtener)
    router.agregar("GET", "/api/orders/{id}/detalle", handlers.detalle)
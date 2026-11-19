from modules.customers import handlers

def registrar(router):
    """Registra las rutas del módulo customers."""
    router.agregar("GET", "/api/customers", handlers.listar)
    router.agregar("GET", "/api/customers/{id}", handlers.obtener)
    router.agregar("POST", "/api/customers", handlers.crear)
    router.agregar("PUT", "/api/customers/{id}", handlers.actualizar)
    router.agregar("PATCH", "/api/customers/{id}/estado", handlers.cambiar_estado)
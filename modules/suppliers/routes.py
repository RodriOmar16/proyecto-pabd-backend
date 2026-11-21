from modules.suppliers import handlers

def registrar(router):
    """Registra las rutas del módulo suppliers."""
    router.agregar("GET", "/api/suppliers", handlers.listar)
    router.agregar("GET", "/api/suppliers/{id}", handlers.obtener)
    router.agregar("POST", "/api/suppliers", handlers.crear)
    router.agregar("PUT", "/api/suppliers/{id}", handlers.actualizar)
    router.agregar("DELETE", "/api/suppliers/{id}", handlers.eliminar)
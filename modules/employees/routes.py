from modules.employees import handlers

def registrar(router):
    """Registra las rutas del módulo employees."""
    router.agregar("GET", "/api/employees", handlers.listar)
    router.agregar("GET", "/api/employees/{id}", handlers.obtener)
    router.agregar("POST", "/api/employees", handlers.crear)
    router.agregar("PUT", "/api/employees/{id}", handlers.actualizar)
    router.agregar("PATCH", "/api/employees/{id}/estado", handlers.cambiar_estado)

from modules.orders import handlers

def registrar(router):
    """Registra las rutas del módulo orders."""
    # Listas para los seleccionables de los filtros
    router.agregar("GET", "/api/orders/clientes", handlers.clientes)
    router.agregar("GET", "/api/orders/empleados", handlers.empleados)
    router.agregar("GET", "/api/orders/transportistas", handlers.transportistas)

    router.agregar("GET", "/api/orders", handlers.listar)
    router.agregar("GET", "/api/orders/{id}", handlers.obtener)
    router.agregar("GET", "/api/orders/{id}/detalle", handlers.detalle)
# Northwind CRUD – Backend

API REST en Python **sin framework** (solo librería estándar + `psycopg`) sobre la base **Northwind** en PostgreSQL.
Proyecto de la materia PABD – UNSa 2026.

**Integrantes y módulos**

| Integrante | Módulos |
| --- | --- |
| Rodrigo Miranda | `customers` (+ `core/`, base del proyecto) |
| <compañero 2> | <tabla/s> |
| <compañero 3> | <tabla/s> |

---

## Requisitos

- Python 3.10 o superior
- PostgreSQL con la base Northwind restaurada

## Instalación

```powershell
git clone <url-del-repo>
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `.env` con los datos de **tu** PostgreSQL (puerto, contraseña, nombre de la base, esquema).
El `.env` **no se sube** al repo; solo se sube `.env.example`.

## Ejecutar

```powershell
python app.py
```

La API queda en `http://localhost:8000` (o el puerto definido en `API_PORT`).

---

## Estructura

```text
backend/
├── app.py            # levanta el servidor y registra los módulos
├── config.py         # lee el .env
├── db.py             # conexión a PostgreSQL
├── core/             # compartido: no modificar sin avisar al grupo
│   ├── http.py       # leer JSON, query params, responder JSON, CORS
│   └── router.py     # asocia método + ruta → función
└── modules/          # un módulo por tabla, cada integrante trabaja en los suyos
    └── customers/
        ├── repository.py   # SQL de la tabla (sin nada de HTTP)
        ├── handlers.py     # lógica HTTP: valida, llama al repository, responde
        └── routes.py       # registra las rutas del módulo
```

## Convenciones de cada módulo

Todos los módulos tienen los **mismos 3 archivos** y las **mismas funciones**:

| Archivo | Funciones |
| --- | --- |
| `repository.py` | `listar(page, size, q)` → `(filas, total)` · `obtener(id)` · `crear(datos)` · `actualizar(id, datos)` · `eliminar(id)` |
| `handlers.py` | `listar(req)` · `obtener(req)` · `crear(req)` · `actualizar(req)` · `eliminar(req)` |
| `routes.py` | `registrar(router)` |

Reglas:
- **Siempre consultas parametrizadas** (`%s`); nunca armar SQL concatenando texto.
- El `repository` no sabe de HTTP; el `handler` no escribe SQL.
- Cada integrante modifica **solo sus carpetas** dentro de `modules/`. Para tocar `core/`, `app.py` o `db.py`, avisar al grupo.

## Contrato de la API (igual para todas las tablas)

| Método | Ruta | Respuesta OK |
| --- | --- | --- |
| GET | `/api/<tabla>?page=1&size=20&q=texto` | 200 – listado paginado |
| GET | `/api/<tabla>/{id}` | 200 – el registro |
| POST | `/api/<tabla>` | 201 – el registro creado |
| PUT | `/api/<tabla>/{id}` | 200 – el registro actualizado |
| DELETE | `/api/<tabla>/{id}` | 204 – sin contenido |

**Listado paginado:**

```json
{ "data": [ ... ], "page": 1, "size": 20, "total": 91 }
```

- `page`: página, desde 1 (por defecto 1)
- `size`: registros por página (por defecto 20, máximo 100)
- `q`: texto de búsqueda opcional (cada módulo define en qué columnas busca)

**Errores** (siempre con este formato):

```json
{ "error": "Mensaje descriptivo" }
```

| Código | Cuándo |
| --- | --- |
| 400 | datos inválidos o faltantes |
| 404 | el registro o la ruta no existen |
| 409 | conflicto: clave duplicada o el registro está referenciado por otra tabla (FK) |
| 500 | error inesperado del servidor |

## Cómo agregar un módulo nuevo

1. Copiar la carpeta `modules/customers` con el nombre de la nueva tabla.
2. En `repository.py`, adaptar el SQL: tabla, clave primaria, columnas y columnas de búsqueda.
3. En `handlers.py`, adaptar las validaciones (campos obligatorios).
4. En `routes.py`, cambiar `/api/customers` por `/api/<tabla>`.
5. Registrar el módulo en `app.py` (una línea).
6. Probar los 5 endpoints antes de hacer el pull request.

## Trabajo con Git

- `main` siempre tiene que funcionar.
- Cada integrante trabaja en su rama: `feature/<tabla>` (ej. `feature/products`).
- Al terminar: `git push` de la rama y **pull request** hacia `main`; otro integrante lo revisa antes de unir.
- Antes de empezar cada día: `git pull origin main` para traer los cambios del resto.

## Migraciones
1. Todo cambio de estructura en la base va como migración nueva. Nunca se hace a mano.
2. Nunca se modifica una migración que ya se subió: si hay que corregir algo, se crea otra (002_...).
3. Después de cada git pull: python migrate.py.
4. Para no chocar números entre los 3, conviene avisar en el grupo antes de crear una migración.
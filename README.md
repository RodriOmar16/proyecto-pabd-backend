# Northwind CRUD – Backend (API)

API REST en Python **sin framework** (librería estándar + `psycopg` 3) sobre la base **Northwind** en PostgreSQL.
Proyecto de la materia PABD – Tecnicatura Universitaria en Programación – UNSa 2026.

**Integrantes y módulos**

| Integrante | Módulos |
| --- | --- |
| Rodrigo Miranda | `customers` (+ `core/`, migraciones, base del proyecto) |
| <compañero 2> | <tabla/s> |
| <compañero 3> | <tabla/s> |

---

## Arquitectura

```text
Pantalla (front web: Next.js)        ← solo muestra datos y manda pedidos
        │  HTTP / JSON
        ▼
API Python (esta carpeta)            ← conexión y llamadas a la base (driver psycopg 3)
        │  SQL
        ▼
PostgreSQL – Northwind               ← la lógica del ABM vive acá (funciones PL/pgSQL)
```

La pantalla puede ser web, Android o escritorio: todas usarían la misma API, y la API es la única que se conecta a la base.

---

## Antes y ahora: la lógica del ABM pasó a la base de datos

### Antes

El ABM se resolvía **en Python**:

- `handlers.py` validaba los datos (campos obligatorios, largos máximos).
- `repository.py` armaba el SQL directamente: `INSERT INTO customers ...`, `UPDATE customers ...`.

### Ahora (pedido de la cátedra)

La cátedra pide que **la lógica viva en la base** y que la aplicación sea una "cáscara":
**la app solo llama a UNA función de la base y le pasa los datos como parámetros.**

- Las validaciones y las operaciones de alta, modificación y baja están en la función
  **`fn_abm_cliente`** (PL/pgSQL), creada con la migración `002_fn_abm_cliente.sql`.
- Un solo punto de entrada; **la acción decide qué hacer**:

| `p_accion` | Qué hace |
| --- | --- |
| `A` | alta |
| `M` | modificación (solo clientes habilitados) |
| `B` | baja lógica: alterna entre inhabilitado y habilitado (no se borra el registro) |

- Si algo no es válido, la función lanza `RAISE EXCEPTION` con un mensaje claro.
  Ese error **viaja al driver** (psycopg), la API lo convierte en una respuesta HTTP
  y la pantalla muestra **el mismo mensaje que escribió la base**.

```sql
-- Así llama la API a la base (repository.py)
SELECT fn_abm_cliente(p_accion => 'A', p_id => 'TESTA', p_nombre => 'Empresa', ...);
```

| Error en la función | SQLSTATE | psycopg lo recibe como | La API responde |
| --- | --- | --- | --- |
| validación (`RAISE EXCEPTION`) | `P0001` | `RaiseException` | 400 |
| el registro no existe o está inhabilitado | `P0002` (`no_data_found`) | `NoDataFound` | 404 |
| código repetido | `23505` (`unique_violation`) | `UniqueViolation` | 409 |

Los **listados y consultas** siguen siendo `SELECT` desde Python (`listar`, `obtener`).

### Cómo se trabaja de ahora en adelante

| Capa | Responsabilidad | NO hace |
| --- | --- | --- |
| **Base de datos** (`migrations/`) | funciones de ABM: validaciones, `INSERT` / `UPDATE`, mensajes de error | — |
| **`repository.py`** | `SELECT` para listar/obtener y **una llamada** a la función de ABM | no valida, no hace `INSERT` ni `UPDATE` directos |
| **`handlers.py`** | lee la petición, llama al repository y traduce los errores de la base a HTTP | no valida datos, no escribe SQL |
| **`routes.py`** | asocia cada URL con su handler | — |

Para cada tabla con ABM se crea su propia función (`fn_abm_<tabla>`) en una migración nueva,
siguiendo el modelo de `fn_abm_cliente`.

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

Editar `.env` con los datos de **tu** PostgreSQL (puerto, contraseña, nombre de la base, esquema)
y el puerto de la API (`API_PORT`). El `.env` **no se sube** al repo; solo `.env.example`.

## Migraciones (estructura y funciones de la base)

Todo cambio en la base (columnas, funciones, vistas) se hace con un archivo SQL numerado en `migrations/`.
La tabla `schema_migrations` registra en **cada base** qué migraciones ya se aplicaron.

```powershell
python migrate.py
```

| Migración | Qué hace |
| --- | --- |
| `001_customers_disabled.sql` | agrega la columna `disabled` (baja lógica) a `customers` |
| `002_fn_abm_cliente.sql` | crea la función `fn_abm_cliente` (ABM de clientes) |

Reglas:
- **Después de cada `git pull`**, ejecutar `python migrate.py`.
- **Nunca modificar una migración ya subida**: para corregir algo, crear una nueva (`003_...`).
- Avisar al grupo antes de crear una migración, para no repetir el número.

## Ejecutar

```powershell
python app.py
```

La API queda en `http://localhost:<API_PORT>`.

- El servidor atiende **cada conexión en un hilo propio**: con un solo hilo, el navegador
  (que abre varias conexiones a la vez) dejaba pedidos colgados.
- En Windows, si ya hay una API corriendo en ese puerto, la segunda **falla con un error**
  en lugar de levantarse en silencio. Si pasa, cerrar la anterior (`Ctrl+C` o
  `netstat -ano | findstr :<puerto>` y `Stop-Process -Id <PID>`).

---

## Estructura

```text
backend/
├── app.py            # levanta el servidor (con hilos) y registra los módulos
├── config.py         # lee el .env
├── db.py             # conexión a PostgreSQL (psycopg 3)
├── migrate.py        # aplica las migraciones pendientes
├── migrations/       # SQL numerado: columnas, funciones de ABM, vistas
├── core/             # compartido: no modificar sin avisar al grupo
│   ├── http.py       # Request, Response, HttpError, JSON, CORS
│   └── router.py     # asocia método + ruta → función; maneja errores 404/405/500
└── modules/          # un módulo por tabla
    └── customers/
        ├── repository.py   # SELECT de listado + llamada a fn_abm_cliente
        ├── handlers.py     # traduce la petición y los errores de la base a HTTP
        └── routes.py       # registra las rutas del módulo
```

## Convenciones de cada módulo

| Archivo | Funciones |
| --- | --- |
| `repository.py` | `listar(page, size, filtros, disabled)` → `(filas, total)` · `obtener(id)` · `crear(id, datos)` · `actualizar(id, datos)` · `cambiar_estado(id)` |
| `handlers.py` | `listar` · `obtener` · `crear` · `actualizar` · `cambiar_estado` (cada uno recibe `req`) |
| `routes.py` | `registrar(router)` |

Reglas:
- **Siempre consultas parametrizadas** (`%s`); nunca armar SQL concatenando datos del usuario.
- Los nombres de columna para filtros salen de una **lista fija** (`COLUMNAS_BUSCABLES`).
- Cada integrante modifica **solo sus carpetas** de `modules/` y sus migraciones.
  Para tocar `core/`, `app.py` o `db.py`, avisar al grupo.

## Contrato de la API (igual para todas las tablas)

| Método | Ruta | Respuesta OK |
| --- | --- | --- |
| GET | `/api/<tabla>?page=1&size=20&disabled=false&<columna>=texto` | 200 – listado paginado |
| GET | `/api/<tabla>/{id}` | 200 – el registro (solo habilitados) |
| POST | `/api/<tabla>` | 201 – el registro creado |
| PUT | `/api/<tabla>/{id}` | 200 – el registro actualizado |
| PATCH | `/api/<tabla>/{id}/estado` | 200 – `{id, nombre, disabled}`: alterna habilitado / inhabilitado |

No hay `DELETE`: la baja es lógica.

**Parámetros del listado**

- `page`: página, desde 1 (por defecto 1)
- `size`: registros por página (por defecto 20, máximo 100)
- `disabled`: `false` (por defecto) lista los habilitados; `true`, los inhabilitados
- `<columna>=texto`: un filtro por cada columna buscable (ej. `companyname=ana&country=mex`).
  Se combinan con AND y no distinguen mayúsculas.

```json
{ "data": [ ... ], "page": 1, "size": 20, "total": 91 }
```

**Errores** (siempre con este formato; el mensaje viene de la base cuando corresponde):

```json
{ "error": "El código debe tener exactamente 5 letras" }
```

| Código | Cuándo |
| --- | --- |
| 400 | datos inválidos (validación de la función de la base) |
| 404 | el registro o la ruta no existen |
| 405 | la ruta existe pero no con ese método |
| 409 | conflicto: código repetido |
| 500 | error inesperado del servidor (el detalle se ve en la consola de la API) |

## Cómo agregar un módulo nuevo

1. Crear la migración con la función `fn_abm_<tabla>(p_accion, p_id, ...)`, siguiendo el modelo de
   `002_fn_abm_cliente.sql`: validaciones con `RAISE EXCEPTION` y los `ERRCODE` de la tabla de errores.
   Probarla primero con `psql`.
2. Si la tabla necesita baja lógica, agregar la columna `disabled` en una migración.
3. Copiar la carpeta `modules/customers` con el nombre de la tabla.
4. En `repository.py`: adaptar el `SELECT` del listado, `COLUMNAS_BUSCABLES` y la llamada a la función.
5. En `routes.py`: cambiar `/api/customers` por `/api/<tabla>`.
6. Registrar el módulo en `app.py` (una línea).
7. Probar los endpoints antes del pull request.

## Trabajo con Git

- `main` siempre tiene que funcionar.
- Cada integrante trabaja en su rama: `feature/<tabla>` (ej. `feature/products`).
- Al terminar: `git push` de la rama y **pull request** hacia `main`; otro integrante lo revisa antes de unir.
- Antes de empezar cada día: `git pull origin main` y `python migrate.py`.
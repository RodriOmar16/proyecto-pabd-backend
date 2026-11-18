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
API Python (esta carpeta)            ← "cáscara": solo llama a funciones de la base (driver psycopg 3)
        │  SQL: SELECT fn_...(...)
        ▼
PostgreSQL – Northwind               ← TODA la lógica vive acá: vistas + funciones PL/pgSQL
```

La pantalla puede ser web, Android o escritorio: todas usarían la misma API, y la API es la única que se conecta a la base.

---

## Antes y ahora: la lógica pasó a la base de datos

### Antes

Todo se resolvía **en Python**:

- `handlers.py` validaba los datos (campos obligatorios, largos máximos).
- `repository.py` armaba el SQL directamente: `SELECT ... WHERE ... LIMIT`, `INSERT INTO customers ...`, `UPDATE customers ...`.

### Ahora (pedido de la cátedra: independencia del conocimiento)

La cátedra pide que **el conocimiento viva en la base, al lado del DBMS**, y que la aplicación sea una "cáscara":
**la app no escribe SQL sobre tablas; solo llama a funciones de la base y les pasa los datos como parámetros.**
Así, cualquier aplicación (web, móvil, escritorio) que use la base obtiene las mismas reglas.

Cada tabla tiene tres objetos en la base:

| Objeto | Para qué | Ejemplo en clientes |
| --- | --- | --- |
| **Vista** | define **qué datos** de la tabla ve la aplicación | `vw_clientes` |
| **Función de consulta** | **lecturas**: obtener uno o listar con filtros y paginado (lee de la vista) | `fn_consulta_cliente` |
| **Función de ABM** | **escrituras**: alta, modificación y baja lógica, con sus validaciones | `fn_abm_cliente` |

#### Lecturas: `fn_consulta_cliente` (migración `003_vw_clientes.sql`)

Un solo punto de entrada para consultar; **los parámetros deciden qué hace**:

| Llamada | Qué devuelve |
| --- | --- |
| con `p_id` | ese cliente (solo si está habilitado) |
| sin `p_id` | la página pedida (`p_page`, `p_size`), filtrada por `p_disabled` y por los filtros de texto |

Devuelve **filas** (`RETURNS TABLE`) con las columnas de la vista más `total`: la cantidad de registros
que cumplen los filtros, sin importar la página (se calcula con `count(*) OVER ()`).

```sql
-- Obtener uno
SELECT * FROM fn_consulta_cliente(p_id => 'ALFKA');

-- Listar: página 1 de 10, clientes habilitados de México
SELECT * FROM fn_consulta_cliente(p_page => 1, p_size => 10, p_pais => 'mex');
```

- Filtros vacíos o `NULL` no filtran; se combinan con AND y no distinguen mayúsculas (`ILIKE`).
- Máximo 100 registros por página.
- Si el cliente no existe o la página es inválida, la función lanza `RAISE EXCEPTION` (ver tabla de errores).

| Columna en la URL | Parámetro de la función |
| --- | --- |
| `customerid` | `p_codigo` |
| `companyname` | `p_nombre` |
| `contactname` | `p_contacto` |
| `contacttitle` | `p_cargo` |
| `address` | `p_direccion` |
| `city` | `p_ciudad` |
| `region` | `p_region` |
| `postalcode` | `p_cp` |
| `country` | `p_pais` |
| `phone` | `p_telefono` |
| `fax` | `p_fax` |

#### Escrituras: `fn_abm_cliente` (migración `002_fn_abm_cliente.sql`)

Un solo punto de entrada para modificar datos; **la acción decide qué hacer**:

| `p_accion` | Qué hace |
| --- | --- |
| `A` | alta |
| `M` | modificación (solo clientes habilitados) |
| `B` | baja lógica: alterna entre inhabilitado y habilitado (no se borra el registro) |

Devuelve un mensaje de texto (ej. `Cliente ALFKA inhabilitado`).

```sql
SELECT fn_abm_cliente(p_accion => 'A', p_id => 'TESTA', p_nombre => 'Empresa', ...);
```

#### Errores: viajan de la base a la pantalla

Si algo no es válido, la función lanza `RAISE EXCEPTION` con un mensaje claro.
Ese error **viaja al driver** (psycopg), la API lo convierte en una respuesta HTTP
y la pantalla muestra **el mismo mensaje que escribió la base**.

| Error en la función | SQLSTATE | psycopg lo recibe como | La API responde |
| --- | --- | --- | --- |
| validación (`RAISE EXCEPTION`) | `P0001` | `RaiseException` | 400 |
| el registro no existe o está inhabilitado | `P0002` (`no_data_found`) | `NoDataFound` | 404 |
| código repetido | `23505` (`unique_violation`) | `UniqueViolation` | 409 |

### Cómo se trabaja de ahora en adelante

| Capa | Responsabilidad | NO hace |
| --- | --- | --- |
| **Base de datos** (`migrations/`) | vista, función de consulta y función de ABM: validaciones, filtros, paginado, `INSERT` / `UPDATE`, mensajes de error | — |
| **`repository.py`** | **llama** a las funciones de la base pasando los parámetros | no escribe `SELECT`, `INSERT` ni `UPDATE` sobre tablas, no valida |
| **`handlers.py`** | lee la petición, llama al repository y traduce los errores de la base a HTTP | no valida datos, no escribe SQL |
| **`routes.py`** | asocia cada URL con su handler | — |

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

Todo cambio en la base (columnas, vistas, funciones) se hace con un archivo SQL numerado en `migrations/`.
La tabla `schema_migrations` registra en **cada base** qué migraciones ya se aplicaron.

```powershell
python migrate.py
```

| Migración | Qué hace |
| --- | --- |
| `001_customers_disabled.sql` | agrega la columna `disabled` (baja lógica) a `customers` |
| `002_fn_abm_cliente.sql` | crea la función `fn_abm_cliente` (escrituras: ABM de clientes) |
| `003_vw_clientes.sql` | crea la vista `vw_clientes` y la función `fn_consulta_cliente` (lecturas: obtener y listar) |

Reglas:
- **Después de cada `git pull`**, ejecutar `python migrate.py`.
- **Nunca modificar una migración ya subida**: para corregir algo, crear una nueva (`004_...`).
- Avisar al grupo antes de crear una migración, para no repetir el número.
- No crear archivos de migración vacíos: `migrate.py` los registraría como aplicados sin hacer nada.

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
├── migrations/       # SQL numerado: columnas, vistas, funciones de consulta y de ABM
├── core/             # compartido: no modificar sin avisar al grupo
│   ├── http.py       # Request, Response, HttpError, JSON, CORS
│   └── router.py     # asocia método + ruta → función; maneja errores 404/405/500
└── modules/          # un módulo por tabla
    └── customers/
        ├── repository.py   # llamadas a fn_consulta_cliente y fn_abm_cliente
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
- El SQL de `repository.py` es **fijo**: siempre se pasan todos los parámetros y los filtros que no vienen van como `NULL`.
- Los filtros aceptados salen de una **lista fija** (`COLUMNAS_BUSCABLES`).
- Cada integrante modifica **solo sus carpetas** de `modules/` y sus migraciones.
  Para tocar `core/`, `app.py` o `db.py`, avisar al grupo.

## Contrato de la API (igual para todas las tablas)

| Método | Ruta | Respuesta OK |
| --- | --- | --- |
| GET | `/api/<tabla>?page=1&size=20&disabled=false&<columna>=texto` | 200 – listado paginado |
| GET | `/api/<tabla>/{id}` | 200 – el registro (solo habilitados) |
| POST | `/api/<tabla>` | 201 – el registro creado |
| PUT | `/api/<tabla>/{id}` | 200 – el registro actualizado |
| PATCH | `/api/<tabla>/{id}/estado` | 200 – `{id, mensaje}`: alterna habilitado / inhabilitado; el mensaje viene de la base |

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

Si se pide una página posterior a la última, `data` viene vacío y `total` en 0
(el total viaja en las filas que devuelve la función).

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

1. Si la tabla necesita baja lógica, agregar la columna `disabled` en una migración.
2. Crear la migración de **lecturas**, siguiendo el modelo de `003_vw_clientes.sql`:
   - la vista `vw_<tabla>` con las columnas que se exponen;
   - la función `fn_consulta_<tabla>(p_id, p_disabled, p_page, p_size, <filtros>)` que lee de la vista
     y devuelve `RETURNS TABLE (... , total bigint)`.
3. Crear la migración de **escrituras** `fn_abm_<tabla>(p_accion, p_id, ...)`, siguiendo el modelo de
   `002_fn_abm_cliente.sql`: validaciones con `RAISE EXCEPTION` y los `ERRCODE` de la tabla de errores.
4. Probar las funciones primero con `psql`.
5. Copiar la carpeta `modules/customers` con el nombre de la tabla.
6. En `repository.py`: adaptar `COLUMNAS_BUSCABLES` y las llamadas a las funciones (mismos nombres de parámetros).
7. En `routes.py`: cambiar `/api/customers` por `/api/<tabla>`.
8. Registrar el módulo en `app.py` (una línea).
9. Probar los endpoints antes del pull request.

## Trabajo con Git

- `main` siempre tiene que funcionar.
- Cada integrante trabaja en su rama: `feature/<tabla>` (ej. `feature/products`).
- Al terminar: `git push` de la rama y **pull request** hacia `main`; otro integrante lo revisa antes de unir.
- Antes de empezar cada día: `git pull origin main` y `python migrate.py`.
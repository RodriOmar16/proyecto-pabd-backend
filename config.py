import os
from pathlib import Path


def load_env(path: Path = Path(__file__).with_name(".env")) -> None:
    """Lee un archivo .env (CLAVE=valor) y carga cada clave en os.environ."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        linea = line.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue  # salta líneas vacías, comentarios y líneas inválidas
        clave, valor = linea.split("=", 1)
        # setdefault: si la variable ya existe en el sistema, tiene prioridad sobre el .env
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


load_env()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "northwind"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "options": f"-c search_path={os.environ.get('DB_SCHEMA', 'public')}",
}

API_PORT = int(os.environ.get("API_PORT", "8000"))

""" Aplica en orden las migraciones SQL pendientes de la carpeta migrations/. """
from pathlib import Path
from db import get_connection

CARPETA = Path(__file__).with_name("migrations")

def main():
    with get_connection() as conn:
        conn.autocommit = True # cada migración maneja su propia transacción

        # Tabla de control: qué migraciones ya se aplicaron en ESTA base
        conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations(
                version     text PRIMARY KEY,
                applied_at  timestamp NOT NULL DEFAULT now()
            )"""
        )

        aplicadas = { f["version"] for f in conn.execute("SELECT version FROM schema_migrations") }

        pendientes = sorted(p for p in CARPETA.glob("*.sql") if p.stem not in aplicadas)
        if not pendientes:
            print("No hay migraciones pendientes.")
            return

        for archivo in pendientes:
            print(f"Aplicando {archivo.name} ...", end="")
            #Todo o nada: si el SQL falla, no se registra y la base queda como estaba

            with conn.transaction():
                conn.execute(archivo.read_text(encoding="utf-8-sig"))
                conn.execute("INSERT INTO schema_migrations(version) VALUES(%s)", (archivo.stem,))

if __name__ == "__main__":
    main()
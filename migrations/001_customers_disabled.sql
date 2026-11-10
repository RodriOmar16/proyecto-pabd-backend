-- Borrado lógico: en vez de eliminar clientes, se marcan como deshabilitados
ALTER TABLE customers ADD COLUMN IF NOT EXISTS disabled boolean NOT NULL DEFAULT false;
-- Borrado lógico: en vez de eliminar empleados, se marcan como deshabilitados
ALTER TABLE employees ADD COLUMN IF NOT EXISTS disabled boolean NOT NULL DEFAULT false;
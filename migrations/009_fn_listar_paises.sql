--Funcion auxiliar para mostrar la lista de paises en los form de employees

-- ---------- Vista ----------
CREATE OR REPLACE VIEW vw_countries AS
SELECT
    c.country
FROM countries c;

CREATE OR REPLACE FUNCTION fn_listar_paises() RETURNS TABLE (
    country varchar(3)
) AS $$
BEGIN
    RETURN QUERY
        SELECT v.country
        FROM vw_countries v;
END;
$$ LANGUAGE plpgsql;
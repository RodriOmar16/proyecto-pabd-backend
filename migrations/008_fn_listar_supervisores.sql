--Funcion auxiliar para mostrar la lista de empleados en los form de employees

CREATE OR REPLACE FUNCTION fn_listar_supervisores(
    p_id int DEFAULT NULL
) RETURNS TABLE (
    employeeid int,
    lastname varchar,
    firstname varchar
) AS $$
BEGIN
    RETURN QUERY
        SELECT v.employeeid, v.lastname, v.firstname
        FROM vw_employees v
        WHERE NOT v.disabled
        AND (p_id IS NULL OR v.employeeid <> p_id);
END;
$$ LANGUAGE plpgsql;
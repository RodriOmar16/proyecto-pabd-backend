ALTER TABLE products
DROP CONSTRAINT IF EXISTS products_fk1;

ALTER TABLE products
ADD CONSTRAINT products_fk1
    FOREIGN KEY (supplierid)
    REFERENCES suppliers (supplierid)
    ON DELETE SET NULL;
ALTER TABLE public.products
DROP CONSTRAINT IF EXISTS products_fk1;

ALTER TABLE public.products
ADD CONSTRAINT products_fk1
    FOREIGN KEY (supplierid)
    REFERENCES public.suppliers (supplierid)
    ON DELETE SET NULL;
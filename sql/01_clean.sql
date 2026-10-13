-- Clean transactions. Rules (each documented in the README):
--   * invoices starting with 'C' are cancellations/returns -> kept in a separate view
--   * non-product stock codes (postage, fees, samples, bank charges) are dropped
--   * rows with price <= 0 or quantity <= 0 are dropped from sales
CREATE OR REPLACE VIEW sales AS
SELECT
    invoice,
    stock_code,
    trim(description)                      AS description,
    quantity,
    unit_price,
    quantity * unit_price                  AS revenue,
    invoice_ts,
    CAST(invoice_ts AS DATE)               AS invoice_date,
    date_trunc('month', invoice_ts)::DATE  AS invoice_month,
    CAST(customer_id AS BIGINT)            AS customer_id,
    country
FROM raw_sales
WHERE invoice NOT LIKE 'C%'
  AND quantity > 0
  AND unit_price > 0
  AND stock_code NOT IN ('POST', 'D', 'DOT', 'M', 'BANK CHARGES', 'S', 'AMAZONFEE', 'B', 'CRUK')
  AND stock_code NOT LIKE 'gift_%'
  AND stock_code NOT LIKE 'ADJUST%';

CREATE OR REPLACE VIEW returns AS
SELECT
    invoice,
    stock_code,
    quantity,
    unit_price,
    quantity * unit_price                  AS revenue,
    invoice_ts,
    date_trunc('month', invoice_ts)::DATE  AS invoice_month,
    CAST(customer_id AS BIGINT)            AS customer_id,
    country
FROM raw_sales
WHERE invoice LIKE 'C%';

-- Sales with a known customer (needed for cohort and RFM work)
CREATE OR REPLACE VIEW customer_sales AS
SELECT * FROM sales WHERE customer_id IS NOT NULL;

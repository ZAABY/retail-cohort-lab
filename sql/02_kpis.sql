-- Monthly KPIs: revenue, orders, customers, average order value, new vs returning customers.
CREATE OR REPLACE VIEW first_purchase AS
SELECT customer_id, min(invoice_month) AS first_month
FROM customer_sales
GROUP BY customer_id;

CREATE OR REPLACE VIEW monthly_kpis AS
WITH orders AS (
    SELECT invoice, invoice_month, customer_id, sum(revenue) AS order_revenue
    FROM sales
    GROUP BY invoice, invoice_month, customer_id
)
SELECT
    o.invoice_month                                              AS month,
    round(sum(o.order_revenue), 2)                               AS revenue,
    count(*)                                                     AS orders,
    count(DISTINCT o.customer_id)                                AS customers,
    round(sum(o.order_revenue) / count(*), 2)                    AS avg_order_value,
    count(DISTINCT o.customer_id)
        FILTER (WHERE f.first_month = o.invoice_month)           AS new_customers,
    count(DISTINCT o.customer_id)
        FILTER (WHERE f.first_month < o.invoice_month)           AS returning_customers
FROM orders o
LEFT JOIN first_purchase f USING (customer_id)
GROUP BY o.invoice_month
ORDER BY o.invoice_month;

-- Month-over-month revenue growth with a window function
CREATE OR REPLACE VIEW monthly_growth AS
SELECT
    month,
    revenue,
    round(100.0 * (revenue - lag(revenue) OVER (ORDER BY month))
          / lag(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM monthly_kpis;

CREATE OR REPLACE VIEW revenue_by_country AS
SELECT country, round(sum(revenue), 2) AS revenue,
       count(DISTINCT customer_id) AS customers,
       count(DISTINCT invoice) AS orders
FROM sales
GROUP BY country
ORDER BY revenue DESC;

CREATE OR REPLACE VIEW top_products AS
SELECT stock_code, any_value(description) AS description,
       sum(quantity) AS units, round(sum(revenue), 2) AS revenue
FROM sales
GROUP BY stock_code
ORDER BY revenue DESC;

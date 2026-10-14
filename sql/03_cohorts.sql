-- Monthly acquisition cohorts and retention.
-- cohort_month = month of a customer's first purchase;
-- month_index  = months since that first purchase (0 = acquisition month).
CREATE OR REPLACE VIEW cohort_activity AS
SELECT DISTINCT
    f.first_month                                                         AS cohort_month,
    date_diff('month', f.first_month, s.invoice_month)                    AS month_index,
    s.customer_id
FROM customer_sales s
JOIN first_purchase f USING (customer_id);

CREATE OR REPLACE VIEW cohort_retention AS
WITH sizes AS (
    SELECT cohort_month, count(*) AS cohort_size
    FROM cohort_activity
    WHERE month_index = 0
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_index,
    count(*)                                         AS active_customers,
    z.cohort_size,
    round(100.0 * count(*) / z.cohort_size, 1)       AS retention_pct
FROM cohort_activity a
JOIN sizes z USING (cohort_month)
GROUP BY a.cohort_month, a.month_index, z.cohort_size
ORDER BY a.cohort_month, a.month_index;

-- Cohort revenue: cumulative revenue per acquired customer
CREATE OR REPLACE VIEW cohort_ltv AS
WITH rev AS (
    SELECT f.first_month AS cohort_month,
           date_diff('month', f.first_month, s.invoice_month) AS month_index,
           sum(s.revenue) AS revenue
    FROM customer_sales s
    JOIN first_purchase f USING (customer_id)
    GROUP BY 1, 2
),
sizes AS (
    SELECT first_month AS cohort_month, count(*) AS cohort_size
    FROM first_purchase
    GROUP BY first_month
)
SELECT r.cohort_month, r.month_index,
       round(sum(r.revenue) OVER (PARTITION BY r.cohort_month ORDER BY r.month_index)
             / z.cohort_size, 2) AS cumulative_revenue_per_customer
FROM rev r JOIN sizes z USING (cohort_month)
ORDER BY r.cohort_month, r.month_index;

-- RFM segmentation: recency, frequency, monetary value, scored 1-5 with NTILE.
CREATE OR REPLACE VIEW rfm_base AS
SELECT
    customer_id,
    date_diff('day', max(invoice_date), (SELECT max(invoice_date) FROM customer_sales) + 1) AS recency_days,
    count(DISTINCT invoice)                                                                 AS frequency,
    round(sum(revenue), 2)                                                                  AS monetary
FROM customer_sales
GROUP BY customer_id;

CREATE OR REPLACE VIEW rfm_scored AS
SELECT
    *,
    ntile(5) OVER (ORDER BY recency_days DESC)  AS r_score,   -- 5 = most recent
    ntile(5) OVER (ORDER BY frequency)          AS f_score,
    ntile(5) OVER (ORDER BY monetary)           AS m_score
FROM rfm_base;

CREATE OR REPLACE VIEW rfm_segments AS
SELECT
    *,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New / promising'
        WHEN r_score <= 2 AND f_score >= 4 THEN 'At risk (was frequent)'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost / hibernating'
        ELSE 'Needs attention'
    END AS segment
FROM rfm_scored;

CREATE OR REPLACE VIEW segment_summary AS
SELECT
    segment,
    count(*)                                   AS customers,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_customers,
    round(sum(monetary), 0)                    AS revenue,
    round(100.0 * sum(monetary) / sum(sum(monetary)) OVER (), 1) AS pct_revenue,
    round(avg(recency_days), 0)                AS avg_recency_days,
    round(avg(frequency), 1)                   AS avg_orders
FROM rfm_segments
GROUP BY segment
ORDER BY revenue DESC;

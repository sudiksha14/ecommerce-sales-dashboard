-- ============================================================
-- Query 2: Customer Cohort Analysis
-- Purpose : Group customers by their first purchase month.
--           Track how many return in subsequent months.
--           Reveals true retention rate beyond the 97% 1-time stat.
-- ============================================================

WITH customer_first_order AS (
    -- Find each customer's first purchase month
    SELECT
        f.customer_key,
        MIN(d.year * 100 + d.month)          AS cohort_month_key,
        MIN(d.full_date)                      AS first_order_date,
        DATE_TRUNC('month', MIN(CAST(d.full_date AS DATE)))
                                              AS cohort_month
    FROM fact f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY f.customer_key
),

customer_orders AS (
    -- All orders with month info
    SELECT
        f.customer_key,
        DATE_TRUNC('month', CAST(d.full_date AS DATE)) AS order_month,
        COUNT(f.order_id)                     AS orders_that_month,
        SUM(f.total_payment)                  AS revenue_that_month
    FROM fact f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY f.customer_key, DATE_TRUNC('month', CAST(d.full_date AS DATE))
),

cohort_data AS (
    SELECT
        cfo.cohort_month,
        co.order_month,
        -- Month number since first purchase (0 = acquisition month)
        DATEDIFF('month', cfo.cohort_month, co.order_month)
                                              AS months_since_first,
        COUNT(DISTINCT co.customer_key)       AS active_customers,
        SUM(co.orders_that_month)             AS total_orders,
        ROUND(SUM(co.revenue_that_month), 2)  AS cohort_revenue
    FROM customer_first_order cfo
    JOIN customer_orders co ON cfo.customer_key = co.customer_key
    WHERE co.order_month >= cfo.cohort_month
    GROUP BY cfo.cohort_month, co.order_month,
             DATEDIFF('month', cfo.cohort_month, co.order_month)
),

cohort_size AS (
    -- Total customers acquired per cohort month
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_key)          AS cohort_size
    FROM customer_first_order
    GROUP BY cohort_month
)

SELECT
    cd.cohort_month,
    cs.cohort_size,
    cd.order_month,
    cd.months_since_first,
    cd.active_customers,
    -- Retention rate = active this month / cohort size
    ROUND(cd.active_customers * 100.0 / cs.cohort_size, 2)
                                              AS retention_rate_pct,
    cd.total_orders,
    cd.cohort_revenue
FROM cohort_data cd
JOIN cohort_size cs ON cd.cohort_month = cs.cohort_month
ORDER BY cd.cohort_month, cd.months_since_first;
-- ============================================================
-- Query 3: RFM Customer Segmentation
-- Purpose : Score every customer on Recency, Frequency,
--           Monetary value. Assign segment labels.
--           Powers customer targeting in Power BI dashboard.
-- ============================================================

WITH max_date AS (
    -- Reference date = last order date in dataset
    SELECT MAX(CAST(full_date AS DATE)) AS snapshot_date
    FROM dim_date
    WHERE date_key IN (SELECT DISTINCT date_key FROM fact)
),

customer_metrics AS (
    SELECT
        f.customer_key,
        c.city,
        c.state,

        -- Recency: days since last order
        DATEDIFF('day',
            MAX(CAST(d.full_date AS DATE)),
            (SELECT snapshot_date FROM max_date)
        )                                     AS recency_days,

        -- Frequency: total number of orders
        COUNT(DISTINCT f.order_id)            AS frequency,

        -- Monetary: total spend
        ROUND(SUM(f.total_payment), 2)        AS monetary,

        -- Avg order value
        ROUND(AVG(f.total_payment), 2)        AS avg_order_value,

        -- Avg review score
        ROUND(AVG(f.avg_review_score), 2)     AS avg_review_score,

        -- Last order date
        MAX(CAST(d.full_date AS DATE))        AS last_order_date

    FROM fact f
    JOIN dim_date d  ON f.date_key      = d.date_key
    JOIN dim_cust c  ON f.customer_key  = c.customer_key
    GROUP BY f.customer_key, c.city, c.state
),

rfm_scores AS (
    SELECT
        *,
        -- Score 1-4 using NTILE (4=best)
        NTILE(4) OVER (ORDER BY recency_days DESC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM customer_metrics
),

rfm_segments AS (
    SELECT
        *,
        -- Combined RFM score string e.g. "444"
        CAST(r_score AS VARCHAR) ||
        CAST(f_score AS VARCHAR) ||
        CAST(m_score AS VARCHAR)                    AS rfm_score,

        -- Total score (max 12)
        (r_score + f_score + m_score)               AS total_rfm_score,

        -- Segment label based on combined score
        CASE
            WHEN r_score = 4 AND f_score = 4 AND m_score = 4
                THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3
                THEN 'Loyal Customers'
            WHEN r_score = 4 AND f_score <= 2
                THEN 'Recent Customers'
            WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 3
                THEN 'Potential Loyalists'
            WHEN r_score = 1 AND f_score >= 3
                THEN 'At Risk'
            WHEN r_score = 1 AND f_score = 4 AND m_score = 4
                THEN 'Cannot Lose Them'
            WHEN r_score <= 2 AND f_score <= 2
                THEN 'Hibernating'
            ELSE 'Need Attention'
        END                                         AS segment
    FROM rfm_scores
)

SELECT
    customer_key,
    city,
    state,
    recency_days,
    frequency,
    monetary,
    avg_order_value,
    avg_review_score,
    last_order_date,
    r_score,
    f_score,
    m_score,
    rfm_score,
    total_rfm_score,
    segment
FROM rfm_segments
ORDER BY total_rfm_score DESC, monetary DESC;
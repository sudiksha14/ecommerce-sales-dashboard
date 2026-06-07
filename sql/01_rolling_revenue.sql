-- ============================================================
-- Query 1: Rolling 30-Day Revenue
-- Purpose : Track smoothed revenue trend removing day-to-day
--           noise. Used as a KPI in Power BI rolling avg card.
-- ============================================================

WITH daily_revenue AS (
    SELECT
        d.full_date                          AS order_date,
        d.year,
        d.month,
        d.month_name,
        d.day_of_week,
        COUNT(f.order_id)                    AS order_count,
        ROUND(SUM(f.total_payment), 2)       AS daily_revenue,
        ROUND(AVG(f.total_payment), 2)       AS avg_order_value
    FROM fact f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.order_status = 'delivered'
    GROUP BY d.full_date, d.year, d.month, d.month_name, d.day_of_week
),

rolling AS (
    SELECT
        order_date,
        year,
        month_name,
        day_of_week,
        order_count,
        daily_revenue,
        avg_order_value,

        -- Rolling 30-day revenue (window function)
        ROUND(SUM(daily_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2)                                AS rolling_30d_revenue,

        -- Rolling 7-day revenue
        ROUND(SUM(daily_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2)                                AS rolling_7d_revenue,

        -- Running total revenue (cumulative)
        ROUND(SUM(daily_revenue) OVER (
            ORDER BY order_date
            ROWS UNBOUNDED PRECEDING
        ), 2)                                AS cumulative_revenue,

        -- Day-over-day revenue change %
        ROUND(
            (daily_revenue - LAG(daily_revenue) OVER (ORDER BY order_date))
            / NULLIF(LAG(daily_revenue) OVER (ORDER BY order_date), 0) * 100
        , 2)                                 AS dod_change_pct

    FROM daily_revenue
)

SELECT * FROM rolling
ORDER BY order_date;
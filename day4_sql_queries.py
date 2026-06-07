"""
Project 1: E-Commerce Sales Intelligence Dashboard
Day 4 — Advanced SQL Queries using DuckDB
Author: Sudiksha Gunjkar | Portfolio Project

Queries:
  1. Rolling 30-day revenue
  2. Cohort analysis
  3. RFM segmentation
"""

import duckdb
import pandas as pd
import os

PROCESSED = "data/processed"
SQL_DIR   = "sql"
os.makedirs(SQL_DIR, exist_ok=True)

print("=" * 60)
print("Day 4 — Advanced SQL Queries with DuckDB")
print("=" * 60)

# ── CONNECT & LOAD TABLES ─────────────────────────────────────
con = duckdb.connect()

tables = {
    "fact":     f"{PROCESSED}/fact_orders.csv",
    "dim_date": f"{PROCESSED}/dim_date.csv",
    "dim_cust": f"{PROCESSED}/dim_customer.csv",
    "dim_prod": f"{PROCESSED}/dim_product.csv",
    "dim_sell": f"{PROCESSED}/dim_seller.csv",
    "dim_geo":  f"{PROCESSED}/dim_geography.csv",
}

for name, path in tables.items():
    con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{path}')")
    count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  Loaded {name}: {count:,} rows")

print()

# ════════════════════════════════════════════════════════════
# QUERY 1 — Rolling 30-Day Revenue
# ════════════════════════════════════════════════════════════

Q1 = """
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
"""

print("Running Query 1: Rolling 30-Day Revenue...")
q1_result = con.execute(Q1).df()
q1_result.to_csv(f"{SQL_DIR}/result_01_rolling_revenue.csv", index=False)
print(f"  Rows returned: {len(q1_result):,}")
print(f"  Max rolling 30d revenue: R${q1_result['rolling_30d_revenue'].max():,.2f}")
print(f"  Saved: sql/result_01_rolling_revenue.csv\n")

# Save SQL file
with open(f"{SQL_DIR}/01_rolling_revenue.sql", "w") as f:
    f.write(Q1.strip())
print("  Saved: sql/01_rolling_revenue.sql")
print()

# ════════════════════════════════════════════════════════════
# QUERY 2 — Cohort Analysis
# ════════════════════════════════════════════════════════════

Q2 = """
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
"""

print("Running Query 2: Cohort Analysis...")
q2_result = con.execute(Q2).df()
q2_result.to_csv(f"{SQL_DIR}/result_02_cohort.csv", index=False)
print(f"  Rows returned: {len(q2_result):,}")
# Month 0 retention is always 100% — show month 1 retention
m1 = q2_result[q2_result["months_since_first"] == 1]
if len(m1) > 0:
    avg_m1_retention = m1["retention_rate_pct"].mean()
    print(f"  Avg Month-1 retention rate: {avg_m1_retention:.2f}%")
print(f"  Saved: sql/result_02_cohort.csv\n")

with open(f"{SQL_DIR}/02_cohort.sql", "w") as f:
    f.write(Q2.strip())
print("  Saved: sql/02_cohort.sql")
print()

# ════════════════════════════════════════════════════════════
# QUERY 3 — RFM Segmentation
# ════════════════════════════════════════════════════════════

Q3 = """
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
"""

print("Running Query 3: RFM Segmentation...")
q3_result = con.execute(Q3).df()
q3_result.to_csv(f"{SQL_DIR}/result_03_rfm.csv", index=False)
print(f"  Rows returned: {len(q3_result):,}")
print("\n  RFM Segment Distribution:")
seg_dist = q3_result["segment"].value_counts()
for seg, count in seg_dist.items():
    pct = count / len(q3_result) * 100
    print(f"    {seg:<22} {count:>6,}  ({pct:.1f}%)")
print(f"\n  Saved: sql/result_03_rfm.csv")

with open(f"{SQL_DIR}/03_rfm.sql", "w") as f:
    f.write(Q3.strip())
print("  Saved: sql/03_rfm.sql")

# ── SUMMARY ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Day 4 COMPLETE — SQL files saved to sql/")
print("=" * 60)
print("  sql/01_rolling_revenue.sql  + result CSV")
print("  sql/02_cohort.sql           + result CSV")
print("  sql/03_rfm.sql              + result CSV")
print("\nThese 3 queries map directly to DAX measures in Week 2.")
print("=" * 60)

con.close()

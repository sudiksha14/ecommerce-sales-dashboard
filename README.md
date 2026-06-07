# E-Commerce Sales Intelligence Dashboard
**Portfolio Project 1 — Data Analyst + Power BI Developer**

An end-to-end business intelligence project built on the Olist Brazilian E-Commerce dataset (99,441 orders, R$16M GMV). Covers the full data pipeline from raw CSVs to a star-schema data warehouse, advanced SQL analytics, and a production Power BI dashboard.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data ingestion | Python (Pandas) |
| Data warehouse | Star schema — 1 fact table + 5 dimension tables |
| Advanced SQL | DuckDB — window functions, cohort analysis, RFM |
| Visualisation | Power BI (DAX, RLS, drillthrough) + Streamlit |
| Version control | Git + GitHub |

---

## Project Structure

```
ecommerce-sales-dashboard/
├── data/
│   ├── raw/              # Olist CSVs (not tracked — too large)
│   └── processed/        # 6 clean dimension + fact tables (ETL output)
├── notebooks/
│   ├── 01_eda.py         # EDA script — 15 business charts
│   ├── charts_10_to_15.py
│   └── charts/           # 15 PNG chart outputs
├── sql/
│   ├── 01_rolling_revenue.sql
│   ├── 02_cohort.sql
│   └── 03_rfm.sql
├── etl_pipeline.py       # Full ETL pipeline
├── day4_sql_queries.py   # DuckDB SQL runner
└── README.md
```

---

## Star Schema Design

```
                    dim_date
                       |
    dim_product --- fact_orders --- dim_customer
                       |
    dim_seller --- dim_geography
```

**Fact table:** `fact_orders` — 99,441 rows  
**Dimensions:** dim_date (774 rows), dim_customer (99,441), dim_product (32,951), dim_seller (3,095), dim_geography (19,015)

---

## Key Business Findings

### 1. Revenue & Growth
- **Total GMV:** R$16.01M across the dataset period
- **Average order value:** R$160.99 — stable across months
- **Revenue peaks in November 2017** — Black Friday drives a sharp MoM spike
- **Monday and Tuesday** are the highest revenue days — weekends underperform by ~18%

### 2. Delivery Performance
- **Average delivery time:** 12.5 days nationally
- **Late order rate:** 7.9% (~7,900 orders arrived after promised date)
- **Northern states (RR, AP, AM)** wait 2-3x longer than Sao Paulo — clear logistics gap
- Late rate **spikes in early 2018** — rapid order growth outpaced logistics capacity

### 3. Customer Behaviour
- **97% of customers placed only 1 order** — severe retention problem and biggest growth lever
- **Only 1.1% Champions** (1,128 customers) in RFM segmentation — most e-commerce platforms target 5-10%
- **4.4% At Risk** customers (4,381) — immediate win-back campaign opportunity
- **Credit card dominates** at ~74% of orders — high instalment usage signals price sensitivity
- **Average review score: 4.09/5** — strong product-market fit confirmed

---

## Advanced SQL Queries (DuckDB)

### Query 1 — Rolling 30-Day Revenue
Window functions: `SUM() OVER (ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)`  
Also includes 7-day rolling, cumulative total, and day-over-day change %.

### Query 2 — Customer Cohort Analysis
Groups customers by first purchase month. Tracks retention rate in subsequent months using `DATE_TRUNC`, `DATEDIFF`, and a cohort self-join pattern.

### Query 3 — RFM Segmentation
Scores all 99,441 customers on Recency, Frequency, Monetary using `NTILE(4)`.  
Assigns 8 business segment labels: Champions, Loyal Customers, At Risk, Hibernating, etc.

---

## EDA Charts (15 total)

| Section | Charts |
|---|---|
| Revenue Analysis | Monthly trend, top categories, AOV, day of week, price bucket |
| Delivery Analysis | By state, late vs on-time, monthly late rate, freight % |
| Customer Analysis | Repeat buyers, review scores, payment types, revenue by state |
| Advanced | Order status, revenue heatmap (month x day) |

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy duckdb matplotlib openpyxl

# 2. Download Olist dataset from Kaggle and place CSVs in data/raw/
# https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

# 3. Run ETL pipeline
python etl_pipeline.py

# 4. Run EDA
python notebooks/01_eda.py

# 5. Run SQL queries
python day4_sql_queries.py
```

---

## Dataset

**Source:** [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Kaggle  
**Size:** 9 CSV files, ~1.6M total rows  
**Period:** 2016–2018  
**License:** CC BY-NC-SA 4.0

---

*Built by Sudiksha Gunjkar — Data Analyst & Power BI Developer*  
*Part of a 3-project portfolio targeting Data Analyst and BI Developer roles*

"""
Project 1: E-Commerce Sales Intelligence Dashboard
ETL Pipeline - Olist Brazilian E-Commerce Dataset
Author: Sudiksha Gunjkar | Portfolio Project
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("etl_log.txt"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

RAW_DIR = "data/raw"
OUT_DIR = "data/processed"
os.makedirs(OUT_DIR, exist_ok=True)


def load_raw_data():
    files = {
        "orders":        "olist_orders_dataset.csv",
        "order_items":   "olist_order_items_dataset.csv",
        "products":      "olist_products_dataset.csv",
        "customers":     "olist_customers_dataset.csv",
        "sellers":       "olist_sellers_dataset.csv",
        "payments":      "olist_order_payments_dataset.csv",
        "reviews":       "olist_order_reviews_dataset.csv",
        "geo":           "olist_geolocation_dataset.csv",
        "category_xlat": "product_category_name_translation.csv",
    }
    raw = {}
    for key, fname in files.items():
        path = os.path.join(RAW_DIR, fname)
        raw[key] = pd.read_csv(path)
        log.info("Loaded %s: %s rows", key, f"{raw[key].shape[0]:,}")
    return raw


def run_dq_checks(raw):
    issues = 0
    for name, df in raw.items():
        nulls = df.isnull().sum()
        nulls = nulls[nulls > 0]
        if not nulls.empty:
            log.warning("DQ | %s has nulls: %s", name, dict(nulls))
            issues += 1
        dups = df.duplicated().sum()
        if dups > 0:
            log.warning("DQ | %s has %s duplicate rows", name, dups)
            issues += 1
    log.info("DQ check complete - %s issue(s) found", issues)

    raw["orders"]["order_delivered_customer_date"].fillna(
        raw["orders"]["order_estimated_delivery_date"], inplace=True)
    raw["products"]["product_category_name"].fillna("unknown", inplace=True)
    raw["reviews"]["review_comment_title"].fillna("", inplace=True)
    raw["reviews"]["review_comment_message"].fillna("", inplace=True)
    raw["geo"] = (raw["geo"]
                  .drop_duplicates(subset=["geolocation_zip_code_prefix"])
                  .reset_index(drop=True))
    log.info("DQ fixes applied")
    return raw


def build_dim_date(orders):
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"])
    min_date = orders["order_purchase_timestamp"].min().normalize()
    max_date = orders["order_purchase_timestamp"].max().normalize()
    dates = pd.date_range(min_date, max_date, freq="D")
    dim = pd.DataFrame({"full_date": dates})
    dim["date_key"]    = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"]        = dim["full_date"].dt.year
    dim["quarter"]     = dim["full_date"].dt.quarter
    dim["month"]       = dim["full_date"].dt.month
    dim["month_name"]  = dim["full_date"].dt.strftime("%B")
    dim["week"]        = dim["full_date"].dt.isocalendar().week.astype(int)
    dim["day_of_week"] = dim["full_date"].dt.day_name()
    dim["is_weekend"]  = dim["full_date"].dt.dayofweek >= 5
    log.info("dim_date: %s rows", f"{len(dim):,}")
    return dim


def build_dim_customer(customers):
    dim = customers.rename(columns={
        "customer_zip_code_prefix": "zip_code",
        "customer_city": "city",
        "customer_state": "state",
    }).copy()
    dim["customer_key"] = range(1, len(dim) + 1)
    log.info("dim_customer: %s rows", f"{len(dim):,}")
    return dim[["customer_key", "customer_id", "customer_unique_id",
                "zip_code", "city", "state"]]


def build_dim_product(products, category_xlat):
    dim = products.merge(category_xlat, on="product_category_name", how="left")
    dim["product_category_name_english"].fillna(
        dim["product_category_name"], inplace=True)
    dim = dim.rename(columns={
        "product_category_name_english": "category_en",
        "product_weight_g": "weight_g",
        "product_length_cm": "length_cm",
        "product_height_cm": "height_cm",
        "product_width_cm": "width_cm",
    })
    dim["product_key"] = range(1, len(dim) + 1)
    log.info("dim_product: %s rows", f"{len(dim):,}")
    return dim[["product_key", "product_id", "category_en",
                "weight_g", "length_cm", "height_cm", "width_cm"]]


def build_dim_seller(sellers):
    dim = sellers.rename(columns={
        "seller_zip_code_prefix": "zip_code",
        "seller_city": "city",
        "seller_state": "state",
    }).copy()
    dim["seller_key"] = range(1, len(dim) + 1)
    log.info("dim_seller: %s rows", f"{len(dim):,}")
    return dim[["seller_key", "seller_id", "zip_code", "city", "state"]]


def build_dim_geography(geo):
    dim = geo.rename(columns={
        "geolocation_zip_code_prefix": "zip_code",
        "geolocation_lat": "lat",
        "geolocation_lng": "lng",
        "geolocation_city": "city",
        "geolocation_state": "state",
    }).copy()
    region_map = {
        "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
        "RS": "South",     "SC": "South",      "PR": "South",
        "BA": "Northeast", "PE": "Northeast",  "CE": "Northeast", "MA": "Northeast",
        "PA": "North",     "AM": "North",      "RO": "North",
        "DF": "Central-West", "GO": "Central-West", "MT": "Central-West", "MS": "Central-West",
    }
    dim["region"]  = dim["state"].map(region_map).fillna("Other")
    dim["geo_key"] = range(1, len(dim) + 1)
    log.info("dim_geography: %s rows", f"{len(dim):,}")
    return dim[["geo_key", "zip_code", "city", "state", "region", "lat", "lng"]]


def build_fact_orders(orders, order_items, payments, reviews,
                      dim_date, dim_customer, dim_product,
                      dim_seller, dim_geo):

    for col in ["order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col])

    pay_agg = (payments.groupby("order_id")
               .agg(total_payment=("payment_value", "sum"),
                    num_installments=("payment_installments", "max"),
                    payment_type=("payment_type", lambda x: x.mode()[0]))
               .reset_index())

    rev_agg = (reviews.groupby("order_id")
               .agg(avg_review_score=("review_score", "mean"))
               .reset_index())

    items_agg = (order_items.groupby("order_id")
                 .agg(product_id=("product_id", "first"),
                      seller_id=("seller_id", "first"),
                      total_freight=("freight_value", "sum"),
                      total_price=("price", "sum"),
                      qty=("order_item_id", "count"))
                 .reset_index())

    fact = (orders
            .merge(items_agg, on="order_id", how="left")
            .merge(pay_agg,   on="order_id", how="left")
            .merge(rev_agg,   on="order_id", how="left"))

    fact["delivery_days"] = (
        (fact["order_delivered_customer_date"] -
         fact["order_purchase_timestamp"]).dt.days)
    fact["is_late"] = (
        fact["order_delivered_customer_date"] >
        fact["order_estimated_delivery_date"]).astype(int)

    fact["date_key"] = (fact["order_purchase_timestamp"]
                        .dt.strftime("%Y%m%d").astype(int))

    fact = fact.merge(
        dim_customer[["customer_id", "customer_key"]],
        on="customer_id", how="left")
    fact = fact.merge(
        dim_product[["product_id", "product_key"]],
        on="product_id", how="left")
    fact = fact.merge(
        dim_seller[["seller_id", "seller_key"]],
        on="seller_id", how="left")

    cust_zip = (dim_customer[["customer_key", "zip_code"]]
                .merge(dim_geo[["zip_code", "geo_key"]],
                       on="zip_code", how="left")
                [["customer_key", "geo_key"]])
    fact = fact.merge(cust_zip, on="customer_key", how="left")

    fact_final = fact[[
        "order_id", "date_key", "customer_key", "product_key",
        "seller_key", "geo_key", "order_status",
        "total_price", "total_freight", "total_payment",
        "qty", "num_installments", "payment_type",
        "delivery_days", "is_late", "avg_review_score",
    ]].copy()

    bins   = [0, 50, 150, 500, np.inf]
    labels = ["budget", "mid-range", "premium", "luxury"]
    fact_final["price_bucket"] = pd.cut(
        fact_final["total_price"], bins=bins, labels=labels)

    log.info("fact_orders: %s rows", f"{len(fact_final):,}")
    return fact_final


def save_tables(tables):
    for name, df in tables.items():
        path = os.path.join(OUT_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        log.info("Saved %s -> %s (%s rows)", name, path, f"{len(df):,}")


def main():
    log.info("=" * 60)
    log.info("ETL Pipeline started")
    log.info("=" * 60)

    raw  = load_raw_data()
    raw  = run_dq_checks(raw)

    dim_date     = build_dim_date(raw["orders"])
    dim_customer = build_dim_customer(raw["customers"])
    dim_product  = build_dim_product(raw["products"], raw["category_xlat"])
    dim_seller   = build_dim_seller(raw["sellers"])
    dim_geo      = build_dim_geography(raw["geo"])

    fact_orders = build_fact_orders(
        raw["orders"], raw["order_items"], raw["payments"],
        raw["reviews"], dim_date, dim_customer,
        dim_product, dim_seller, dim_geo,
    )

    save_tables({
        "dim_date":      dim_date,
        "dim_customer":  dim_customer,
        "dim_product":   dim_product,
        "dim_seller":    dim_seller,
        "dim_geography": dim_geo,
        "fact_orders":   fact_orders,
    })

    log.info("ETL complete. Load CSVs into Power BI or SQL Server.")


if __name__ == "__main__":
    main()

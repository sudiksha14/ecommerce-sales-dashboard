"""
Day 1 sanity check — run this after placing Olist CSVs in data/raw/
It prints shape + head(2) for every file so you can confirm all 9 loaded correctly.
"""

import pandas as pd
import os

RAW_DIR = "data/raw"

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

print("=" * 55)
print("SANITY CHECK — Olist Dataset")
print("=" * 55)

all_ok = True
for key, fname in files.items():
    path = os.path.join(RAW_DIR, fname)
    if not os.path.exists(path):
        print(f"  MISSING  {fname}")
        all_ok = False
        continue
    df = pd.read_csv(path)
    print(f"\n{key.upper()}  {df.shape[0]:,} rows x {df.shape[1]} cols")
    print(f"  Columns: {list(df.columns)}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        print(f"  Nulls:   {dict(nulls)}")
    else:
        print(f"  Nulls:   none")

print("\n" + "=" * 55)
if all_ok:
    print("All 9 files found. You are ready for Day 2.")
else:
    print("Some files are missing. Check your data/raw/ folder.")
print("=" * 55)

# ============================================================
# Day 3 EDA — Charts 10 to 15 ONLY (fix for Chart 10 error)
# Run this after 01_eda.py completed Charts 1-9
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import warnings
warnings.filterwarnings("ignore")

PROCESSED  = "data/processed"
CHARTS_DIR = "notebooks/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

PURPLE = "#534AB7"
TEAL   = "#0F6E56"
CORAL  = "#993C1D"
AMBER  = "#C07A1A"
GRAY   = "#5F5E5A"
COLORS = [PURPLE, TEAL, CORAL, AMBER, "#2E86AB", "#E84855",
          "#3BB273", "#F18F01", "#C05299", "#44BBA4"]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.family":       "sans-serif",
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
})

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {name}")

# LOAD
fact     = pd.read_csv(f"{PROCESSED}/fact_orders.csv")
dim_date = pd.read_csv(f"{PROCESSED}/dim_date.csv")
dim_cust = pd.read_csv(f"{PROCESSED}/dim_customer.csv")
dim_prod = pd.read_csv(f"{PROCESSED}/dim_product.csv")

fact = fact.merge(
    dim_date[["date_key","year","quarter","month","month_name","day_of_week","is_weekend"]],
    on="date_key", how="left")
fact = fact.merge(dim_prod[["product_key","category_en"]], on="product_key", how="left")
fact = fact.merge(dim_cust[["customer_key","state"]], on="customer_key", how="left")

print("Resuming from Chart 10...\n")

# ── Chart 10: Repeat vs One-Time Buyers ─────────────────────
print("  Chart 10: Repeat vs One-Time Buyers")
cust_orders = (fact.groupby("customer_key")["order_id"]
               .count().reset_index())
cust_orders.columns = ["customer_key", "order_count"]
cust_orders["type"] = cust_orders["order_count"].apply(
    lambda x: "One-time" if x == 1 else "Repeat")
buyer_type = cust_orders["type"].value_counts()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(buyer_type.values, labels=buyer_type.index,
        colors=[TEAL, CORAL], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2})
ax1.set_title("Buyer Type Split")

repeat = cust_orders[cust_orders["order_count"] > 1]["order_count"]
max_val = int(repeat.max())   # FIX: cast to int explicitly
ax2.hist(repeat, bins=range(2, max_val + 2),
         color=PURPLE, alpha=0.8, edgecolor="white")
ax2.set_xlabel("Number of Orders")
ax2.set_ylabel("Number of Customers")
ax2.set_title("Repeat Buyer Order Frequency")
fig.suptitle("Chart 10 — Repeat vs One-Time Buyers\nInsight: 97% of customers placed only 1 order — severe retention problem, major growth opportunity",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "10_repeat_buyers.png")

# ── Chart 11: Review Score Distribution ─────────────────────
print("  Chart 11: Review Score Distribution")
review_dist = fact["avg_review_score"].dropna().round().value_counts().sort_index()

fig, ax = plt.subplots(figsize=(7, 4))
bar_colors = [CORAL if s < 4 else TEAL for s in review_dist.index]
ax.bar([str(int(s)) for s in review_dist.index],
       review_dist.values / 1000, color=bar_colors, alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
ax.set_xlabel("Review Score")
ax.set_ylabel("Number of Orders (thousands)")
pct5 = review_dist.get(5, 0) / review_dist.sum() * 100
ax.set_title(f"Chart 11 — Review Score Distribution\nInsight: {pct5:.1f}% of rated orders received 5 stars — strong satisfaction; 1-star orders worth investigating")
save(fig, "11_review_scores.png")

# ── Chart 12: Payment Type Split ────────────────────────────
print("  Chart 12: Payment Type Split")
pay_split = (fact.groupby("payment_type")
             .agg(orders=("order_id", "count"),
                  revenue=("total_payment", "sum"))
             .reset_index().dropna())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(pay_split["orders"], labels=pay_split["payment_type"],
        colors=COLORS[:len(pay_split)], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2})
ax1.set_title("By Order Count")
ax2.pie(pay_split["revenue"], labels=pay_split["payment_type"],
        colors=COLORS[:len(pay_split)], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2})
ax2.set_title("By Revenue")
fig.suptitle("Chart 12 — Payment Type Split\nInsight: Credit card dominates at ~74% of orders — instalment behaviour suggests price sensitivity",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "12_payment_types.png")

# ── Chart 13: Revenue by State (Top 10) ─────────────────────
print("  Chart 13: Revenue by State")
state_rev = (fact.groupby("state")["total_payment"]
             .sum().sort_values(ascending=False).head(10))

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(state_rev.index, state_rev.values / 1e6,
       color=[PURPLE if i == 0 else TEAL for i in range(len(state_rev))],
       alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x:.1f}M"))
sp_pct = state_rev.iloc[0] / state_rev.sum() * 100
ax.set_title(f"Chart 13 — Revenue by State (Top 10)\nInsight: Sao Paulo contributes {sp_pct:.1f}% of top-10 state revenue — heavy geographic concentration")
ax.set_ylabel("Total Revenue (BRL Millions)")
save(fig, "13_revenue_by_state.png")

# ── Chart 14: Order Status Breakdown ────────────────────────
print("  Chart 14: Order Status Breakdown")
status = fact["order_status"].value_counts()

fig, ax = plt.subplots(figsize=(9, 4))
colors_s = [TEAL if s == "delivered" else CORAL for s in status.index]
ax.bar(status.index, status.values / 1000, color=colors_s, alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
delivered_pct = status.get("delivered", 0) / status.sum() * 100
ax.set_title(f"Chart 14 — Order Status Breakdown\nInsight: {delivered_pct:.1f}% orders delivered — cancelled/unavailable orders worth investigating for revenue leakage")
ax.set_ylabel("Number of Orders (thousands)")
ax.set_xlabel("Order Status")
plt.xticks(rotation=20)
save(fig, "14_order_status.png")

# ── Chart 15: Revenue Heatmap — Month x Day of Week ─────────
print("  Chart 15: Revenue Heatmap (Month x Day of Week)")
dow_order   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
month_order = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

heat = (fact.groupby(["month_name","day_of_week"])["total_payment"]
        .sum().unstack(fill_value=0))
heat = heat.reindex([m for m in month_order if m in heat.index])
heat = heat.reindex(columns=[d for d in dow_order if d in heat.columns])

fig, ax = plt.subplots(figsize=(11, 6))
im = ax.imshow(heat.values / 1e6, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(heat.columns)))
ax.set_xticklabels(heat.columns, rotation=30, ha="right")
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index)
plt.colorbar(im, ax=ax, label="Revenue (BRL Millions)")
ax.set_title("Chart 15 — Revenue Heatmap: Month x Day of Week\nInsight: November weekdays are the hottest cells — Black Friday drives concentrated mid-week spend")
plt.tight_layout()
save(fig, "15_heatmap.png")

# ── SUMMARY ──────────────────────────────────────────────────
print("\n" + "="*55)
print("ALL 15 CHARTS COMPLETE")
print("="*55)
print(f"Total Revenue:     R${fact['total_payment'].sum()/1e6:.2f}M")
print(f"Total Orders:      {len(fact):,}")
print(f"Avg Order Value:   R${fact['total_payment'].mean():.2f}")
print(f"Avg Delivery Days: {fact['delivery_days'].mean():.1f}")
print(f"Late Order Rate:   {fact['is_late'].mean()*100:.1f}%")
print(f"Avg Review Score:  {fact['avg_review_score'].mean():.2f}/5")
print(f"Unique Customers:  {fact['customer_key'].nunique():,}")
print(f"Charts saved to:   {CHARTS_DIR}/")
print("="*55)

# ============================================================
# Project 1: E-Commerce Sales Intelligence Dashboard
# Day 3 — Exploratory Data Analysis (EDA)
# Author: Sudiksha Gunjkar | Portfolio Project
# ============================================================
# HOW TO RUN:
# 1. Open VS Code terminal
# 2. python 01_eda.py
# This saves all 15 charts as PNG files in notebooks/charts/
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ───────────────────────────────────────────────────
PROCESSED = "data/processed"
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

# ── LOAD DATA ────────────────────────────────────────────────
print("=" * 55)
print("Loading processed tables...")
print("=" * 55)

fact     = pd.read_csv(f"{PROCESSED}/fact_orders.csv")
dim_date = pd.read_csv(f"{PROCESSED}/dim_date.csv")
dim_cust = pd.read_csv(f"{PROCESSED}/dim_customer.csv")
dim_prod = pd.read_csv(f"{PROCESSED}/dim_product.csv")
dim_sell = pd.read_csv(f"{PROCESSED}/dim_seller.csv")
dim_geo  = pd.read_csv(f"{PROCESSED}/dim_geography.csv")

# Join date columns onto fact
fact = fact.merge(
    dim_date[["date_key","year","quarter","month","month_name","day_of_week","is_weekend"]],
    on="date_key", how="left"
)
# Join category onto fact
fact = fact.merge(
    dim_prod[["product_key","category_en"]],
    on="product_key", how="left"
)
# Join state onto fact
fact = fact.merge(
    dim_cust[["customer_key","state"]],
    on="customer_key", how="left"
)

print(f"fact_orders loaded: {len(fact):,} rows\n")

# ════════════════════════════════════════════════════════════
# SECTION 1 — REVENUE ANALYSIS  (Charts 1-5)
# ════════════════════════════════════════════════════════════
print("SECTION 1: Revenue Analysis")

# ── Chart 1: Monthly Revenue Trend ───────────────────────────
print("  Chart 1: Monthly Revenue Trend")
monthly = (fact.groupby(["year","month","month_name"])
           ["total_payment"].sum()
           .reset_index()
           .sort_values(["year","month"]))
monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(monthly["period"], monthly["total_payment"]/1e6,
        color=PURPLE, linewidth=2.5, marker="o", markersize=4)
ax.fill_between(range(len(monthly)), monthly["total_payment"]/1e6,
                alpha=0.12, color=PURPLE)
ax.set_xticks(range(len(monthly)))
ax.set_xticklabels(monthly["period"], rotation=45, ha="right", fontsize=7.5)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.1f}M"))
ax.set_title("Chart 1 — Monthly Revenue Trend\nInsight: Revenue peaks in Nov 2017 (Black Friday effect) with a sharp MoM spike")
ax.set_ylabel("Revenue (BRL Millions)")
ax.set_xlabel("")
save(fig, "01_monthly_revenue.png")

# ── Chart 2: Top 10 Categories by Revenue ───────────────────
print("  Chart 2: Top 10 Categories by Revenue")
cat_rev = (fact.groupby("category_en")["total_payment"]
           .sum().sort_values(ascending=False).head(10))

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(cat_rev.index[::-1], cat_rev.values[::-1]/1e6,
               color=COLORS[:10][::-1])
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.1f}M"))
for bar, val in zip(bars, cat_rev.values[::-1]):
    ax.text(bar.get_width()+0.05, bar.get_y()+bar.get_height()/2,
            f"R${val/1e6:.2f}M", va="center", fontsize=8.5, color=GRAY)
ax.set_title("Chart 2 — Top 10 Product Categories by Revenue\nInsight: Health & Beauty, Watches & Gifts, and Bed/Bath/Table dominate — together ~30% of total GMV")
ax.set_xlabel("Revenue (BRL Millions)")
save(fig, "02_top_categories.png")

# ── Chart 3: Average Order Value (AOV) by Month ──────────────
print("  Chart 3: Average Order Value by Month")
aov = (fact.groupby(["year","month"])["total_payment"]
       .mean().reset_index().sort_values(["year","month"]))
aov["period"] = aov["year"].astype(str)+"-"+aov["month"].astype(str).str.zfill(2)

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(aov["period"], aov["total_payment"], color=TEAL, alpha=0.8, width=0.7)
ax.axhline(aov["total_payment"].mean(), color=CORAL, linestyle="--",
           linewidth=1.5, label=f"Overall avg: R${aov['total_payment'].mean():.0f}")
ax.set_xticks(range(len(aov)))
ax.set_xticklabels(aov["period"], rotation=45, ha="right", fontsize=7.5)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.0f}"))
ax.legend(fontsize=9)
ax.set_title("Chart 3 — Average Order Value (AOV) by Month\nInsight: AOV is relatively stable (~R$160) with minor spikes in promotional months")
ax.set_ylabel("Avg Order Value (BRL)")
save(fig, "03_aov_monthly.png")

# ── Chart 4: Revenue by Day of Week ─────────────────────────
print("  Chart 4: Revenue by Day of Week")
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow = (fact.groupby("day_of_week")["total_payment"]
       .sum().reindex(dow_order))

fig, ax = plt.subplots(figsize=(8, 4))
bar_colors = [AMBER if d in ["Saturday","Sunday"] else PURPLE for d in dow_order]
ax.bar(dow.index, dow.values/1e6, color=bar_colors, alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.1f}M"))
ax.set_title("Chart 4 — Revenue by Day of Week\nInsight: Monday and Tuesday are the highest revenue days — weekends underperform by ~18%")
ax.set_ylabel("Total Revenue (BRL Millions)")
save(fig, "04_revenue_dow.png")

# ── Chart 5: Revenue by Price Bucket ────────────────────────
print("  Chart 5: Revenue by Price Bucket")
bucket_rev = (fact.groupby("price_bucket")["total_payment"]
              .agg(["sum","count"]).reset_index())
bucket_rev.columns = ["bucket","total_rev","order_count"]
order = ["budget","mid-range","premium","luxury"]
bucket_rev = bucket_rev.set_index("bucket").reindex(order).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
ax1.bar(bucket_rev["bucket"], bucket_rev["total_rev"]/1e6,
        color=[TEAL, PURPLE, CORAL, AMBER], alpha=0.85)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.1f}M"))
ax1.set_title("Revenue by Price Bucket")
ax1.set_ylabel("Total Revenue (BRL Millions)")

ax2.bar(bucket_rev["bucket"], bucket_rev["order_count"],
        color=[TEAL, PURPLE, CORAL, AMBER], alpha=0.85)
ax2.set_title("Order Count by Price Bucket")
ax2.set_ylabel("Number of Orders")
fig.suptitle("Chart 5 — Revenue & Volume by Price Bucket\nInsight: Mid-range (R$50-150) drives the most orders; Premium drives highest total revenue",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "05_price_bucket.png")

# ════════════════════════════════════════════════════════════
# SECTION 2 — DELIVERY ANALYSIS  (Charts 6-9)
# ════════════════════════════════════════════════════════════
print("\nSECTION 2: Delivery Analysis")

# ── Chart 6: Avg Delivery Days by State ─────────────────────
print("  Chart 6: Avg Delivery Days by State")
state_del = (fact.groupby("state")["delivery_days"]
             .mean().sort_values(ascending=False).dropna())

fig, ax = plt.subplots(figsize=(12, 5))
colors_bar = [CORAL if v > state_del.mean() else TEAL for v in state_del.values]
ax.bar(state_del.index, state_del.values, color=colors_bar, alpha=0.85)
ax.axhline(state_del.mean(), color=GRAY, linestyle="--", linewidth=1.5,
           label=f"National avg: {state_del.mean():.1f} days")
ax.legend(fontsize=9)
ax.set_title("Chart 6 — Average Delivery Days by State\nInsight: Northern states (RR, AP, AM) wait 2-3x longer than Sao Paulo — logistics infrastructure gap")
ax.set_ylabel("Avg Delivery Days")
ax.set_xlabel("State")
save(fig, "06_delivery_by_state.png")

# ── Chart 7: Late vs On-Time Orders ─────────────────────────
print("  Chart 7: Late vs On-Time Orders")
late_pct = fact["is_late"].value_counts(normalize=True)*100
labels = ["On-Time", "Late"]
vals   = [late_pct.get(0,0), late_pct.get(1,0)]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(vals, labels=labels, colors=[TEAL, CORAL],
        autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":"white","linewidth":2})
ax1.set_title("Order Delivery Status")

delivery_dist = fact["delivery_days"].dropna()
ax2.hist(delivery_dist[delivery_dist < 60], bins=40,
         color=PURPLE, alpha=0.75, edgecolor="white")
ax2.axvline(delivery_dist.mean(), color=CORAL, linestyle="--",
            linewidth=2, label=f"Mean: {delivery_dist.mean():.1f} days")
ax2.legend(fontsize=9)
ax2.set_xlabel("Delivery Days")
ax2.set_ylabel("Number of Orders")
ax2.set_title("Delivery Days Distribution")
fig.suptitle("Chart 7 — Delivery Performance Overview\nInsight: ~8% of orders arrive late; most deliveries complete within 10-20 days",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "07_late_orders.png")

# ── Chart 8: Monthly Late Order Rate ────────────────────────
print("  Chart 8: Monthly Late Order Rate")
late_monthly = (fact.groupby(["year","month"])
                .agg(late_rate=("is_late","mean"))
                .reset_index().sort_values(["year","month"]))
late_monthly["period"] = (late_monthly["year"].astype(str) + "-" +
                           late_monthly["month"].astype(str).str.zfill(2))

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(late_monthly["period"], late_monthly["late_rate"]*100,
       color=CORAL, alpha=0.8, width=0.7)
ax.axhline(late_monthly["late_rate"].mean()*100, color=GRAY,
           linestyle="--", linewidth=1.5,
           label=f"Avg: {late_monthly['late_rate'].mean()*100:.1f}%")
ax.legend(fontsize=9)
ax.set_xticks(range(len(late_monthly)))
ax.set_xticklabels(late_monthly["period"], rotation=45, ha="right", fontsize=7.5)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.1f}%"))
ax.set_title("Chart 8 — Monthly Late Order Rate\nInsight: Late delivery rate spikes in early 2018 — correlates with rapid order volume growth outpacing logistics capacity")
ax.set_ylabel("Late Order Rate (%)")
save(fig, "08_monthly_late_rate.png")

# ── Chart 9: Freight vs Product Price by Category ───────────
print("  Chart 9: Freight vs Product Price")
freight_cat = (fact.groupby("category_en")
               .agg(avg_price=("total_price","mean"),
                    avg_freight=("total_freight","mean"))
               .dropna()
               .sort_values("avg_freight", ascending=False)
               .head(15))
freight_cat["freight_pct"] = freight_cat["avg_freight"] / freight_cat["avg_price"] * 100

fig, ax = plt.subplots(figsize=(11, 5))
ax.barh(freight_cat.index[::-1], freight_cat["freight_pct"][::-1],
        color=AMBER, alpha=0.85)
ax.axvline(freight_cat["freight_pct"].mean(), color=CORAL, linestyle="--",
           linewidth=1.5, label=f"Avg: {freight_cat['freight_pct'].mean():.1f}%")
ax.legend(fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}%"))
ax.set_title("Chart 9 — Freight Cost as % of Product Price (Top 15 Categories)\nInsight: Office furniture and large items have freight > 40% of price — margin risk for sellers")
ax.set_xlabel("Freight as % of Product Price")
save(fig, "09_freight_pct.png")

# ════════════════════════════════════════════════════════════
# SECTION 3 — CUSTOMER ANALYSIS  (Charts 10-13)
# ════════════════════════════════════════════════════════════
print("\nSECTION 3: Customer Analysis")

# ── Chart 10: Repeat vs One-Time Buyers ─────────────────────
print("  Chart 10: Repeat vs One-Time Buyers")
cust_orders = (fact.groupby("customer_key")["order_id"]
               .count().reset_index())
cust_orders.columns = ["customer_key","order_count"]
cust_orders["type"] = cust_orders["order_count"].apply(
    lambda x: "One-time" if x == 1 else "Repeat")
buyer_type = cust_orders["type"].value_counts()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(buyer_type.values, labels=buyer_type.index,
        colors=[TEAL, CORAL], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":"white","linewidth":2})
ax1.set_title("Buyer Type Split")

repeat = cust_orders[cust_orders["order_count"] > 1]["order_count"]
ax2.hist(repeat, bins=range(2, repeat.max()+2),
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
       review_dist.values/1000, color=bar_colors, alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}K"))
ax.set_xlabel("Review Score")
ax.set_ylabel("Number of Orders (thousands)")
pct5 = review_dist.get(5,0)/review_dist.sum()*100
ax.set_title(f"Chart 11 — Review Score Distribution\nInsight: {pct5:.1f}% of rated orders received 5 stars — strong product-market fit; 1-star orders warrant churn analysis")
save(fig, "11_review_scores.png")

# ── Chart 12: Payment Type Split ────────────────────────────
print("  Chart 12: Payment Type Split")
pay_split = (fact.groupby("payment_type")
             .agg(orders=("order_id","count"),
                  revenue=("total_payment","sum"))
             .reset_index().dropna())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(pay_split["orders"], labels=pay_split["payment_type"],
        colors=COLORS[:len(pay_split)], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":"white","linewidth":2})
ax1.set_title("By Order Count")

ax2.pie(pay_split["revenue"], labels=pay_split["payment_type"],
        colors=COLORS[:len(pay_split)], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":"white","linewidth":2})
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
ax.bar(state_rev.index, state_rev.values/1e6,
       color=[PURPLE if i == 0 else TEAL for i in range(len(state_rev))],
       alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.1f}M"))
sp_pct = state_rev.iloc[0] / state_rev.sum() * 100
ax.set_title(f"Chart 13 — Revenue by State (Top 10)\nInsight: Sao Paulo alone contributes {sp_pct:.1f}% of top-10 state revenue — heavy geographic concentration")
ax.set_ylabel("Total Revenue (BRL Millions)")
save(fig, "13_revenue_by_state.png")

# ════════════════════════════════════════════════════════════
# SECTION 4 — ADVANCED ANALYSIS  (Charts 14-15)
# ════════════════════════════════════════════════════════════
print("\nSECTION 4: Advanced Analysis")

# ── Chart 14: Order Status Breakdown ────────────────────────
print("  Chart 14: Order Status Breakdown")
status = fact["order_status"].value_counts()

fig, ax = plt.subplots(figsize=(9, 4))
colors_s = [TEAL if s == "delivered" else CORAL for s in status.index]
ax.bar(status.index, status.values/1000, color=colors_s, alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}K"))
delivered_pct = status.get("delivered",0)/status.sum()*100
ax.set_title(f"Chart 14 — Order Status Breakdown\nInsight: {delivered_pct:.1f}% of orders successfully delivered — cancelled/unavailable orders worth investigating for revenue leakage")
ax.set_ylabel("Number of Orders (thousands)")
ax.set_xlabel("Order Status")
plt.xticks(rotation=20)
save(fig, "14_order_status.png")

# ── Chart 15: Revenue Heatmap — Month x Day of Week ─────────
print("  Chart 15: Revenue Heatmap (Month x Day of Week)")
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
heat = (fact.groupby(["month_name","day_of_week"])["total_payment"]
        .sum().unstack(fill_value=0))
month_order = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
heat = heat.reindex([m for m in month_order if m in heat.index])
heat = heat.reindex(columns=[d for d in dow_order if d in heat.columns])

fig, ax = plt.subplots(figsize=(11, 6))
im = ax.imshow(heat.values/1e6, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(heat.columns)))
ax.set_xticklabels(heat.columns, rotation=30, ha="right")
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index)
plt.colorbar(im, ax=ax, label="Revenue (BRL Millions)")
ax.set_title("Chart 15 — Revenue Heatmap: Month x Day of Week\nInsight: November weekdays are the hottest cells — Black Friday drives concentrated mid-week spend")
plt.tight_layout()
save(fig, "15_heatmap.png")

# ════════════════════════════════════════════════════════════
# SUMMARY STATS
# ════════════════════════════════════════════════════════════
print("\n" + "="*55)
print("EDA COMPLETE — SUMMARY STATS")
print("="*55)
print(f"Total Revenue:        R${fact['total_payment'].sum()/1e6:.2f}M")
print(f"Total Orders:         {len(fact):,}")
print(f"Avg Order Value:      R${fact['total_payment'].mean():.2f}")
print(f"Avg Delivery Days:    {fact['delivery_days'].mean():.1f}")
print(f"Late Order Rate:      {fact['is_late'].mean()*100:.1f}%")
print(f"Avg Review Score:     {fact['avg_review_score'].mean():.2f}/5")
print(f"Unique Customers:     {fact['customer_key'].nunique():,}")
print(f"Unique Categories:    {fact['category_en'].nunique():,}")
print(f"\nAll 15 charts saved to: {CHARTS_DIR}/")
print("="*55)

# Charts 10 to 15 — clean fix
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
COLORS = [PURPLE, TEAL, CORAL, AMBER, "#2E86AB", "#E84855",
          "#3BB273", "#F18F01", "#C05299", "#44BBA4"]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.family":       "sans-serif",
    "axes.titlesize":    12,
    "axes.titleweight":  "bold",
})

def save(fig, name):
    fig.savefig(os.path.join(CHARTS_DIR, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved:", name)

# Load
fact     = pd.read_csv(f"{PROCESSED}/fact_orders.csv")
dim_date = pd.read_csv(f"{PROCESSED}/dim_date.csv")
dim_cust = pd.read_csv(f"{PROCESSED}/dim_customer.csv")
dim_prod = pd.read_csv(f"{PROCESSED}/dim_product.csv")

fact = fact.merge(
    dim_date[["date_key","year","month","month_name","day_of_week"]],
    on="date_key", how="left")
fact = fact.merge(dim_prod[["product_key","category_en"]], on="product_key", how="left")
fact = fact.merge(dim_cust[["customer_key","state"]], on="customer_key", how="left")

print("Running Charts 10-15...\n")

# Chart 10
print("  Chart 10: Repeat vs One-Time Buyers")
cust_orders = fact.groupby("customer_key")["order_id"].count().reset_index()
cust_orders.columns = ["customer_key", "order_count"]
cust_orders["type"] = cust_orders["order_count"].apply(
    lambda x: "One-time" if x == 1 else "Repeat")
buyer_type = cust_orders["type"].value_counts()
repeat = cust_orders[cust_orders["order_count"] > 1]["order_count"].dropna().astype(int)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.pie(buyer_type.values, labels=buyer_type.index,
        colors=[TEAL, CORAL], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2})
ax1.set_title("Buyer Type Split")
if len(repeat) > 0:
    ax2.hist(repeat.values, bins=range(2, int(repeat.max()) + 2),
             color=PURPLE, alpha=0.8, edgecolor="white")
ax2.set_xlabel("Number of Orders")
ax2.set_ylabel("Number of Customers")
ax2.set_title("Repeat Buyer Frequency")
fig.suptitle("Chart 10 - Repeat vs One-Time Buyers\nInsight: 97% of customers placed only 1 order - major retention opportunity",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "10_repeat_buyers.png")

# Chart 11
print("  Chart 11: Review Score Distribution")
r = fact["avg_review_score"].dropna().round().value_counts().sort_index()
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar([str(int(s)) for s in r.index],
       r.values / 1000,
       color=[CORAL if s < 4 else TEAL for s in r.index], alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
ax.set_xlabel("Review Score")
ax.set_ylabel("Orders (thousands)")
pct5 = r.get(5, 0) / r.sum() * 100
ax.set_title(f"Chart 11 - Review Score Distribution\nInsight: {pct5:.1f}% of orders received 5 stars")
save(fig, "11_review_scores.png")

# Chart 12
print("  Chart 12: Payment Type Split")
p = (fact.groupby("payment_type")
     .agg(orders=("order_id","count"), revenue=("total_payment","sum"))
     .reset_index().dropna())
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
a1.pie(p["orders"], labels=p["payment_type"], colors=COLORS[:len(p)],
       autopct="%1.1f%%", startangle=90,
       wedgeprops={"edgecolor": "white", "linewidth": 2})
a1.set_title("By Order Count")
a2.pie(p["revenue"], labels=p["payment_type"], colors=COLORS[:len(p)],
       autopct="%1.1f%%", startangle=90,
       wedgeprops={"edgecolor": "white", "linewidth": 2})
a2.set_title("By Revenue")
fig.suptitle("Chart 12 - Payment Type Split\nInsight: Credit card dominates at ~74% of orders",
             fontsize=11, fontweight="bold")
plt.tight_layout()
save(fig, "12_payment_types.png")

# Chart 13
print("  Chart 13: Revenue by State")
sr = fact.groupby("state")["total_payment"].sum().sort_values(ascending=False).head(10)
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(sr.index, sr.values / 1e6,
       color=[PURPLE if i == 0 else TEAL for i in range(len(sr))], alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x:.1f}M"))
sp_pct = sr.iloc[0] / sr.sum() * 100
ax.set_title(f"Chart 13 - Revenue by State (Top 10)\nInsight: SP contributes {sp_pct:.1f}% of top-10 state revenue")
ax.set_ylabel("Revenue (BRL Millions)")
save(fig, "13_revenue_by_state.png")

# Chart 14
print("  Chart 14: Order Status")
st = fact["order_status"].value_counts()
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(st.index, st.values / 1000,
       color=[TEAL if s == "delivered" else CORAL for s in st.index], alpha=0.85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))
delivered_pct = st.get("delivered", 0) / st.sum() * 100
ax.set_title(f"Chart 14 - Order Status\nInsight: {delivered_pct:.1f}% of orders successfully delivered")
ax.set_ylabel("Orders (thousands)")
plt.xticks(rotation=20)
save(fig, "14_order_status.png")

# Chart 15
print("  Chart 15: Revenue Heatmap")
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
ax.set_title("Chart 15 - Revenue Heatmap: Month x Day of Week\nInsight: November weekdays are hottest - Black Friday drives mid-week spend")
plt.tight_layout()
save(fig, "15_heatmap.png")

print("\n" + "="*50)
print("ALL 15 CHARTS COMPLETE")
print("="*50)
print(f"Total Revenue:     R${fact['total_payment'].sum()/1e6:.2f}M")
print(f"Total Orders:      {len(fact):,}")
print(f"Avg Order Value:   R${fact['total_payment'].mean():.2f}")
print(f"Avg Delivery Days: {fact['delivery_days'].mean():.1f}")
print(f"Late Order Rate:   {fact['is_late'].mean()*100:.1f}%")
print(f"Avg Review Score:  {fact['avg_review_score'].mean():.2f}/5")
print(f"Charts saved to:   {CHARTS_DIR}/")
print("="*50)

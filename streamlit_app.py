"""
Project 1: E-Commerce Sales Intelligence Dashboard
Streamlit App — Live Portfolio Version
Author: Sudiksha Gunjkar
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F8F7F4; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        border-top: 4px solid;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-label { font-size: 12px; color: #7A7975; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 26px; font-weight: 600; margin-top: 4px; }
    .metric-sub   { font-size: 12px; color: #7A7975; margin-top: 2px; }
    .section-header { font-size: 13px; font-weight: 600; color: #5F5E5A; text-transform: uppercase;
                      letter-spacing: 0.06em; margin: 24px 0 12px; border-bottom: 1px solid #E8E6E0; padding-bottom: 6px; }
    div[data-testid="stMetric"] { background: white; border-radius: 10px; padding: 12px 16px; }
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    PROCESSED = "data/processed"
    SQL_DIR   = "sql"

    fact     = pd.read_csv(f"{PROCESSED}/fact_orders.csv")
    dim_date = pd.read_csv(f"{PROCESSED}/dim_date.csv")
    dim_cust = pd.read_csv(f"{PROCESSED}/dim_customer.csv")
    dim_prod = pd.read_csv(f"{PROCESSED}/dim_product.csv")
    dim_geo  = pd.read_csv(f"{PROCESSED}/dim_geography.csv")
    rfm      = pd.read_csv(f"{SQL_DIR}/result_03_rfm.csv")

    fact = fact.merge(
        dim_date[["date_key","year","month","month_name","day_of_week","quarter"]],
        on="date_key", how="left")
    fact = fact.merge(dim_prod[["product_key","category_en"]], on="product_key", how="left")
    fact = fact.merge(dim_cust[["customer_key","state","city"]], on="customer_key", how="left")

    return fact, dim_date, dim_cust, dim_prod, dim_geo, rfm

fact, dim_date, dim_cust, dim_prod, dim_geo, rfm = load_data()

# ── COLOR PALETTE ─────────────────────────────────────────────
PURPLE = "#534AB7"
TEAL   = "#0F6E56"
CORAL  = "#993C1D"
AMBER  = "#854F0B"
GREEN  = "#3B6D11"
COLORS = [PURPLE, TEAL, CORAL, AMBER, GREEN,
          "#2E86AB", "#E84855", "#3BB273", "#F18F01"]

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Dashboard Filters")
    st.markdown("---")

    years = ["All"] + sorted(fact["year"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", years)

    categories = ["All"] + sorted(fact["category_en"].dropna().unique().tolist())
    selected_cat = st.selectbox("Category", categories)

    states = ["All"] + sorted(fact["state"].dropna().unique().tolist())
    selected_state = st.selectbox("State", states)

    st.markdown("---")
    st.markdown("### 📄 Pages")
    page = st.radio("", ["Revenue Overview", "Delivery & Operations", "Customer Intelligence"],
                    label_visibility="collapsed")

    st.markdown("---")
    st.caption("Built by Sudiksha Gunjkar")
    st.caption("Stack: Python · Pandas · DuckDB · Plotly · Streamlit")

# ── FILTER DATA ───────────────────────────────────────────────
df = fact.copy()
if selected_year != "All":
    df = df[df["year"] == int(selected_year)]
if selected_cat != "All":
    df = df[df["category_en"] == selected_cat]
if selected_state != "All":
    df = df[df["state"] == selected_state]

# ════════════════════════════════════════════════════════════
# PAGE 1 — REVENUE OVERVIEW
# ════════════════════════════════════════════════════════════
if page == "Revenue Overview":
    st.title("Revenue Overview")
    st.caption(f"Showing: {'All years' if selected_year == 'All' else selected_year}  |  "
               f"{'All categories' if selected_cat == 'All' else selected_cat}  |  "
               f"{'All states' if selected_state == 'All' else selected_state}")

    # KPI ROW
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Revenue", f"R${df['total_payment'].sum()/1e6:.2f}M")
    with c2:
        st.metric("Total Orders", f"{len(df):,}")
    with c3:
        st.metric("Avg Order Value", f"R${df['total_payment'].mean():.2f}")
    with c4:
        st.metric("Avg Review Score", f"{df['avg_review_score'].mean():.2f} / 5")
    with c5:
        late_rate = df['is_late'].mean() * 100
        st.metric("Late Order Rate", f"{late_rate:.1f}%",
                  delta=f"{'Above' if late_rate > 7.9 else 'Below'} avg",
                  delta_color="inverse")

    st.markdown('<div class="section-header">Monthly Revenue Trend</div>', unsafe_allow_html=True)
    monthly = (df.groupby(["year","month","month_name"])["total_payment"]
               .sum().reset_index().sort_values(["year","month"]))
    monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    fig1 = px.line(monthly, x="period", y="total_payment",
                   labels={"total_payment": "Revenue (BRL)", "period": "Month"},
                   color_discrete_sequence=[PURPLE])
    fig1.update_traces(line_width=2.5, mode="lines+markers", marker_size=5)
    fig1.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                       yaxis_tickformat=",.0f", height=320,
                       margin=dict(l=20,r=20,t=20,b=40),
                       xaxis=dict(tickangle=-45, tickfont_size=10))
    fig1.update_yaxes(gridcolor="#F0EEE8")
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Top 10 Categories by Revenue</div>', unsafe_allow_html=True)
        cat_rev = (df.groupby("category_en")["total_payment"]
                   .sum().sort_values(ascending=True).tail(10).reset_index())
        fig2 = px.bar(cat_rev, x="total_payment", y="category_en", orientation="h",
                      color_discrete_sequence=[TEAL],
                      labels={"total_payment": "Revenue (BRL)", "category_en": ""})
        fig2.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=320, margin=dict(l=20,r=20,t=10,b=20))
        fig2.update_xaxes(tickformat=",.0f", gridcolor="#F0EEE8")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Revenue by Price Bucket</div>', unsafe_allow_html=True)
        bucket = df.groupby("price_bucket")["total_payment"].sum().reset_index()
        fig3 = px.pie(bucket, values="total_payment", names="price_bucket",
                      hole=0.5, color_discrete_sequence=COLORS)
        fig3.update_layout(paper_bgcolor="white", height=320,
                           margin=dict(l=20,r=20,t=10,b=20))
        st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-header">Revenue by Day of Week</div>', unsafe_allow_html=True)
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow = (df.groupby("day_of_week")["total_payment"]
               .sum().reindex(dow_order).reset_index())
        fig4 = px.bar(dow, x="day_of_week", y="total_payment",
                      color_discrete_sequence=[CORAL],
                      labels={"total_payment": "Revenue (BRL)", "day_of_week": ""})
        fig4.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=280, margin=dict(l=20,r=20,t=10,b=20))
        fig4.update_yaxes(tickformat=",.0f", gridcolor="#F0EEE8")
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        st.markdown('<div class="section-header">Avg Order Value by Month</div>', unsafe_allow_html=True)
        aov = (df.groupby(["year","month"])["total_payment"]
               .mean().reset_index().sort_values(["year","month"]))
        aov["period"] = aov["year"].astype(str)+"-"+aov["month"].astype(str).str.zfill(2)
        fig5 = px.bar(aov, x="period", y="total_payment",
                      color_discrete_sequence=[AMBER],
                      labels={"total_payment": "Avg Order Value (BRL)", "period": ""})
        fig5.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=280, margin=dict(l=20,r=20,t=10,b=20))
        fig5.update_xaxes(tickangle=-45, tickfont_size=9)
        fig5.update_yaxes(tickformat=",.0f", gridcolor="#F0EEE8")
        st.plotly_chart(fig5, use_container_width=True)

# ════════════════════════════════════════════════════════════
# PAGE 2 — DELIVERY & OPERATIONS
# ════════════════════════════════════════════════════════════
elif page == "Delivery & Operations":
    st.title("Delivery & Operations")
    st.caption(f"Showing: {'All years' if selected_year == 'All' else selected_year}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Avg Delivery Days", f"{df['delivery_days'].mean():.1f}")
    with c2:
        late = df['is_late'].mean()*100
        st.metric("Late Order Rate", f"{late:.1f}%")
    with c3:
        status = "Good" if late <= 5 else "Watch" if late <= 10 else "Critical"
        st.metric("KPI Status", status)
    with c4:
        st.metric("Avg Review Score", f"{df['avg_review_score'].mean():.2f}/5")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Avg Delivery Days by State</div>', unsafe_allow_html=True)
        state_del = (df.groupby("state")["delivery_days"]
                     .mean().sort_values(ascending=True).reset_index())
        nat_avg = df["delivery_days"].mean()
        fig6 = px.bar(state_del, x="delivery_days", y="state", orientation="h",
                      color="delivery_days",
                      color_continuous_scale=["#0F6E56","#854F0B","#993C1D"],
                      labels={"delivery_days": "Avg Days", "state": ""})
        fig6.add_vline(x=nat_avg, line_dash="dash", line_color="#534AB7",
                       annotation_text=f"Avg: {nat_avg:.1f}d")
        fig6.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=420, margin=dict(l=20,r=20,t=10,b=20),
                           coloraxis_showscale=False)
        fig6.update_xaxes(gridcolor="#F0EEE8")
        st.plotly_chart(fig6, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Monthly Late Order Rate</div>', unsafe_allow_html=True)
        late_m = (df.groupby(["year","month"])
                  .agg(late_rate=("is_late","mean")).reset_index()
                  .sort_values(["year","month"]))
        late_m["period"] = late_m["year"].astype(str)+"-"+late_m["month"].astype(str).str.zfill(2)
        late_m["late_rate_pct"] = late_m["late_rate"]*100
        fig7 = px.line(late_m, x="period", y="late_rate_pct",
                       color_discrete_sequence=[CORAL],
                       labels={"late_rate_pct": "Late Rate %", "period": ""})
        fig7.add_hline(y=late_m["late_rate_pct"].mean(), line_dash="dash",
                       line_color="#534AB7",
                       annotation_text=f"Avg: {late_m['late_rate_pct'].mean():.1f}%")
        fig7.update_traces(line_width=2.5)
        fig7.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=420, margin=dict(l=20,r=20,t=10,b=40))
        fig7.update_xaxes(tickangle=-45, tickfont_size=9)
        fig7.update_yaxes(tickformat=".1f", gridcolor="#F0EEE8")
        st.plotly_chart(fig7, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-header">Delivery Days Distribution</div>', unsafe_allow_html=True)
        del_dist = df[df["delivery_days"].between(0,60)]["delivery_days"].dropna()
        fig8 = px.histogram(del_dist, nbins=40,
                            color_discrete_sequence=[PURPLE],
                            labels={"value": "Delivery Days", "count": "Orders"})
        fig8.add_vline(x=del_dist.mean(), line_dash="dash", line_color=CORAL,
                       annotation_text=f"Mean: {del_dist.mean():.1f}d")
        fig8.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                           height=280, margin=dict(l=20,r=20,t=10,b=20),
                           showlegend=False)
        fig8.update_yaxes(gridcolor="#F0EEE8")
        st.plotly_chart(fig8, use_container_width=True)

    with col4:
        st.markdown('<div class="section-header">On-Time vs Late Orders</div>', unsafe_allow_html=True)
        ot = df["is_late"].value_counts().reset_index()
        ot.columns = ["is_late","count"]
        ot["label"] = ot["is_late"].map({0:"On-Time", 1:"Late"})
        fig9 = px.pie(ot, values="count", names="label", hole=0.5,
                      color_discrete_sequence=[TEAL, CORAL])
        fig9.update_layout(paper_bgcolor="white", height=280,
                           margin=dict(l=20,r=20,t=10,b=20))
        st.plotly_chart(fig9, use_container_width=True)

# ════════════════════════════════════════════════════════════
# PAGE 3 — CUSTOMER INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "Customer Intelligence":
    st.title("Customer Intelligence")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customers", f"{len(rfm):,}")
    with c2:
        st.metric("Avg Review Score", f"{df['avg_review_score'].mean():.2f}/5")
    with c3:
        champ = len(rfm[rfm["segment"]=="Champions"])
        st.metric("Champions", f"{champ:,}", f"{champ/len(rfm)*100:.1f}% of base")
    with c4:
        atrisk = len(rfm[rfm["segment"]=="At Risk"])
        st.metric("At Risk", f"{atrisk:,}", f"{atrisk/len(rfm)*100:.1f}% of base",
                  delta_color="inverse")

    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown('<div class="section-header">RFM Segment Filter</div>', unsafe_allow_html=True)
        all_segs = sorted(rfm["segment"].unique().tolist())
        selected_segs = st.multiselect("Select segments", all_segs, default=all_segs)

    rfm_filtered = rfm[rfm["segment"].isin(selected_segs)] if selected_segs else rfm

    with col2:
        st.markdown('<div class="section-header">Revenue by RFM Segment</div>', unsafe_allow_html=True)
        seg_rev = (rfm_filtered.groupby("segment")["monetary"]
                   .sum().sort_values(ascending=True).reset_index())
        fig10 = px.bar(seg_rev, x="monetary", y="segment", orientation="h",
                       color="segment",
                       color_discrete_map={
                           "Champions": GREEN, "Loyal Customers": TEAL,
                           "At Risk": CORAL, "Cannot Lose Them": "#A32D2D",
                           "Hibernating": "#888780", "Need Attention": AMBER,
                           "Recent Customers": PURPLE, "Potential Loyalists": "#2E86AB"
                       },
                       labels={"monetary": "Total Spend (BRL)", "segment": ""})
        fig10.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                            height=300, margin=dict(l=20,r=20,t=10,b=20),
                            showlegend=False)
        fig10.update_xaxes(tickformat=",.0f", gridcolor="#F0EEE8")
        st.plotly_chart(fig10, use_container_width=True)

    col3, col4, col5 = st.columns(3)
    with col3:
        st.markdown('<div class="section-header">Review Score Distribution</div>', unsafe_allow_html=True)
        rev = df["avg_review_score"].dropna().round().value_counts().sort_index().reset_index()
        rev.columns = ["score","count"]
        rev["color"] = rev["score"].apply(lambda x: CORAL if x < 4 else TEAL)
        fig11 = px.bar(rev, x="score", y="count",
                       color="color", color_discrete_map="identity",
                       labels={"score": "Review Score", "count": "Orders"})
        fig11.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                            height=280, margin=dict(l=20,r=20,t=10,b=20),
                            showlegend=False)
        fig11.update_xaxes(tickvals=[1,2,3,4,5])
        fig11.update_yaxes(gridcolor="#F0EEE8")
        st.plotly_chart(fig11, use_container_width=True)

    with col4:
        st.markdown('<div class="section-header">Payment Type Split</div>', unsafe_allow_html=True)
        pay = df.groupby("payment_type")["order_id"].count().reset_index()
        pay.columns = ["payment_type","orders"]
        fig12 = px.pie(pay, values="orders", names="payment_type",
                       hole=0.5, color_discrete_sequence=COLORS)
        fig12.update_layout(paper_bgcolor="white", height=280,
                            margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig12, use_container_width=True)

    with col5:
        st.markdown('<div class="section-header">RFM Segment Distribution</div>', unsafe_allow_html=True)
        seg_count = rfm_filtered["segment"].value_counts().reset_index()
        seg_count.columns = ["segment","count"]
        fig13 = px.bar(seg_count, x="count", y="segment", orientation="h",
                       color_discrete_sequence=[PURPLE],
                       labels={"count": "Customers", "segment": ""})
        fig13.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                            height=280, margin=dict(l=20,r=20,t=10,b=20))
        fig13.update_xaxes(gridcolor="#F0EEE8")
        st.plotly_chart(fig13, use_container_width=True)

    st.markdown('<div class="section-header">RFM Customer Detail Table (Top 20 by Spend)</div>',
                unsafe_allow_html=True)
    top20 = (rfm_filtered.sort_values("monetary", ascending=False)
             .head(20)[["customer_key","city","state","recency_days",
                        "frequency","monetary","segment","r_score","f_score","m_score"]]
             .reset_index(drop=True))
    top20["monetary"] = top20["monetary"].apply(lambda x: f"R${x:,.2f}")
    st.dataframe(top20, use_container_width=True, height=280)

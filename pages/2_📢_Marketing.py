import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from utils.db_pipeline import load_marketing_customer_rfm, load_and_clean_catalog_data
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Marketing & Growth Analytics", page_icon="📢", layout="wide")
apply_custom_bi_theme()

st.title("📢 Marketing, Customer RFM & Revenue Growth")
st.markdown("Analyze customer spend distribution, revenue Pareto (80/20 rule), and genre market preference.")

df_rfm = load_marketing_customer_rfm()
df_catalog = load_and_clean_catalog_data()

if df_rfm.is_empty():
    st.warning("⚠️ Marketing customer data unavailable.")
    st.stop()

# --- METRIC CARDS ---
col1, col2, col3, col4 = st.columns(4)
total_customers = len(df_rfm)
total_revenue = float(df_rfm["total_spend"].sum())
avg_customer_spend = float(df_rfm["total_spend"].mean())
top_10_revenue = float(df_rfm.head(int(total_customers * 0.10))["total_spend"].sum())
top_10_pct = (top_10_revenue / total_revenue * 100) if total_revenue > 0 else 0.0

col1.metric("Active Customer Base", f"{total_customers:,}")
col2.metric("Total Gross Revenue", f"${total_revenue:,.2f}")
col3.metric("Avg Spend per Customer", f"${avg_customer_spend:.2f}")
col4.metric("Top 10% Revenue Share", f"{top_10_pct:.1f}%")

st.divider()

# --- REVENUE PARETO DUAL AXIS ---
st.subheader("👑 VIP Customer Revenue Pareto Analysis")

df_pd = df_rfm.to_pandas()
df_pd["cumulative_spend"] = df_pd["total_spend"].cumsum()
df_pd["cum_pct"] = (df_pd["cumulative_spend"] / total_revenue) * 100

top_n = st.slider("Select Top N Customers for Breakdown", min_value=10, max_value=100, value=30)
df_top = df_pd.head(top_n)

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(
    x=df_top["customer_name"],
    y=df_top["total_spend"],
    name="Total Spend ($)",
    marker=dict(color=df_top["total_spend"], colorscale="Plasma")
))
fig_pareto.add_trace(go.Scatter(
    x=df_top["customer_name"],
    y=df_top["cum_pct"],
    name="Cumulative Share %",
    yaxis="y2",
    mode="lines+markers",
    line=dict(color="#FFD700", width=3)
))
fig_pareto.update_layout(
    yaxis2=dict(title="Cumulative Share %", overlaying="y", side="right", range=[0, 105], showgrid=False)
)
apply_plotly_bi_theme(fig_pareto, title_text=f"Top {top_n} Customers Pareto Distribution", x_title="Customer Name", y_title="Spend ($)")
st.plotly_chart(fig_pareto, use_container_width=True)

st.divider()

# --- GENRE MARKET SHARE & RENTAL RATE DISTRIBUTION ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Genre Revenue & Market Share")
    df_cat_summary = (
        df_catalog
        .group_by("category")
        .agg([
            pl.col("total_rentals").sum().alias("total_rentals"),
            (pl.col("total_rentals") * pl.col("rental_rate")).sum().alias("estimated_revenue")
        ])
        .sort("estimated_revenue", descending=True)
        .to_pandas()
    )

    fig_pie = px.pie(
        df_cat_summary,
        names="category",
        values="estimated_revenue",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_pie, title_text="Estimated Revenue Share by Genre")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Price Tier Performance")
    df_price_tier = (
        df_catalog
        .group_by("rental_rate")
        .agg([
            pl.len().alias("film_count"),
            pl.col("total_rentals").sum().alias("total_rentals")
        ])
        .to_pandas()
    )
    df_price_tier["rental_rate_str"] = df_price_tier["rental_rate"].apply(lambda x: f"${x:.2f}")

    fig_price = px.bar(
        df_price_tier,
        x="rental_rate_str",
        y="total_rentals",
        color="film_count",
        title="Rentals by Price Point",
        labels={"rental_rate_str": "Price Tier", "total_rentals": "Total Rentals"},
        color_continuous_scale="Purples",
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_price, title_text="Demand Volume by Rental Price Point")
    st.plotly_chart(fig_price, use_container_width=True)

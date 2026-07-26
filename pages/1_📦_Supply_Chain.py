import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from utils.db_pipeline import load_supply_chain_metrics, load_and_clean_catalog_data
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Supply Chain & Asset Management", page_icon="📦", layout="wide")
apply_custom_bi_theme()

st.title("📦 Supply Chain & Inventory Asset Control")
st.markdown("Monitor inventory turnover, capital tied up in replacement costs, and stockout risk metrics.")

df_supply = load_supply_chain_metrics()
df_catalog = load_and_clean_catalog_data()

if df_supply.is_empty():
    st.warning("⚠️ Supply chain data unavailable. Please verify database container status.")
    st.stop()

# --- TOP METRIC CARDS ---
col1, col2, col3, col4 = st.columns(4)
total_units = int(df_supply["total_inventory_units"].sum())
total_capital = float(df_supply["total_capital_tied_up"].sum())
rented_now = int(df_supply["currently_rented_units"].sum())
utilization_rate = (rented_now / total_units * 100) if total_units > 0 else 0.0

col1.metric("Total Inventory Units", f"{total_units:,}")
col2.metric("Total Asset Value (Cost)", f"${total_capital:,.2f}")
col3.metric("Currently Rented (Out)", f"{rented_now:,}")
col4.metric("Inventory Utilization", f"{utilization_rate:.1f}%")

st.divider()

# --- CHARTS SECTION ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Capital Tied Up by Genre & Store")
    df_pd = df_supply.to_pandas()
    fig_capital = px.bar(
        df_pd,
        x="category",
        y="total_capital_tied_up",
        color="store_id",
        barmode="group",
        title="Asset Replacement Cost Exposure ($)",
        labels={"category": "Genre", "total_capital_tied_up": "Capital Tied Up ($)", "store_id": "Store ID"},
        color_continuous_scale="Electric",
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_capital, title_text="Asset Capital Exposure by Genre ($)", x_title="Genre", y_title="Capital ($)")
    st.plotly_chart(fig_capital, use_container_width=True)

with col_right:
    st.subheader("In-Stock vs Currently Rented")
    df_store_stock = df_supply.group_by("store_id").agg([
        pl.col("in_stock_units").sum(),
        pl.col("currently_rented_units").sum()
    ]).to_pandas()

    fig_stock = go.Figure()
    fig_stock.add_trace(go.Bar(
        x=df_store_stock["store_id"].astype(str),
        y=df_store_stock["in_stock_units"],
        name="In-Stock (Available)",
        marker_color="#00F2FE"
    ))
    fig_stock.add_trace(go.Bar(
        x=df_store_stock["store_id"].astype(str),
        y=df_store_stock["currently_rented_units"],
        name="Out on Rental",
        marker_color="#FF007F"
    ))
    fig_stock.update_layout(barmode="stack")
    apply_plotly_bi_theme(fig_stock, title_text="Stock Availability Breakdown by Store", x_title="Store ID", y_title="Units")
    st.plotly_chart(fig_stock, use_container_width=True)

# --- QUADRANT ASSET MATRIX ---
st.divider()
st.subheader("⚖️ High-Cost Inventory Asset Risk Matrix")

df_cat_pd = df_catalog.to_pandas()
avg_cost = float(df_cat_pd["replacement_cost"].mean())
avg_rentals = float(df_cat_pd["total_rentals"].mean())

fig_scatter = px.scatter(
    df_cat_pd,
    x="total_rentals",
    y="replacement_cost",
    color="category",
    size="inventory_copies",
    hover_name="title",
    labels={"total_rentals": "Lifetime Rentals", "replacement_cost": "Replacement Cost ($)"},
    template="plotly_dark"
)

fig_scatter.add_hline(y=avg_cost, line_dash="dash", line_color="#FF8C00", annotation_text=f"Avg Cost (${avg_cost:.2f})")
fig_scatter.add_vline(x=avg_rentals, line_dash="dash", line_color="#00F2FE", annotation_text=f"Avg Rentals ({avg_rentals:.0f})")
apply_plotly_bi_theme(fig_scatter, title_text="Asset Risk Matrix: Replacement Cost vs Rental Yield", x_title="Lifetime Rentals", y_title="Replacement Cost ($)")

st.plotly_chart(fig_scatter, use_container_width=True)

with st.expander("🔍 View Raw Supply Chain Data Table"):
    st.dataframe(df_pd, use_container_width=True)

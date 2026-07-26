import streamlit as st
from utils.db_pipeline import (
    load_and_clean_catalog_data,
    load_supply_chain_metrics,
    load_marketing_customer_rfm,
    load_operations_turnaround_data,
    load_market_basket_analysis,
    train_demand_model
)
from utils.ui_theme import apply_custom_bi_theme

# ==========================================
# PAGE CONFIGURATION & THEME SETUP
# ==========================================
st.set_page_config(
    page_title="DVD Rental Intelligence Hub",
    page_icon="🎬",
    layout="wide"
)

apply_custom_bi_theme()

st.title("⚡ DVD Rental Enterprise Intelligence & ML Portal")
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 100%); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 14px; padding: 22px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <h3 style="color: #00F2FE; margin-top: 0;">Welcome to the DVD Rental Executive Portal</h3>
    <p style="color: #CBD5E1; font-size: 1.05rem; margin-bottom: 0;">
        A comprehensive BI analytics & Supervised ML suite powered by <b>PostgreSQL 17</b>, <b>DuckDB</b>, <b>Polars</b>, <b>Plotly</b>, and <b>scikit-learn</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# DATA PREPARATION & GLOBAL METRICS
# ==========================================
df_catalog = load_and_clean_catalog_data()
df_supply = load_supply_chain_metrics()
df_rfm = load_marketing_customer_rfm()
df_ops = load_operations_turnaround_data()
rules_df, _ = load_market_basket_analysis()
model, r2, mse, features = train_demand_model(df_catalog)

if df_catalog.is_empty():
    st.warning("⚠️ Database offline or empty data. Please check container status (`make up`).")
    st.stop()

# ==========================================
# EXECUTIVE DASHBOARD KPI STRIP
# ==========================================
col1, col2, col3, col4, col5 = st.columns(5)
total_catalog = len(df_catalog)
total_asset_val = float(df_supply["total_capital_tied_up"].sum()) if not df_supply.is_empty() else 0.0
total_customers = len(df_rfm) if not df_rfm.is_empty() else 0
rules_count = len(rules_df) if not rules_df.is_empty() else 0
overdue_count = len(df_ops.filter(df_ops["return_status"] == "Overdue Return")) if not df_ops.is_empty() else 0

col1.metric("Catalog Titles", f"{total_catalog:,}")
col2.metric("Asset Value Exposure", f"${total_asset_val:,.2f}")
col3.metric("Active Customers", f"{total_customers:,}")
col4.metric("Market Basket Rules", f"{rules_count:,}")
col5.metric("Demand Model R²", f"{r2:.3f}")

st.divider()

# ==========================================
# DOMAIN MODULE NAVIGATION TILES
# ==========================================
st.subheader("🎯 Executive & Supervised ML Intelligence Domains")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #00F2FE; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #00F2FE; margin: 0 0 8px 0;">📦 1. Supply Chain & Asset Control</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            Track inventory copies, stock availability per store, capital tied up in replacement costs, and high-risk asset matrices.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #7F00FF; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #7F00FF; margin: 0 0 8px 0;">⚙️ 3. Operations & Turnaround</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            Analyze peak hourly traffic heatmaps (Day × Hour), store turnaround times, return compliance ratios, and bottlenecks.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #00FF66; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #00FF66; margin: 0 0 8px 0;">🛒 5. Market Basket & Co-Rental Affinity</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            Discover genre co-rental rules, cross-category affinities, and association metrics (<b>Support</b>, <b>Confidence</b>, and <b>Lift</b>).
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #FF007F; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #FF007F; margin: 0 0 8px 0;">📢 2. Marketing & Customer Growth</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            VIP customer RFM analysis, 80/20 revenue Pareto charts, genre market share, and rental price tier sensitivity breakdown.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #FFD700; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #FFD700; margin: 0 0 8px 0;">🧠 4. Predictive Demand Engine</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            Simulate prospective film rental demand with Random Forest Regressor models, model accuracy metrics (R²/MSE), and feature weights.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; border-left: 5px solid #38BDF8; border-radius: 12px; padding: 18px; margin-bottom: 18px;">
        <h4 style="color: #38BDF8; margin: 0 0 8px 0;">🤖 6. Supervised Machine Learning Suite</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
            Supervised <b>Customer Churn Classifier</b>, <b>Overdue Return Risk Model</b>, and <b>Film Demand Regressor</b> with interactive calculators.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.info("👈 Select a domain dashboard from the sidebar to launch interactive analytics.")
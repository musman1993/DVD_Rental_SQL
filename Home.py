import streamlit as st
from utils.ui_theme import apply_custom_bi_theme
st.set_page_config(
    page_title="DVD Rental Intelligence Hub",
    page_icon="🎬",
    layout="wide"
)

apply_custom_bi_theme()

st.title("⚡ DVD Rental Intelligence & ML Portal")
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 100%); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 14px; padding: 22px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <h3 style="color: #00F2FE; margin-top: 0;">Welcome to the DVD Rental Executive Portal</h3>
    <p style="color: #CBD5E1; font-size: 1.05rem; margin-bottom: 0;">
        A comprehensive BI analytics & Supervised ML suite powered by <b>PostgreSQL 17</b>, <b>DuckDB</b>, <b>Polars</b>, <b>Plotly</b>, and <b>scikit-learn</b>,
        built on top of the classic <b>DVD Rental</b> sample database (customers, rentals, payments, inventory, film catalog, staff and stores).
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("📂 What's inside")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📦 Supply Chain")
    st.caption(
        "Inventory turnover, capital tied up in replacement costs by genre & store, "
        "in-stock vs. currently-rented breakdowns, and a high-cost inventory risk matrix."
    )

    st.markdown("#### 📢 Marketing")
    st.caption(
        "Customer RFM segmentation, revenue Pareto (80/20) analysis, genre revenue & "
        "market share, and price-tier performance."
    )

    st.markdown("#### ⚙️ Operations")
    st.caption(
        "Rental turnaround times, peak hourly traffic (day × hour heatmap), overdue "
        "return compliance, and store-vs-store operational comparisons."
    )

with col2:
    st.markdown("#### 🛒 Market Basket Analysis")
    st.caption(
        "Genre co-rental association rules with support, confidence & lift metrics, "
        "plus a co-rental affinity heatmap across genres."
    )

    st.markdown("#### 🤖 Supervised Machine Learning")
    st.caption(
        "Predictive models for customer churn risk (Random Forest), overdue-return "
        "probability (Gradient Boosting), and film demand regression — each with "
        "interactive what-if calculators."
    )
st.divider()
st.subheader("🗄️ Source Data & Transformation")
st.markdown(
    "Everything in this portal is derived from the classic **PostgreSQL DVD Rental** "
    "sample database below — 15 normalized OLTP tables covering customers, staff, "
    "stores, inventory, film catalog, rentals and payments. The pages in the sidebar "
    "don't query these raw tables directly: `utils/db_pipeline.py` joins, aggregates "
    "and reshapes them (via Polars/DuckDB) into analytics-ready frames — customer RFM "
    "segments, inventory turnover, rental turnaround times, genre co-rental baskets, "
    "and ML training features — which the BI and ML pages then visualize."
    )
st.image(
    "docs/dvd-rental-sample-database-diagram.avif",
    caption="DVD Rental sample database — entity relationship diagram (raw OLTP schema)",
    use_container_width=True,
    )

st.divider()
st.info("👈 Please select a tool from the sidebar to begin.")
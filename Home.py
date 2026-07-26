import streamlit as st
from utils.ui_theme import apply_custom_bi_theme
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

st.info("👈 Please select a tool from the sidebar to begin.")
import streamlit as st
import plotly.express as px
from utils.db_pipeline import load_and_clean_catalog_data, train_demand_model
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Predictive Demand Modeling Engine", page_icon="🧠", layout="wide")
apply_custom_bi_theme()

st.title("🧠 Predictive Demand Engine & ML Diagnostics")
st.markdown("Train and simulate film rental demand using a **Random Forest Regressor** trained on historical catalog metadata.")

df_catalog = load_and_clean_catalog_data()
model, r2, mse, features = train_demand_model(df_catalog)

if model is None:
    st.warning("⚠️ Model training dataset unavailable. Check PostgreSQL connection.")
    st.stop()

# --- DIAGNOSTIC METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Model Algorithm", "Random Forest Regressor")
col2.metric("Variance Explained (R²)", f"{r2:.3f}")
col3.metric("Mean Squared Error (MSE)", f"{mse:.2f}")

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Feature Weight Importance")
    importances = model.feature_importances_
    fig_imp = px.bar(
        x=importances,
        y=features,
        orientation="h",
        labels={"x": "Importance Weight", "y": "Metadata Feature"},
        color=importances,
        color_continuous_scale="Purples",
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_imp, title_text="Random Forest Feature Importance Weights")
    st.plotly_chart(fig_imp, use_container_width=True)

with col_right:
    st.subheader("🎛️ Scenario Forecast Simulator")
    with st.form("demand_simulation_form"):
        input_length = st.number_input("Film Duration (Minutes)", min_value=30, max_value=300, value=120)
        input_rate = st.select_slider("Rental Rate ($)", options=[0.99, 2.99, 4.99], value=2.99)
        input_cost = st.slider("Replacement Cost ($)", min_value=9.99, max_value=29.99, value=19.99)

        submitted = st.form_submit_button("Run Demand Simulation")

        if submitted:
            pred = float(model.predict([[input_length, input_rate, input_cost]])[0])
            st.markdown(f"""
            <div style="background: rgba(0, 242, 254, 0.1); border: 2px solid #00F2FE; border-radius: 14px; padding: 24px; text-align: center; margin-top: 15px; box-shadow: 0 0 25px rgba(0, 242, 254, 0.3);">
                <span style="color: #94A3B8; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700;">Projected Lifetime Rentals</span>
                <h2 style="background: linear-gradient(90deg, #00F2FE 0%, #7F00FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0 0 0; font-size: 3rem; font-weight: 900;">{pred:.0f} Units</h2>
            </div>
            """, unsafe_allow_html=True)
            st.caption("✨ Forecast generated using Random Forest Regressor trained on DuckDB catalog features.")

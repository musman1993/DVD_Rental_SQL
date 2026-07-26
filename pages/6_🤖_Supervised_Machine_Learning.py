import streamlit as st
import polars as pl
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.db_pipeline import (
    load_marketing_customer_rfm,
    load_operations_turnaround_data,
    load_and_clean_catalog_data,
    train_customer_churn_classifier,
    train_overdue_risk_classifier,
    train_demand_model
)
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Supervised Machine Learning Engine", page_icon="🤖", layout="wide")
apply_custom_bi_theme()

st.title("🤖 Supervised Machine Learning Suite")
st.markdown("Enterprise supervised predictive models for **Customer Churn Risk**, **Overdue Return Probability**, and **Film Demand Regression**.")

df_rfm = load_marketing_customer_rfm()
df_ops = load_operations_turnaround_data()
df_catalog = load_and_clean_catalog_data()

tab1, tab2, tab3 = st.tabs([
    "🎯 Model 1: Customer Churn Classification",
    "⏰ Model 2: Overdue Return Risk Classifier",
    "📈 Model 3: Film Demand Regressor"
])

# ==========================================
# TAB 1: SUPERVISED CUSTOMER CHURN CLASSIFIER
# ==========================================
with tab1:
    st.header("🎯 Supervised Customer Churn Risk Model")
    st.markdown("Predicts customer churn / inactivity risk using a **Random Forest Classifier** trained on customer rental frequency and spend metrics.")

    model_churn, acc_c, prec_c, rec_c, auc_c, cm_c, feats_c = train_customer_churn_classifier(df_rfm)

    if model_churn is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Model Accuracy", f"{acc_c * 100:.1f}%")
        col2.metric("Precision", f"{prec_c * 100:.1f}%")
        col3.metric("Recall", f"{rec_c * 100:.1f}%")
        col4.metric("ROC-AUC Score", f"{auc_c:.3f}")

        st.divider()
        col_cm, col_sim = st.columns([1, 1])

        with col_cm:
            st.subheader("Confusion Matrix & Feature Importances")
            fig_cm = px.imshow(
                cm_c,
                text_auto=True,
                labels=dict(x="Predicted Label", y="True Label", color="Count"),
                x=["Retained", "High Risk / Churn"],
                y=["Retained", "High Risk / Churn"],
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            apply_plotly_bi_theme(fig_cm, title_text="Confusion Matrix: Customer Churn Classifier")
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_sim:
            st.subheader("🎛️ Interactive Customer Churn Risk Calculator")
            with st.form("churn_risk_form"):
                in_rentals = st.number_input("Lifetime Rental Count", min_value=1, max_value=200, value=14)
                in_spend = st.number_input("Total Spend ($)", min_value=5.0, max_value=500.0, value=58.5)
                in_ticket = st.slider("Average Ticket ($)", min_value=0.99, max_value=10.0, value=3.99)

                submit_c = st.form_submit_button("Compute Churn Risk")

                if submit_c:
                    prob = model_churn.predict_proba([[in_rentals, in_spend, in_ticket]])[0][1]
                    risk_pct = prob * 100
                    
                    if risk_pct >= 50.0:
                        st.error(f"⚠️ **High Churn Risk Probability:** {risk_pct:.1f}%")
                    else:
                        st.success(f"✅ **Low Churn Risk Probability:** {risk_pct:.1f}%")

# ==========================================
# TAB 2: OVERDUE RETURN RISK CLASSIFIER
# ==========================================
with tab2:
    st.header("⏰ Supervised Overdue Return Risk Model")
    st.markdown("Predicts rental delay risk using a **Gradient Boosting Classifier** on transaction and film attributes.")

    model_overdue, acc_o, prec_o, rec_o, auc_o, feats_o = train_overdue_risk_classifier(df_ops)

    if model_overdue is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Model Accuracy", f"{acc_o * 100:.1f}%")
        col2.metric("Precision", f"{prec_o * 100:.1f}%")
        col3.metric("Recall", f"{rec_o * 100:.1f}%")
        col4.metric("ROC-AUC Score", f"{auc_o:.3f}")

        st.divider()
        col_imp, col_osim = st.columns([1, 1])

        with col_imp:
            st.subheader("Gradient Boosting Feature Importances")
            imp_o = model_overdue.feature_importances_
            fig_o = px.bar(
                x=imp_o,
                y=feats_o,
                orientation="h",
                labels={"x": "Importance Weight", "y": "Attribute"},
                color=imp_o,
                color_continuous_scale="Magma",
                template="plotly_dark"
            )
            apply_plotly_bi_theme(fig_o, title_text="Overdue Risk Feature Contributions")
            st.plotly_chart(fig_o, use_container_width=True)

        with col_osim:
            st.subheader("🎛️ Transaction Delay Risk Evaluator")
            with st.form("overdue_risk_form"):
                o_length = st.number_input("Film Duration (Minutes)", min_value=30, max_value=300, value=130)
                o_rate = st.selectbox("Rental Rate ($)", [0.99, 2.99, 4.99], index=0)
                o_cost = st.slider("Replacement Cost ($)", min_value=9.99, max_value=29.99, value=21.99)
                o_allowed = st.slider("Allowed Days", min_value=3, max_value=7, value=3)

                submit_o = st.form_submit_button("Predict Overdue Risk")

                if submit_o:
                    prob_o = model_overdue.predict_proba([[o_length, o_rate, o_cost, o_allowed]])[0][1]
                    late_pct = prob_o * 100

                    if late_pct >= 50.0:
                        st.error(f"⚠️ **High Overdue Probability:** {late_pct:.1f}%")
                    else:
                        st.success(f"✅ **On-Time Probability:** {100 - late_pct:.1f}%")

# ==========================================
# TAB 3: FILM DEMAND REGRESSOR
# ==========================================
with tab3:
    st.header("📈 Supervised Film Demand Regressor")
    st.markdown("Forecast lifetime rental volume for new catalog entries using a **Random Forest Regressor**.")

    model_reg, r2_r, mse_r, feats_r = train_demand_model(df_catalog)

    if model_reg is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Model Algorithm", "Random Forest Regressor")
        col2.metric("R² Score", f"{r2_r:.3f}")
        col3.metric("MSE Metric", f"{mse_r:.2f}")

        st.divider()
        render_imp = px.bar(
            x=model_reg.feature_importances_,
            y=feats_r,
            orientation="h",
            labels={"x": "Importance Weight", "y": "Feature"},
            color=model_reg.feature_importances_,
            color_continuous_scale="Purples",
            template="plotly_dark"
        )
        apply_plotly_bi_theme(render_imp, title_text="Demand Regressor Feature Weights")
        st.plotly_chart(render_imp, use_container_width=True)

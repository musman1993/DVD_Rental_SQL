import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from utils.db_pipeline import load_market_basket_analysis
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Market Basket Analysis", page_icon="🛒", layout="wide")
apply_custom_bi_theme()

st.title("🛒 Market Basket & Co-Rental Affinity Analysis")
st.markdown("Discover genre co-rental rules, cross-category affinities, and association rule metrics (**Support**, **Confidence**, and **Lift**).")

rules_df, pairs_df = load_market_basket_analysis()

if rules_df.is_empty():
    st.warning("⚠️ Market basket data unavailable. Check PostgreSQL database connectivity.")
    st.stop()

# --- TOP METRIC STRIP ---
col1, col2, col3, col4 = st.columns(4)
total_rules = len(rules_df)
max_lift = float(rules_df["Lift"].max())
avg_confidence = float(rules_df["Confidence (A->B)"].mean() * 100)
top_pair = f"{rules_df['Antecedent (Genre A)'][0]} ↔ {rules_df['Consequent (Genre B)'][0]}"

col1.metric("Discovered Rule Pairs", f"{total_rules:,}")
col2.metric("Maximum Pair Lift", f"{max_lift:.2f}x")
col3.metric("Avg Pair Confidence", f"{avg_confidence:.1f}%")
col4.metric("Strongest Co-Rental Pair", top_pair)

st.divider()

# --- INTERACTIVE RULE FILTERING ---
st.subheader("🎛️ Association Rule Threshold Filters")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    min_support = st.slider("Minimum Support Threshold", min_value=0.01, max_value=0.50, value=0.05, step=0.01)
with col_f2:
    min_confidence = st.slider("Minimum Confidence Threshold", min_value=0.10, max_value=1.00, value=0.30, step=0.05)
with col_f3:
    min_lift = st.slider("Minimum Lift Threshold", min_value=0.80, max_value=3.00, value=1.00, step=0.05)

filtered_rules = rules_df.filter(
    (pl.col("Support") >= min_support) &
    (pl.col("Confidence (A->B)") >= min_confidence) &
    (pl.col("Lift") >= min_lift)
).to_pandas()

st.markdown(f"**Found {len(filtered_rules)} rules matching thresholds.**")

# --- CHARTS ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Support vs Confidence Scatter (Colored by Lift)")
    if not filtered_rules.empty:
        fig_scatter = px.scatter(
            filtered_rules,
            x="Support",
            y="Confidence (A->B)",
            size="Pair Count",
            color="Lift",
            hover_name="Antecedent (Genre A)",
            hover_data=["Consequent (Genre B)", "Lift"],
            labels={"Confidence (A->B)": "Confidence (A → B)"},
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        apply_plotly_bi_theme(fig_scatter, title_text="Association Rule Support vs Confidence Matrix", x_title="Support", y_title="Confidence")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No rules match current filter thresholds.")

with col_right:
    st.subheader("Top 15 Co-Rental Rules by Lift")
    if not filtered_rules.empty:
        top_15 = filtered_rules.sort_values("Lift", ascending=False).head(15)
        top_15["rule_name"] = top_15["Antecedent (Genre A)"] + " ➔ " + top_15["Consequent (Genre B)"]

        fig_bar = px.bar(
            top_15,
            x="Lift",
            y="rule_name",
            orientation="h",
            color="Lift",
            color_continuous_scale="Plasma",
            template="plotly_dark"
        )
        apply_plotly_bi_theme(fig_bar, title_text="Top 15 Genre Association Rules by Lift", x_title="Lift", y_title="Rule")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- CO-RENTAL HEATMAP ---
st.divider()
st.subheader("🔥 Genre Co-Rental Matrix Heatmap")

if not pairs_df.is_empty():
    df_pairs_pd = pairs_df.to_pandas()
    pivot_matrix = df_pairs_pd.pivot(index="genre_A", columns="genre_B", values="pair_customer_count").fillna(0)

    fig_matrix = go.Figure(data=go.Heatmap(
        z=pivot_matrix.values,
        x=pivot_matrix.columns,
        y=pivot_matrix.index,
        colorscale=[
            [0.0, "#0F172A"],
            [0.3, "#0284C7"],
            [0.6, "#00F2FE"],
            [0.8, "#7F00FF"],
            [1.0, "#FF007F"]
        ],
        hovertemplate="<b>Genre A:</b> %{y}<br><b>Genre B:</b> %{x}<br><b>Co-Renting Customers:</b> %{z:,}<extra></extra>"
    ))
    apply_plotly_bi_theme(fig_matrix, title_text="Co-Rental Customer Overlap Heatmap", x_title="Genre B", y_title="Genre A")
    st.plotly_chart(fig_matrix, use_container_width=True)

with st.expander("🔍 View Filtered Association Rules Data Table"):
    st.dataframe(filtered_rules, use_container_width=True)

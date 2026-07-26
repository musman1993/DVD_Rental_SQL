import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from utils.db_pipeline import load_operations_turnaround_data, load_rental_activity_data
from utils.ui_theme import apply_custom_bi_theme, apply_plotly_bi_theme

st.set_page_config(page_title="Operations & Logistics", page_icon="⚙️", layout="wide")
apply_custom_bi_theme()

st.title("⚙️ Operations, Turnaround & Traffic Activity")
st.markdown("Analyze rental turnaround times, peak hourly rental windows, overdue return ratios, and store bottlenecks.")

df_ops = load_operations_turnaround_data()
df_activity = load_rental_activity_data()

if df_ops.is_empty():
    st.warning("⚠️ Operations data unavailable.")
    st.stop()

# --- METRIC CARDS ---
col1, col2, col3, col4 = st.columns(4)
total_transactions = len(df_ops)
df_pd = df_ops.to_pandas()
overdue_count = len(df_pd[df_pd["return_status"] == "Overdue Return"])
overdue_pct = (overdue_count / total_transactions * 100) if total_transactions > 0 else 0.0
avg_actual_days = float(df_pd["actual_days"].mean())
avg_allowed_days = float(df_pd["allowed_days"].mean())

col1.metric("Logged Transactions", f"{total_transactions:,}")
col2.metric("Overdue Rate", f"{overdue_pct:.1f}%")
col3.metric("Avg Actual Turnaround", f"{avg_actual_days:.1f} Days")
col4.metric("Avg Allowed Rental Window", f"{avg_allowed_days:.1f} Days")

st.divider()

# --- PEAK HOURLY HEATMAP ---
st.subheader("🔥 Operational Peak Traffic Matrix (Day × Hour)")

if not df_activity.is_empty():
    df_act_pd = df_activity.to_pandas()
    day_map = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
    df_act_pd["day_name"] = df_act_pd["day_of_week"].map(day_map)

    pivot_df = df_act_pd.pivot(index="day_name", columns="hour_of_day", values="rental_count").fillna(0)
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot_df = pivot_df.reindex([d for d in day_order if d in pivot_df.index])

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=[f"{int(h):02d}:00" for h in pivot_df.columns],
        y=pivot_df.index,
        colorscale=[
            [0.0, "#0F172A"],
            [0.2, "#0369A1"],
            [0.5, "#00F2FE"],
            [0.8, "#7F00FF"],
            [1.0, "#FF007F"]
        ],
        hovertemplate="<b>Day:</b> %{y}<br><b>Hour:</b> %{x}<br><b>Transactions:</b> %{z:,}<extra></extra>"
    ))
    apply_plotly_bi_theme(fig_heatmap, title_text="Peak Traffic Activity Matrix (Day × Hour)", x_title="Hour of Day", y_title="Day of Week")
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# --- RETURN STATUS & STORE COMPARISON ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rental Return Status Compliance")
    status_counts = df_pd["return_status"].value_counts().reset_index()
    status_counts.columns = ["return_status", "count"]

    fig_status = px.bar(
        status_counts,
        x="return_status",
        y="count",
        color="return_status",
        color_discrete_map={
            "On-Time Return": "#00FF66",
            "Overdue Return": "#FF007F",
            "Currently Rented": "#00F2FE"
        },
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_status, title_text="Return Compliance Distribution", x_title="Status", y_title="Count")
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("Store 1 vs Store 2 Operational Turnaround")
    fig_store = px.box(
        df_pd,
        x="store_id",
        y="actual_days",
        color="store_id",
        points="outliers",
        labels={"store_id": "Store ID", "actual_days": "Actual Rental Days"},
        color_discrete_sequence=["#00F2FE", "#7F00FF"],
        template="plotly_dark"
    )
    apply_plotly_bi_theme(fig_store, title_text="Turnaround Time Distribution by Store", x_title="Store ID", y_title="Days")
    st.plotly_chart(fig_store, use_container_width=True)

import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def apply_custom_bi_theme():
    """Applies an aggressive, vibrant neon cyber-dark theme to Streamlit."""
    st.markdown("""
    <style>
        /* Base Cyber Dark Environment */
        .stApp {
            background: radial-gradient(circle at 50% 0%, #0F172A 0%, #020617 100%);
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* Aggressive Glowing Metric Cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%);
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-left: 5px solid #00F2FE;
            border-radius: 14px;
            padding: 18px 22px;
            box-shadow: 0 10px 25px -5px rgba(0, 242, 254, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px) scale(1.01);
            border-color: #00F2FE;
            box-shadow: 0 15px 35px -5px rgba(0, 242, 254, 0.35), 0 0 15px rgba(0, 242, 254, 0.25);
        }

        /* Neon Metric Labels & Typography */
        div[data-testid="stMetricLabel"] > label {
            color: #94A3B8 !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }
        div[data-testid="stMetricValue"] > div {
            background: linear-gradient(90deg, #FFFFFF 0%, #38BDF8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }

        /* Aggressive Neon Gradient Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #00F2FE 0%, #7F00FF 100%);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            border: none;
            border-radius: 10px;
            padding: 12px 28px;
            box-shadow: 0 4px 20px rgba(0, 242, 254, 0.4);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #7F00FF 0%, #00F2FE 100%);
            box-shadow: 0 8px 30px rgba(127, 0, 255, 0.6), 0 0 20px rgba(0, 242, 254, 0.5);
            transform: translateY(-2px);
        }

        /* Tab Header Customization */
        button[data-baseweb="tab"] {
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            color: #94A3B8 !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
        }
        button[aria-selected="true"] {
            color: #00F2FE !important;
            background: rgba(0, 242, 254, 0.1) !important;
            border-bottom: 3px solid #00F2FE !important;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_plotly_bi_theme(fig: go.Figure, title_text: str = "", x_title: str = "", y_title: str = "") -> go.Figure:
    """Applies standardized aggressive cyber-dark styling to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(2, 6, 23, 0.8)",
        margin=dict(l=40, r=40, t=60, b=40),
        title=dict(
            text=f"<b>{title_text}</b>" if title_text else "",
            font=dict(size=19, color="#FFFFFF", family="-apple-system, sans-serif"),
            x=0.0,
            xanchor="left"
        ),
        xaxis=dict(
            title=dict(text=x_title, font=dict(color="#94A3B8", size=13)) if x_title else None,
            gridcolor="#1E293B",
            zerolinecolor="#334155",
            tickfont=dict(color="#CBD5E1")
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="#94A3B8", size=13)) if y_title else None,
            gridcolor="#1E293B",
            zerolinecolor="#334155",
            tickfont=dict(color="#CBD5E1")
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.85)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="#F8FAFC")
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=13,
            font_family="-apple-system, sans-serif",
            bordercolor="#00F2FE"
        )
    )
    return fig

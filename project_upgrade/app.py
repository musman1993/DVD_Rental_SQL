import os

import duckdb
import polars as pl
import plotly.express as px
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Analytics Showcase",
    page_icon="📊",
    layout="wide"
)

# --- CONNECTION CONFIG ---
# These default to "localhost" so `uv run streamlit run app.py` still works
# unchanged for local dev outside Docker. Inside docker-compose, the app
# container reaches Postgres by its SERVICE NAME ("db"), not "localhost" —
# Compose's embedded DNS resolves "db" to the db container's internal IP on
# the shared network. docker-compose.yml sets POSTGRES_HOST=db explicitly
# for the app service to make this work without touching this file.
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
PG_DB = os.environ.get("POSTGRES_DB", "dvdrental")

# --- DATABASE CONNECTION CACHING ---
# We cache the DuckDB connection to prevent re-attaching on every user interaction
@st.cache_resource
def get_duckdb_connection():
    con = duckdb.connect()
    # LOAD (not INSTALL) here — the extension is already installed at image
    # build time (see app/Dockerfile). Calling INSTALL again would be a
    # harmless no-op locally, but LOAD is the precise, correct call at
    # runtime since the binary is already on disk.
    con.execute("LOAD postgres;")

    pg_conn_str = (
        f"dbname={PG_DB} user={PG_USER} password={PG_PASSWORD} "
        f"host={PG_HOST} port={PG_PORT}"
    )
    con.execute(f"ATTACH '{pg_conn_str}' AS pg (TYPE POSTGRES);")
    return con

con = get_duckdb_connection()

# --- APP TITLE & SIDEBAR ---
st.title("⚡ PostgreSQL + DuckDB Analytics Engine")
st.markdown("High-performance OLAP analytics layer powered by **DuckDB**, **Polars**, and **Plotly**.")

st.sidebar.header("Filter Controls")

# Fetch categories dynamically via DuckDB
categories_df = con.execute("SELECT name FROM pg.public.category ORDER BY name;").pl()
category_list = categories_df["name"].to_list()
selected_category = st.sidebar.selectbox("Select Film Category:", category_list)

# --- DATA QUERYING VIA POLARS ---
# Parameterized query instead of an f-string — avoids building a SQL
# injection vector out of a value that ultimately comes from user-controlled
# input (the sidebar selectbox). DuckDB's execute() accepts positional
# parameters via `?` the same way most DB-API drivers do.
query = """
    SELECT
        f.film_id,
        f.title,
        f.length,
        f.rental_rate,
        f.rating,
        c.name as category
    FROM pg.public.film f
    JOIN pg.public.film_category fc ON f.film_id = fc.film_id
    JOIN pg.public.category c ON fc.category_id = c.category_id
    WHERE c.name = ?
"""

# Zero-copy conversion into Polars
df: pl.DataFrame = con.execute(query, [selected_category]).pl()

# --- METRIC CARDS ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Titles", len(df))
col2.metric("Avg Duration (mins)", round(df["length"].mean(), 1))
col3.metric("Avg Rental Rate ($)", f"${df['rental_rate'].mean():.2f}")

st.divider()

# --- INTERACTIVE PLOTLY CHARTS ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Film Length vs. Rental Rate")
    fig_scatter = px.scatter(
        df.to_pandas(),
        x="length",
        y="rental_rate",
        color="rating",
        hover_data=["title"],
        labels={"length": "Film Duration (Mins)", "rental_rate": "Rental Price ($)"},
        template="plotly_dark",
    )
    fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("Distribution by Rating")
    rating_counts = df.group_by("rating").len().sort("len", descending=True)

    fig_bar = px.bar(
        rating_counts.to_pandas(),
        x="rating",
        y="len",
        color="rating",
        labels={"len": "Number of Films", "rating": "MPAA Rating"},
        template="plotly_dark",
    )
    fig_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# --- DATA TABLE ---
st.subheader("Raw Data View")
st.dataframe(df.to_pandas(), use_container_width=True)

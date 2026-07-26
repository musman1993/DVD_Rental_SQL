import streamlit as st
import duckdb
import polars as pl
import plotly.express as px

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")
st.title("📊 Analytics Dashboard")

# 1. Database Connection & Polars Extraction
@st.cache_data
def load_data():
    con = duckdb.connect()
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")
    pg_conn = "dbname=dvdrental user=postgres password=postgres host=localhost port=5432"
    con.execute(f"ATTACH '{pg_conn}' AS pg (TYPE POSTGRES);")
    
    query = """
        SELECT c.name AS category_name, COUNT(fc.film_id) AS total_films
        FROM pg.public.category c
        JOIN pg.public.film_category fc ON c.category_id = fc.category_id
        GROUP BY c.name
    """
    # Execute and output directly to a Polars DataFrame
    return con.execute(query).pl()

df_cat = load_data()

# 2. Polars Data Manipulation (Filtering categories with > 50 films)
df_filtered = df_cat.filter(pl.col("total_films") > 50).sort("total_films", descending=True)

# 3. Plotly Visualization
st.subheader("Inventory Distribution by Category")

fig_cat = px.bar(
    df_filtered.to_pandas(), # Plotly consumes pandas easily
    x="total_films",
    y="category_name",
    orientation="h",
    title="Top Performing Categories (>50 Films)",
    labels={"category_name": "Genre", "total_films": "Volume"},
    template="plotly_dark",
    color="total_films",
    color_continuous_scale="Viridis"
)

st.plotly_chart(fig_cat, use_container_width=True)

# Raw Data View
with st.expander("View Raw Data"):
    st.dataframe(df_filtered.to_pandas(), use_container_width=True)
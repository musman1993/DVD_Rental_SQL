import duckdb
import polars as pl
import plotly.express as px
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="DVD Rental Intelligence", layout="wide")
st.title("🎬 DVD Rental Intelligence & Prediction Engine")

# ==========================================
# PHASE 1: DATA EXTRACTION & CLEANING (ETL)
# ==========================================
@st.cache_resource
def get_db_connection():
    con = duckdb.connect()
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")
    pg_conn = "dbname=dvdrental user=postgres password=postgres host=localhost port=5432"
    con.execute(f"ATTACH '{pg_conn}' AS pg (TYPE POSTGRES);")
    return con

@st.cache_data
def load_and_clean_data():
    con = get_db_connection()
    
    # Extract: Join film, inventory, and rental tables to get total rentals per film
    query = """
        SELECT 
            f.film_id,
            f.title,
            f.length,
            f.rental_rate,
            f.replacement_cost,
            c.name AS category,
            COUNT(r.rental_id) AS total_rentals
        FROM pg.public.film f
        LEFT JOIN pg.public.film_category fc ON f.film_id = fc.film_id
        LEFT JOIN pg.public.category c ON fc.category_id = c.category_id
        LEFT JOIN pg.public.inventory i ON f.film_id = i.film_id
        LEFT JOIN pg.public.rental r ON i.inventory_id = r.inventory_id
        GROUP BY f.film_id, f.title, f.length, f.rental_rate, f.replacement_cost, c.name
    """
    
    # Load into Polars
    df = con.execute(query).pl()
    
    # Clean: Drop rows with null values and cast types appropriately
    df_cleaned = (
        df.drop_nulls()
        .with_columns([
            pl.col("length").cast(pl.Float64),
            pl.col("rental_rate").cast(pl.Float64),
            pl.col("replacement_cost").cast(pl.Float64),
            pl.col("total_rentals").cast(pl.Float64)
        ])
    )
    return df_cleaned

df = load_and_clean_data()

# ==========================================
# PHASE 2: EXPLORATORY DATA ANALYSIS (EDA)
# ==========================================
st.header("📊 Business Analytics & Visualization")

col1, col2, col3 = st.columns(3)
col1.metric("Total Catalog Size", len(df))
col2.metric("Average Rentals per Film", round(df["total_rentals"].mean(), 1))
col3.metric("Avg Replacement Cost", f"${df['replacement_cost'].mean():.2f}")

# Visualizing Category Performance using Plotly
category_summary = df.group_by("category").agg(
    pl.col("total_rentals").sum().alias("sum_rentals")
).sort("sum_rentals", descending=True)

fig_bar = px.bar(
    category_summary.to_pandas(), 
    x="category", 
    y="sum_rentals",
    title="Total Rentals by Genre",
    template="plotly_dark",
    color="sum_rentals",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# PHASE 3: MACHINE LEARNING & PREDICTION
# ==========================================
st.header("🧠 Predictive Modeling: Rental Demand")
st.markdown("""
We will train a **Random Forest Regressor** to predict how many times a film will be rented based on its metadata.
""")

# Prepare Features (X) and Target (y)
features = ["length", "rental_rate", "replacement_cost"]
target = "total_rentals"

X = df.select(features).to_numpy()
y = df.select(target).to_numpy().ravel()

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Model Evaluation
predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

col_metric1, col_metric2 = st.columns(2)
col_metric1.metric("Model R² Score", round(r2, 3))
col_metric2.metric("Mean Squared Error (MSE)", round(mse, 2))

# ==========================================
# PHASE 4: INTERACTIVE PREDICTION UI
# ==========================================
st.subheader("🔮 Predict Demand for a New Film")

with st.form("prediction_form"):
    input_length = st.number_input("Film Length (minutes)", min_value=30, max_value=300, value=120)
    input_rate = st.selectbox("Rental Rate ($)", [0.99, 2.99, 4.99])
    input_cost = st.slider("Replacement Cost ($)", min_value=9.99, max_value=29.99, value=19.99)
    
    submitted = st.form_submit_button("Predict Total Rentals")
    
    if submitted:
        # Create input array matching the feature structure
        new_data = [[input_length, input_rate, input_cost]]
        predicted_rentals = model.predict(new_data)[0]
        
        st.success(f"This film is projected to be rented **{predicted_rentals:.0f} times** over its lifecycle.")
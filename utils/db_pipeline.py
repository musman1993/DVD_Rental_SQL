import os
import duckdb
import numpy as np
import polars as pl
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix
)

load_dotenv()


def get_env_db_conn_string() -> str:
    """Build PostgreSQL connection string.

    Prefers Streamlit secrets (`.streamlit/secrets.toml`, e.g. Neon for the
    deployed web app) when a [postgres] table is configured there; otherwise
    falls back to POSTGRES_* environment variables (local Docker Postgres).
    """
    pg_secrets = st.secrets.get("postgres", {}) if hasattr(st, "secrets") else {}

    host = pg_secrets.get("host", os.environ.get("POSTGRES_HOST", "localhost"))
    port = pg_secrets.get("port", os.environ.get("POSTGRES_PORT", "5432"))
    user = pg_secrets.get("user", os.environ.get("POSTGRES_USER", "postgres"))
    password = pg_secrets.get("password", os.environ.get("POSTGRES_PASSWORD", "postgres"))
    dbname = pg_secrets.get("dbname", os.environ.get("POSTGRES_DB", "dvdrental"))
    sslmode = pg_secrets.get("sslmode", os.environ.get("POSTGRES_SSLMODE"))

    conn_str = f"dbname={dbname} user={user} password={password} host={host} port={port}"
    if sslmode:
        conn_str += f" sslmode={sslmode}"
    return conn_str


@st.cache_resource
def get_duckdb_connection():
    """Creates and caches a DuckDB connection attached to PostgreSQL with error handling."""
    try:
        con = duckdb.connect()
        con.execute("LOAD postgres;")
        pg_conn_str = get_env_db_conn_string()
        con.execute(f"ATTACH '{pg_conn_str}' AS pg (TYPE POSTGRES);")
        return con
    except Exception as e:
        st.error(f"⚠️ Failed to connect to PostgreSQL database: {e}")
        return None


@st.cache_data(ttl=3600)
def load_and_clean_catalog_data():
    """Loads film catalog data joined with categories, inventory, and rentals."""
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame()

    query = """
        SELECT 
            f.film_id,
            f.title,
            f.length,
            f.rental_duration,
            f.rental_rate,
            f.replacement_cost,
            f.rating,
            COALESCE(c.name, 'Uncategorized') AS category,
            COUNT(DISTINCT i.inventory_id) AS inventory_copies,
            COUNT(r.rental_id) AS total_rentals
        FROM pg.public.film f
        LEFT JOIN pg.public.film_category fc ON f.film_id = fc.film_id
        LEFT JOIN pg.public.category c ON fc.category_id = c.category_id
        LEFT JOIN pg.public.inventory i ON f.film_id = i.film_id
        LEFT JOIN pg.public.rental r ON i.inventory_id = r.inventory_id
        GROUP BY f.film_id, f.title, f.length, f.rental_duration, f.rental_rate, f.replacement_cost, f.rating, c.name
    """
    try:
        df = con.execute(query).pl()
        if df.is_empty():
            return df

        return df.with_columns([
            pl.col("length").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("rental_duration").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("rental_rate").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("replacement_cost").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("inventory_copies").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("total_rentals").cast(pl.Float64, strict=False).fill_null(0.0)
        ])
    except Exception as e:
        st.error(f"Error loading film catalog data: {e}")
        return pl.DataFrame()


@st.cache_data(ttl=3600)
def load_supply_chain_metrics():
    """Loads inventory stock, capital tied up, store distributions, and unreturned item counts."""
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame()

    query = """
        SELECT 
            s.store_id,
            COALESCE(c.name, 'Uncategorized') AS category,
            COUNT(i.inventory_id) AS total_inventory_units,
            SUM(f.replacement_cost) AS total_capital_tied_up,
            COUNT(CASE WHEN r.return_date IS NULL THEN 1 END) AS currently_rented_units,
            COUNT(i.inventory_id) - COUNT(CASE WHEN r.return_date IS NULL THEN 1 END) AS in_stock_units
        FROM pg.public.inventory i
        JOIN pg.public.film f ON i.film_id = f.film_id
        LEFT JOIN pg.public.film_category fc ON f.film_id = fc.film_id
        LEFT JOIN pg.public.category c ON fc.category_id = c.category_id
        JOIN pg.public.store s ON i.store_id = s.store_id
        LEFT JOIN pg.public.rental r ON i.inventory_id = r.inventory_id AND r.return_date IS NULL
        GROUP BY s.store_id, c.name
        ORDER BY store_id, total_capital_tied_up DESC
    """
    try:
        return con.execute(query).pl()
    except Exception as e:
        st.error(f"Error loading supply chain data: {e}")
        return pl.DataFrame()


@st.cache_data(ttl=3600)
def load_marketing_customer_rfm():
    """Loads customer rental frequency, monetary spend, and churn label."""
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame()

    query = """
        SELECT 
            c.customer_id,
            c.first_name || ' ' || c.last_name AS customer_name,
            c.email,
            c.activebool AS is_active,
            COUNT(r.rental_id) AS rental_count,
            SUM(p.amount) AS total_spend,
            AVG(p.amount) AS avg_ticket_value,
            MAX(r.rental_date) AS last_rental_date,
            MIN(r.rental_date) AS first_rental_date
        FROM pg.public.customer c
        JOIN pg.public.rental r ON c.customer_id = r.customer_id
        JOIN pg.public.payment p ON r.rental_id = p.rental_id
        GROUP BY c.customer_id, customer_name, c.email, c.activebool
        ORDER BY total_spend DESC
    """
    try:
        df = con.execute(query).pl()
        if df.is_empty():
            return df
        
        # Calculate tenure days and create synthetic Churn target (rental_count < 15 or low spend)
        df_processed = df.with_columns([
            (pl.col("rental_count") < 20).cast(pl.Int32).alias("churn_risk_label")
        ])
        return df_processed
    except Exception as e:
        st.error(f"Error loading marketing customer RFM data: {e}")
        return pl.DataFrame()


@st.cache_data(ttl=3600)
def load_operations_turnaround_data():
    """Loads rental duration, overdue rates, turn-around times, and store performance."""
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame()

    query = """
        SELECT 
            r.rental_id,
            r.customer_id,
            r.staff_id,
            i.store_id,
            f.film_id,
            f.title,
            f.rental_rate,
            f.replacement_cost,
            f.length,
            f.rental_duration AS allowed_days,
            EXTRACT(EPOCH FROM (COALESCE(r.return_date, NOW()) - r.rental_date)) / 86400.0 AS actual_days,
            CASE 
                WHEN r.return_date IS NULL THEN 1
                WHEN (EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 86400.0) > f.rental_duration THEN 1
                ELSE 0
            END AS is_overdue,
            CASE 
                WHEN r.return_date IS NULL THEN 'Currently Rented'
                WHEN (EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 86400.0) > f.rental_duration THEN 'Overdue Return'
                ELSE 'On-Time Return'
            END AS return_status
        FROM pg.public.rental r
        JOIN pg.public.inventory i ON r.inventory_id = i.inventory_id
        JOIN pg.public.film f ON i.film_id = f.film_id
        LIMIT 5000
    """
    try:
        return con.execute(query).pl()
    except Exception as e:
        st.error(f"Error loading operations turnaround data: {e}")
        return pl.DataFrame()


@st.cache_data(ttl=3600)
def load_rental_activity_data():
    """Loads rental timestamps aggregated by day-of-week and hour-of-day for activity heatmaps."""
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame()

    query = """
        SELECT 
            EXTRACT(DOW FROM rental_date) AS day_of_week,
            EXTRACT(HOUR FROM rental_date) AS hour_of_day,
            COUNT(rental_id) AS rental_count
        FROM pg.public.rental
        GROUP BY day_of_week, hour_of_day
        ORDER BY day_of_week, hour_of_day
    """
    try:
        return con.execute(query).pl()
    except Exception as e:
        st.error(f"Error loading rental activity data: {e}")
        return pl.DataFrame()


# ==========================================
# 🛒 MARKET BASKET ANALYSIS (ASSOCIATION RULES)
# ==========================================
@st.cache_data(ttl=3600)
def load_market_basket_analysis():
    """
    Performs Market Basket Analysis on film genre co-rentals by customer transactions.
    Calculates Support, Confidence, and Lift metrics for genre pairs.
    """
    con = get_duckdb_connection()
    if con is None:
        return pl.DataFrame(), pl.DataFrame()

    query_genre_pairs = """
        WITH customer_genres AS (
            SELECT DISTINCT 
                r.customer_id, 
                c.name AS genre
            FROM pg.public.rental r
            JOIN pg.public.inventory i ON r.inventory_id = i.inventory_id
            JOIN pg.public.film f ON i.film_id = f.film_id
            JOIN pg.public.film_category fc ON f.film_id = fc.film_id
            JOIN pg.public.category c ON fc.category_id = c.category_id
        )
        SELECT 
            cg1.genre AS genre_A,
            cg2.genre AS genre_B,
            COUNT(DISTINCT cg1.customer_id) AS pair_customer_count
        FROM customer_genres cg1
        JOIN customer_genres cg2 ON cg1.customer_id = cg2.customer_id AND cg1.genre < cg2.genre
        GROUP BY genre_A, genre_B
        ORDER BY pair_customer_count DESC
    """
    
    query_total_customers = "SELECT COUNT(DISTINCT customer_id) AS total_customers FROM pg.public.rental;"
    query_genre_counts = """
        SELECT c.name AS genre, COUNT(DISTINCT r.customer_id) AS genre_customer_count
        FROM pg.public.rental r
        JOIN pg.public.inventory i ON r.inventory_id = i.inventory_id
        JOIN pg.public.film_category fc ON i.film_id = fc.film_id
        JOIN pg.public.category c ON fc.category_id = c.category_id
        GROUP BY genre
    """

    try:
        pairs_df = con.execute(query_genre_pairs).pl()
        total_cust = con.execute(query_total_customers).fetchone()[0]
        genre_counts_df = con.execute(query_genre_counts).pl()

        # Join single genre counts to compute Support, Confidence, Lift
        genre_count_map = dict(zip(genre_counts_df["genre"], genre_counts_df["genre_customer_count"]))

        records = []
        for row in pairs_df.iter_rows(named=True):
            gA = row["genre_A"]
            gB = row["genre_B"]
            pair_cnt = row["pair_customer_count"]

            cnt_A = genre_count_map.get(gA, 1)
            cnt_B = genre_count_map.get(gB, 1)

            support_AB = pair_cnt / total_cust
            support_A = cnt_A / total_cust
            support_B = cnt_B / total_cust

            confidence_A_B = pair_cnt / cnt_A
            confidence_B_A = pair_cnt / cnt_B

            lift = support_AB / (support_A * support_B) if (support_A * support_B) > 0 else 0

            records.append({
                "Antecedent (Genre A)": gA,
                "Consequent (Genre B)": gB,
                "Pair Count": pair_cnt,
                "Support": round(support_AB, 4),
                "Confidence (A->B)": round(confidence_A_B, 4),
                "Confidence (B->A)": round(confidence_B_A, 4),
                "Lift": round(lift, 2)
            })

        rules_df = pl.DataFrame(records).sort("Lift", descending=True)
        return rules_df, pairs_df
    except Exception as e:
        st.error(f"Error performing Market Basket Analysis: {e}")
        return pl.DataFrame(), pl.DataFrame()


# ==========================================
# 🤖 SUPERVISED MACHINE LEARNING MODELS
# ==========================================

@st.cache_resource
def train_demand_model(df_data: pl.DataFrame):
    """Supervised Regression: RandomForestRegressor for predicting lifetime rental demand."""
    if df_data.is_empty() or len(df_data) < 10:
        return None, 0.0, 0.0, []

    features = ["length", "rental_rate", "replacement_cost"]
    target = "total_rentals"

    X = df_data.select(features).to_numpy()
    y = df_data.select(target).to_numpy().ravel()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mse = float(mean_squared_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))

    return model, r2, mse, features


@st.cache_resource
def train_customer_churn_classifier(df_rfm: pl.DataFrame):
    """
    Supervised Classification: RandomForestClassifier for predicting customer churn risk.
    Returns: (model, accuracy, precision, recall, roc_auc, conf_matrix, feature_names)
    """
    if df_rfm.is_empty() or len(df_rfm) < 20:
        return None, 0.0, 0.0, 0.0, 0.0, None, []

    features = ["rental_count", "total_spend", "avg_ticket_value"]
    target = "churn_risk_label"

    X = df_rfm.select(features).to_numpy()
    y = df_rfm.select(target).to_numpy().ravel()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, preds))
    prec = float(precision_score(y_test, preds, zero_division=0))
    rec = float(recall_score(y_test, preds, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, probs))
    cm = confusion_matrix(y_test, preds)

    return model, acc, prec, rec, roc_auc, cm, features


@st.cache_resource
def train_overdue_risk_classifier(df_ops: pl.DataFrame):
    """
    Supervised Classification: GradientBoostingClassifier for predicting overdue return risk on transactions.
    Returns: (model, accuracy, precision, recall, roc_auc, feature_names)
    """
    if df_ops.is_empty() or len(df_ops) < 20:
        return None, 0.0, 0.0, 0.0, 0.0, []

    features = ["length", "rental_rate", "replacement_cost", "allowed_days"]
    target = "is_overdue"

    X = df_ops.select(features).to_numpy()
    y = df_ops.select(target).to_numpy().ravel()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, preds))
    prec = float(precision_score(y_test, preds, zero_division=0))
    rec = float(recall_score(y_test, preds, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, probs))

    return model, acc, prec, rec, roc_auc, features

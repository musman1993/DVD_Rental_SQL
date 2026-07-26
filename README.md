# 🎬 PostgreSQL DVD Rental Intelligence, Market Basket & Supervised ML Platform

An enterprise-grade, multi-container analytics & machine learning portal powered by **PostgreSQL 17**, **DuckDB**, **Polars**, **Plotly**, **scikit-learn**, and **Streamlit**.

---

## 🏗️ Architecture & ML Stack Overview

* **Database Layer**: PostgreSQL 17 running inside a containerized setup (`dvdrental-db`) with automatic database restoration on boot.
* **Analytics Engine**: High-performance OLAP engine using **DuckDB**'s PostgreSQL attachment scanner and **Polars** zero-copy dataframes.
* **Interactive UI**: Multi-page **Streamlit** application (`dvdrental-app`) with aggressive cyber-dark styling (`#0F172A`), neon metric cards, and interactive Plotly visualizations.
* **Supervised Machine Learning & Data Mining**:
  * 🛒 **Market Basket Analysis**: Association rule mining (Support, Confidence, Lift) for genre co-rentals and cross-category affinity matrices.
  * 🎯 **Supervised Customer Churn Classifier**: `RandomForestClassifier` for churn/inactivity risk with interactive calculators, confusion matrices, and ROC-AUC metrics.
  * ⏰ **Supervised Overdue Return Risk Model**: `GradientBoostingClassifier` predicting rental delay risk on transactions.
  * 📈 **Supervised Film Demand Regressor**: `RandomForestRegressor` for forecasting lifetime film rentals.
* **Container Orchestration**: Production-ready **Docker Compose** mesh (`db` + `app` services with `service_healthy` startup conditions).

---

## 📂 Project Directory Structure

```
Postgres_DB_DVDRental/
├── README.md                      # Comprehensive project guide
├── Makefile                       # Make automation commands (up, down, status, logs, connect)
├── docker-compose.yml             # Multi-container Compose orchestration
├── .env / .env.example            # Environment variables configuration
├── pyproject.toml / uv.lock       # Python package dependencies & lockfile
│
├── app.py                         # Root Streamlit Executive & ML Portal
├── pages/                         # Streamlit multi-page navigation
│   ├── 1_📦_Supply_Chain.py       # Inventory & replacement cost asset matrix
│   ├── 2_📢_Marketing.py          # Customer RFM & 80/20 revenue Pareto chart
│   ├── 3_⚙️_Operations.py         # Traffic activity heatmap & store turnaround
│   ├── 4_🧠_Predictive_Modeling.py # Demand forecasting simulator
│   ├── 5_🛒_Market_Basket_Analysis.py # Support/Confidence/Lift association rules
│   └── 6_🤖_Supervised_Machine_Learning.py # Churn, Overdue, and Demand ML Suite
├── utils/                         # Modular application engine
│   ├── db_pipeline.py             # DuckDB connection caching, Polars ETL, & ML model fitting
│   └── ui_theme.py                # Cyber-dark CSS, Plotly themes, & chart components
├── app/                           # Container build context for Streamlit service
│   └── Dockerfile                 # Multi-stage Dockerfile with pre-installed DuckDB extension
│
├── docs/                          # Architecture & infrastructure documentation
├── sql/                           # SQL practice & reference scripts
├── notebooks/                     # Data exploration & analysis notebooks
├── postgres-setup/                # PostgreSQL container build & restoration script
└── archives/                      # Legacy archives & dbt transform packages
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Docker** & **Colima** (macOS): `brew install colima docker`

### 1. Launch the Full Containerized Stack
```bash
make up
```
This command starts Colima (if not running), builds both Docker images, restores the PostgreSQL `dvdrental` database, and launches the Streamlit app.

### 2. Access the Application
Open your browser to: **[http://localhost:8501](http://localhost:8501)**

### 3. Management & Diagnostic Commands
```bash
make status      # Check container status and health
make logs        # View live logs from all services
make connect     # Connect directly to psql inside the database container
make down        # Stop the stack
make clean       # Stop stack and remove volumes/containers
```

---

## 🤖 Registered Agents & Skills

The project includes specialized subagents and agent skills in `.agents/skills/`:
* 🧪 **`quality_assurance`**: Audits data pipeline reliability, connection caching, type safety, and error handling.
* 📊 **`data_visualization`**: Designs interactive Plotly charts, dark-mode themes, and glassmorphic layout components.
* 🔮 **`dashboard_creator`**: Extends analytical features, SQL queries, and Streamlit pages ([`dashboard-creator`](file://.agents/skills/dashboard-creator/SKILL.md)).
* 🛠️ **`data_engineer`**: Manages ETL pipelines, DuckDB/Polars workflows, dbt transformations, and Docker Compose stack migrations ([`data-engineer`](file://.agents/skills/data-engineer/SKILL.md)).

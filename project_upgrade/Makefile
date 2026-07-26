.PHONY: help colima-start colima-stop up down restart build logs logs-db logs-app \
        status health connect app-shell db-shell clean reset env \
        dbt-deps dbt-run dbt-test dbt-docs

# Configuration — these back Compose's ${VAR:-default} substitutions via .env
POSTGRES_USER?=postgres
POSTGRES_PASSWORD?=postgres
POSTGRES_DB?=dvdrental
HOST_PORT?=5432

DBT_PROJECT_DIR=dbt_dvdrental
DBT_PROFILES_DIR=dbt_dvdrental

# Colors
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
NC=\033[0m

help:
	@echo "$(BLUE)DVD Rental Analytics Stack - Make Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Colima Management:$(NC)"
	@echo "  make colima-start        Start Colima VM"
	@echo "  make colima-stop         Stop Colima VM"
	@echo ""
	@echo "$(GREEN)Stack Management (Postgres + Streamlit/DuckDB app):$(NC)"
	@echo "  make up                  Build and start the full stack, detached"
	@echo "  make down                Stop and remove containers (data volume kept)"
	@echo "  make restart             down + up"
	@echo "  make build               Rebuild images without starting containers"
	@echo ""
	@echo "$(GREEN)Observability:$(NC)"
	@echo "  make status              Show status of both services"
	@echo "  make health              Check health of both services"
	@echo "  make logs                Tail logs from both services"
	@echo "  make logs-db             Tail Postgres logs only"
	@echo "  make logs-app            Tail Streamlit app logs only"
	@echo ""
	@echo "$(GREEN)Access:$(NC)"
	@echo "  make connect             psql shell into the db container"
	@echo "  make db-shell            bash shell into the db container"
	@echo "  make app-shell           bash shell into the app container"
	@echo ""
	@echo "$(GREEN)dbt (runs from host via uv, against the published Postgres port):$(NC)"
	@echo "  make dbt-deps            Install dbt packages (dbt_utils)"
	@echo "  make dbt-run             Build staging + mart models"
	@echo "  make dbt-test            Run schema + singular tests"
	@echo "  make dbt-docs            Generate and serve the dbt docs site"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean               Remove containers + images (data volume kept)"
	@echo "  make reset               Full reset: containers, images, AND the data volume"

# --- Colima ---
colima-start:
	@echo "$(BLUE)Starting Colima...$(NC)"
	@colima start || true
	@sleep 2
	@echo "$(GREEN)✓ Colima ready$(NC)"

colima-stop:
	@colima stop

# --- Stack lifecycle ---
# Every target below depends on colima-start, same pattern as before: Make
# guarantees the VM is up before any docker/docker-compose command runs.

build: colima-start
	@echo "$(BLUE)Building images...$(NC)"
	@docker compose build
	@echo "$(GREEN)✓ Images built$(NC)"

up: colima-start
	@echo "$(BLUE)Starting full stack (db + app)...$(NC)"
	@docker compose up --build -d
	@echo ""
	@echo "$(GREEN)✓ Stack starting.$(NC) Postgres becomes healthy first, then the app starts automatically."
	@echo "  Streamlit:  http://localhost:8501"
	@echo "  Postgres:   localhost:$(HOST_PORT)"
	@echo ""
	@echo "  Run '$(YELLOW)make status$(NC)' in a few seconds to confirm both are healthy."

down:
	@docker compose down
	@echo "$(GREEN)✓ Stack stopped (data volume preserved)$(NC)"

restart: down up

# --- Observability ---
status:
	@docker compose ps

health:
	@echo "$(BLUE)Service health (from Docker's own HEALTHCHECK status):$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}"

logs:
	@docker compose logs -f

logs-db:
	@docker compose logs -f db

logs-app:
	@docker compose logs -f app

# --- Access ---
connect:
	@docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

db-shell:
	@docker compose exec db sh

app-shell:
	@docker compose exec app bash

# --- dbt ---
# dbt runs from the HOST, not inside a container, and connects to Postgres
# via the port docker-compose publishes to localhost. This mirrors how dbt
# is actually used in practice (a CLI tool run from a dev machine or CI
# runner against a warehouse) rather than baking it into either image.
dbt-deps:
	@uv run dbt deps --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-run:
	@POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) POSTGRES_DB=$(POSTGRES_DB) \
		uv run dbt run --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-test:
	@POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) POSTGRES_DB=$(POSTGRES_DB) \
		uv run dbt test --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-docs:
	@POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) POSTGRES_DB=$(POSTGRES_DB) \
		uv run dbt docs generate --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)
	@uv run dbt docs serve --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

# --- Cleanup ---
clean:
	@docker compose down --rmi local
	@echo "$(GREEN)✓ Containers and locally-built images removed (volume kept)$(NC)"

reset: colima-stop
	@docker compose down -v --rmi all
	@echo "$(GREEN)✓ Full reset: containers, images, and the data volume are gone$(NC)"

env:
	@echo "$(BLUE)Current Environment:$(NC)"
	@echo "  User: $(POSTGRES_USER)"
	@echo "  Database: $(POSTGRES_DB)"
	@echo "  Port: $(HOST_PORT)"

.DEFAULT_GOAL := help

.PHONY: help up down restart logs status connect clean reset colima-start colima-stop

# Colors
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
NC=\033[0m

help:
	@echo "$(BLUE)DVD Rental PostgreSQL & Streamlit Stack - Make Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Compose Stack Management:$(NC)"
	@echo "  make up                  Start both PostgreSQL and Streamlit containers"
	@echo "  make down                Stop all Compose services"
	@echo "  make restart             Restart Compose stack"
	@echo "  make logs                View Compose service logs"
	@echo "  make status              Check running containers & health"
	@echo ""
	@echo "$(GREEN)Colima Management:$(NC)"
	@echo "  make colima-start        Start Colima VM"
	@echo "  make colima-stop         Stop Colima VM"
	@echo ""
	@echo "$(GREEN)Database Access & Cleanup:$(NC)"
	@echo "  make connect             Connect to PostgreSQL via container psql"
	@echo "  make clean               Stop stack and remove containers"
	@echo "  make reset               Full system prune reset"

colima-start:
	@echo "$(BLUE)Starting Colima...$(NC)"
	@colima start || true
	@echo "$(GREEN)✓ Colima started$(NC)"

colima-stop:
	@echo "$(BLUE)Stopping Colima...$(NC)"
	@colima stop
	@echo "$(GREEN)✓ Colima stopped$(NC)"

up: colima-start
	@echo "$(BLUE)Bringing up multi-container Docker Compose stack...$(NC)"
	@docker compose up --build -d
	@echo "$(GREEN)✓ Services started! Streamlit app: http://localhost:8501$(NC)"

down:
	@echo "$(BLUE)Stopping Docker Compose stack...$(NC)"
	@docker compose down

restart: down up

logs:
	@docker compose logs -f

status:
	@echo "$(BLUE)Container Status:$(NC)"
	@docker compose ps

connect:
	@echo "$(BLUE)Connecting to PostgreSQL database...$(NC)"
	@docker exec -it dvdrental-db psql -U postgres -d dvdrental

clean: down
	@echo "$(BLUE)Cleaning containers and volumes...$(NC)"
	@docker compose down -v --remove-orphans
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

reset: clean colima-stop
	@echo "$(BLUE)Full reset complete$(NC)"

.DEFAULT_GOAL := help

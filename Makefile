.PHONY: help colima-start colima-stop build run stop logs clean connect status env-file

# Configuration
DOCKER_IMAGE_NAME=dvdrental-postgres
DOCKER_CONTAINER_NAME=dvdrental-db
POSTGRES_USER?=postgres
POSTGRES_PASSWORD?=postgres
POSTGRES_DB?=dvdrental
DB_PORT?=5432
HOST_PORT?=5432

# Colors for output
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
NC=\033[0m # No Color

help:
	@echo "$(BLUE)DVD Rental PostgreSQL Database - Make Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Colima Management:$(NC)"
	@echo "  make colima-start        Start Colima VM"
	@echo "  make colima-stop         Stop Colima VM"
	@echo "  make colima-status       Check Colima status"
	@echo ""
	@echo "$(GREEN)Container Management:$(NC)"
	@echo "  make build               Build Docker image"
	@echo "  make run                 Build and run container"
	@echo "  make stop                Stop running container"
	@echo "  make restart             Restart container"
	@echo "  make status              Check container status"
	@echo ""
	@echo "$(GREEN)Health Checks:$(NC)"
	@echo "  make health              Full health check (container + DB)"
	@echo "  make health-quick        Quick container status"
	@echo "  make health-db           Check database connection"
	@echo ""
	@echo "$(GREEN)Database Access:$(NC)"
	@echo "  make connect             Connect to PostgreSQL database"
	@echo "  make logs                View container logs"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean               Remove container and image"
	@echo "  make reset               Full reset (Colima, containers, images)"
	@echo ""
	@echo "$(YELLOW)Environment Variables:$(NC)"
	@echo "  POSTGRES_USER=$(POSTGRES_USER)"
	@echo "  POSTGRES_PASSWORD=$(POSTGRES_PASSWORD)"
	@echo "  POSTGRES_DB=$(POSTGRES_DB)"
	@echo "  HOST_PORT=$(HOST_PORT)"

# Colima commands
colima-status:
	@colima status 2>/dev/null || echo "$(RED)Colima is not running$(NC)"

colima-start:
	@echo "$(BLUE)Starting Colima...$(NC)"
	@colima start || true
	@echo "$(GREEN)✓ Colima started$(NC)"
	@sleep 2

colima-stop:
	@echo "$(BLUE)Stopping Colima...$(NC)"
	@colima stop
	@echo "$(GREEN)✓ Colima stopped$(NC)"

# Docker image building
build: colima-start
	@echo "$(BLUE)Building Docker image: $(DOCKER_IMAGE_NAME)$(NC)"
	@cd postgres-setup && docker build -t $(DOCKER_IMAGE_NAME):latest .
	@echo "$(GREEN)✓ Image built successfully$(NC)"

# Container management
run: build
	@echo "$(BLUE)Stopping existing container if running...$(NC)"
	@docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@echo "$(BLUE)Starting PostgreSQL container...$(NC)"
	@docker run -d \
		--name $(DOCKER_CONTAINER_NAME) \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		-p $(HOST_PORT):$(DB_PORT) \
		-v dvdrental-volume:/var/lib/postgresql/data \
		$(DOCKER_IMAGE_NAME):latest
	@echo "$(GREEN)✓ Container started$(NC)"
	@sleep 3
	@echo ""
	@echo "$(GREEN)Connection Details:$(NC)"
	@echo "  Host: localhost"
	@echo "  Port: $(HOST_PORT)"
	@echo "  User: $(POSTGRES_USER)"
	@echo "  Password: $(POSTGRES_PASSWORD)"
	@echo "  Database: $(POSTGRES_DB)"
	@echo ""

stop:
	@echo "$(BLUE)Stopping container...$(NC)"
	@docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || echo "$(YELLOW)Container not running$(NC)"
	@echo "$(GREEN)✓ Container stopped$(NC)"

restart: stop run
	@echo "$(GREEN)✓ Container restarted$(NC)"

status:
	@echo "$(BLUE)Colima Status:$(NC)"
	@colima status 2>/dev/null || echo "$(YELLOW)Not running$(NC)"
	@echo ""
	@echo "$(BLUE)Container Status:$(NC)"
	@docker ps --filter name=$(DOCKER_CONTAINER_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "$(YELLOW)No containers running$(NC)"

# Database access
connect: status
	@echo "$(BLUE)Connecting to PostgreSQL...$(NC)"
	@PGPASSWORD=$(POSTGRES_PASSWORD) psql -h localhost -p $(HOST_PORT) -U $(POSTGRES_USER) -d $(POSTGRES_DB)

logs:
	@docker logs -f $(DOCKER_CONTAINER_NAME)

# Health checks
health: 
	@echo "$(BLUE)Checking Container Health...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Container Status:$(NC)"
	@docker inspect $(DOCKER_CONTAINER_NAME) --format='{{.State.Status}}' 2>/dev/null || echo "$(RED)Container not found$(NC)"
	@echo ""
	@echo "$(BLUE)2. Container Uptime:$(NC)"
	@docker inspect $(DOCKER_CONTAINER_NAME) --format='Started: {{.State.StartedAt}}' 2>/dev/null || echo "$(YELLOW)N/A$(NC)"
	@echo ""
	@echo "$(BLUE)3. Database Connection Test:$(NC)"
	@PGPASSWORD=$(POSTGRES_PASSWORD) psql -h localhost -p $(HOST_PORT) -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT version();" 2>/dev/null && echo "$(GREEN)✓ Database is responding$(NC)" || echo "$(RED)✗ Cannot connect to database$(NC)"
	@echo ""
	@echo "$(BLUE)4. Memory Usage:$(NC)"
	@docker inspect $(DOCKER_CONTAINER_NAME) --format='{{.State.Pid}}' 2>/dev/null | xargs -I {} sh -c 'ps -o %mem= -p {} 2>/dev/null || echo "N/A"' || echo "N/A"
	@echo ""
	@echo "$(BLUE)5. Recent Logs:$(NC)"
	@docker logs --tail 5 $(DOCKER_CONTAINER_NAME) 2>/dev/null | sed 's/^/  /'

health-quick:
	@docker ps --filter name=$(DOCKER_CONTAINER_NAME) --format "{{.Status}}" | grep -q running && echo "$(GREEN)✓ Container is running$(NC)" || echo "$(RED)✗ Container is not running$(NC)"

health-db:
	@PGPASSWORD=$(POSTGRES_PASSWORD) psql -h localhost -p $(HOST_PORT) -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT datname, pg_database.oid FROM pg_database WHERE datname = '$(POSTGRES_DB)'" 2>/dev/null && echo "" && echo "$(GREEN)✓ Database is healthy$(NC)" || echo "$(RED)✗ Database connection failed$(NC)"

# Cleanup
clean: stop
	@echo "$(BLUE)Removing container and image...$(NC)"
	@docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE_NAME):latest 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

reset: colima-stop clean
	@echo "$(BLUE)Full reset: removing all containers, images, and volumes...$(NC)"
	@docker system prune -af --volumes
	@echo "$(GREEN)✓ Full reset complete$(NC)"

# Helper target - show environment
env:
	@echo "$(BLUE)Current Environment:$(NC)"
	@echo "  Image: $(DOCKER_IMAGE_NAME)"
	@echo "  Container: $(DOCKER_CONTAINER_NAME)"
	@echo "  User: $(POSTGRES_USER)"
	@echo "  Database: $(POSTGRES_DB)"
	@echo "  Port: $(HOST_PORT)"

.DEFAULT_GOAL := help

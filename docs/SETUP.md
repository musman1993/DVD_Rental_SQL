# PostgreSQL DVD Rental Database Setup

## Prerequisites

1. **Colima** - Install with Homebrew:
   ```bash
   brew install colima
   ```

2. **Docker** - Install from Docker Desktop or via Homebrew:
   ```bash
   brew install docker
   ```

3. **psql** (PostgreSQL client) - Optional, for connecting to the database:
   ```bash
   brew install libpq
   ```

## Quick Start

### 1. Start Colima
```bash
make colima-start
```

### 2. Build and Run the Container
```bash
make run
```

This will:
- ✓ Start Colima (if not running)
- ✓ Build the Docker image
- ✓ Start the PostgreSQL container
- ✓ Display connection details

### 3. Connect to the Database
```bash
make connect
```

Or use any PostgreSQL client:
```bash
psql -h localhost -p 5432 -U postgres -d dvdrental
```

## Common Commands

| Command | Description |
|---------|-------------|
| `make run` | Build and start the container |
| `make stop` | Stop the container |
| `make restart` | Restart the container |
| `make logs` | View container logs |
| `make status` | Check Colima and container status |
| `make clean` | Remove container and image |
| `make reset` | Full reset (Colima, containers, images) |
| `make help` | Show all available commands |

## Customization

### Using Different Credentials

You can pass environment variables:

```bash
make run POSTGRES_USER=myuser POSTGRES_PASSWORD=mypass POSTGRES_DB=mydb HOST_PORT=5433
```

Or create a `.env` file from `.env.example` and modify it:

```bash
cp .env.example .env
# Edit .env with your values
make run
```

## Troubleshooting

### Container won't start
```bash
make logs  # Check the error messages
make clean # Remove and rebuild
make run   # Try again
```

### Can't connect to database
1. Check if Colima is running: `make colima-status`
2. Check if container is running: `make status`
3. Verify port mapping: `docker ps`
4. Try restarting: `make restart`

### Colima won't start
```bash
colima status  # Check current state
colima delete  # Reset if needed
colima start   # Start fresh
```

## Files Structure

```
.
├── Makefile                      # Docker & Colima management
├── .env.example                  # Environment configuration template
├── sql-learning.sql              # Your SQL scripts
└── postgres-setup/
    ├── dockerfile                # Docker image configuration
    ├── import-data.sh            # Data restoration script
    └── dvdrental.tar             # PostgreSQL backup
```

## Notes

- Data persists in Docker volume `dvdrental-volume`
- Default credentials: `postgres` / `postgres`
- Database: `dvdrental`
- Port: `5432` (configurable)

## Clean Up

To completely remove everything:
```bash
make reset
make colima-stop
```

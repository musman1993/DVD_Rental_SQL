# Migration Guide — Compose-based Stack Upgrade

## What changed and why

Before: Postgres ran in Docker (via Colima + a single `docker run`), while
the Streamlit/DuckDB app ran bare on your Mac via `uv run streamlit run app.py`.
Two different execution environments for one project — the app's behavior on
your machine wasn't guaranteed to match its behavior anywhere else.

After: both services run in Docker, orchestrated by Compose, brought up with
one command (`make up`), with the app container only starting once Postgres
is confirmed healthy (not just "the container process exists" — see the
`depends_on: condition: service_healthy` comment in docker-compose.yml).

## Where each file goes in your existing repo

```
.
├── Makefile                  <- REPLACE with the new one
├── docker-compose.yml        <- NEW, add at repo root
├── .env.example               <- NEW, add at repo root
├── pyproject.toml            <- REPLACE (adds dbt-postgres)
├── app.py                    <- REPLACE (env-driven connection, parameterized query)
├── app/
│   └── Dockerfile            <- NEW folder + file
├── postgres-setup/
│   ├── dockerfile             <- UNCHANGED, leave as-is
│   ├── import-data.sh         <- UNCHANGED, leave as-is
│   └── dvdrental.tar          <- UNCHANGED, leave as-is
└── dbt_dvdrental/             <- from the earlier dbt deliverable, UNCHANGED
```

## Steps to apply

1. Drop `app/Dockerfile`, `docker-compose.yml`, and `.env.example` into place.
2. Overwrite `Makefile`, `pyproject.toml`, and `app.py` with the new versions.
3. `cp .env.example .env` (Compose auto-loads `.env` — this is where you'd
   override credentials without touching docker-compose.yml).
4. Regenerate your lockfile since `pyproject.toml` gained a dependency:
   ```bash
   uv lock
   ```
5. Bring the whole stack up:
   ```bash
   make up
   ```
   First run will be slower (building both images, restoring the dvdrental
   data). Subsequent runs reuse Docker's layer cache and the named volume.
6. Check both services:
   ```bash
   make status
   ```
7. Open the app: http://localhost:8501

## Running dbt against this stack

dbt still runs from your host machine (not inside a container — see the
comment block in the Makefile for why), against the Postgres port Compose
publishes to `localhost`:

```bash
make dbt-deps
make dbt-run
make dbt-test
```

## Old workflow vs new

| Old | New |
|---|---|
| `make run` (Postgres only) | `make up` (Postgres + app) |
| `uv run streamlit run app.py` (separate step) | app starts automatically as part of `make up` |
| `make connect` used local `psql` | `make connect` now runs `psql` *inside* the db container — no local `psql` install required at all |
| Single-container health checks | `make health` reports both services |

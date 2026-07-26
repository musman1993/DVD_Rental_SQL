# app/Dockerfile
# Build context is the REPO ROOT (not app/), so this can COPY pyproject.toml
# and uv.lock from the top level. Build with:
#   docker build -f app/Dockerfile -t dvdrental-app .
# (docker-compose.yml already points at this correctly — see below.)

# ---- Stage 1: resolve dependencies with uv ----
FROM python:3.14-slim AS builder

# Pull the uv binary directly from its official distroless image rather than
# pip-installing it — faster, and keeps uv itself out of the final image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy ONLY the dependency manifests first. Docker caches each layer by the
# hash of its inputs — as long as pyproject.toml/uv.lock don't change, this
# layer (and the slow `uv sync`) is reused even if app.py changes constantly.
COPY pyproject.toml uv.lock ./

# --frozen: install exactly what's in uv.lock, fail loudly if it's stale
#           instead of silently re-resolving (this is what makes the build
#           reproducible rather than "whatever the latest compatible version is today")
# --no-install-project: install the dependency set only; this project has
#           no installable package of its own (it's an app, not a library)
# --no-dev: skip any dev-only dependency group, keeping the runtime image lean
RUN uv sync --frozen --no-install-project --no-dev

# ---- Stage 2: runtime image ----
FROM python:3.14-slim

WORKDIR /app

# Bring in only the resolved virtual environment from the builder stage —
# not uv, not pip caches, not build tooling. This is the main payoff of a
# multi-stage build: a smaller, more auditable final image.
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Pre-install the DuckDB "postgres" extension AT BUILD TIME.
# Without this, app.py's own `con.execute("INSTALL postgres;")` call has to
# reach extensions.duckdb.org over the network on first run inside the
# container — an avoidable startup delay and an avoidable failure mode if
# that container ever runs somewhere without outbound internet access.
# Baking it in means the extension ships as part of the image itself.
RUN python -c "import duckdb; con = duckdb.connect(); con.execute('INSTALL postgres;')"

COPY app.py .

EXPOSE 8501

# Streamlit exposes a built-in health endpoint at /_stcore/health specifically
# for cases like this — no need to hand-roll a readiness probe.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# --server.address=0.0.0.0 is required inside a container — Streamlit's
# default binds to localhost, which would be unreachable from outside the
# container even with the port published.
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

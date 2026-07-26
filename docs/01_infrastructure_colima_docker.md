# 01 — Local Infrastructure: Colima, Docker & the Makefile

This document covers the foundation layer of the project: how a Postgres
database ends up running locally, why each piece of tooling is there, and
what's actually happening under the hood when you run `make run`.

---

## 1. Why Colima exists at all

Docker containers are Linux processes — they share the host machine's Linux
kernel for namespacing and cgroups instead of virtualizing a full OS. That's
what makes them lightweight compared to a VM.

The problem: macOS doesn't run a Linux kernel. So "Docker on Mac" has never
actually been Docker running natively — it's always been Docker's daemon
running *inside a lightweight Linux VM*, with the CLI on your Mac talking to
that VM over a socket. Docker Desktop bundles this VM (based on a hypervisor
like HyperKit or Apple's Virtualization framework) along with a GUI, licensing
for commercial use, and a bunch of extra tooling most people don't touch.

**Colima** (COntainers on LIMA) strips this down to just the VM part. It uses
[Lima](https://github.com/lima-vm/lima) to spin up a minimal Linux VM (via
QEMU or Apple's native Virtualization.framework on Apple Silicon), installs a
container runtime inside it (`containerd` by default, though it can also run
`dockerd`), and exposes the Docker socket back to your Mac so the regular
`docker` CLI works exactly as if Docker Desktop were installed.

Why this project uses it instead of Docker Desktop:
- No license concerns (Docker Desktop requires a paid license for larger
  companies; Colima is Apache-2.0, free regardless of use case).
- Lower resource overhead — no GUI process, smaller default VM footprint.
- Fully scriptable from the terminal, which matters for `make colima-start`
  being a dependency of `make build` (see §3) — there's no "open the app and
  wait for the whale icon" step that can't be automated.

`colima start` provisions the VM on first run (allocating CPU/memory/disk per
its defaults or your `~/.colima/default/colima.yaml` config) and boots it;
subsequent calls just start an already-provisioned VM, which is why it's fast
after the first run.

---

## 2. Why containerize Postgres instead of installing it natively

You could `brew install postgresql@17` and run it directly on macOS. The
project uses a container instead for a few concrete reasons:

- **Reproducibility.** The dockerfile pins `postgres:17-alpine` exactly. Six
  months from now, `make run` produces the *same* Postgres minor version and
  base OS, regardless of what's changed on your Mac. A native install drifts
  with whatever `brew upgrade` does over time.
- **Disposability.** `make clean` / `make reset` can nuke the entire database
  and rebuild it from scratch in seconds, because the state lives in a Docker
  volume, not scattered across `/opt/homebrew` or `/usr/local`.
- **Portability of the whole project.** Anyone who clones this repo runs the
  exact same environment you built it in — no "works on my machine" gap
  caused by a different locally-installed Postgres version.
- **Isolation.** It doesn't collide with any other Postgres instance you might
  already have running locally for a different project.

---

## 3. The Makefile, target by target

The Makefile is the operational interface to the whole stack — it wraps raw
`colima` and `docker` commands into named, composable targets so you don't
have to remember flags.

### Configuration block

```make
DOCKER_IMAGE_NAME=dvdrental-postgres
DOCKER_CONTAINER_NAME=dvdrental-db
POSTGRES_USER?=postgres
POSTGRES_PASSWORD?=postgres
POSTGRES_DB?=dvdrental
DB_PORT?=5432
HOST_PORT?=5432
```

The `?=` operator is a **conditional assignment** — it only sets the variable
if it isn't already set. This is what makes the documented override pattern
work:

```bash
make run POSTGRES_USER=myuser POSTGRES_PASSWORD=mypass HOST_PORT=5433
```

Make treats command-line arguments like `VAR=value` as pre-set variables, so
the `?=` inside the file backs off and lets your override win. Without `?=`
(i.e. plain `=`), the file's value would always clobber your CLI override.

### `colima-start`

```make
colima-start:
	@colima start || true
	@sleep 2
```

Two details worth understanding:
- `|| true` — if Colima is already running, `colima start` exits non-zero
  (it refuses to start twice). Without `|| true`, Make would treat that as a
  failed command and abort the whole chain (`build` depends on this target).
  The `|| true` makes "already running" a non-fatal, expected outcome.
- `sleep 2` — gives the VM's internal Docker socket a moment to become
  reachable before the next target tries to run `docker build` against it.
  This is a pragmatic fixed delay rather than a proper readiness poll —
  fine for local dev, but worth knowing as a limitation if you ever see a
  flaky "cannot connect to the Docker daemon" error right after a cold start.

### `build`

```make
build: colima-start
	@cd postgres-setup && docker build -t $(DOCKER_IMAGE_NAME):latest .
```

`build: colima-start` is a **Make dependency** — Make will always run
`colima-start` first, every time you run `make build`, before executing
`build`'s own recipe. This is how the Makefile guarantees the VM is up before
touching Docker, without you having to remember to do it manually.

`docker build -t name:latest .` reads the `Dockerfile` in the current
directory, executes each instruction as a layer (see doc 02 for what those
instructions actually do), and tags the resulting image `dvdrental-postgres:latest`.

### `run`

```make
run: build
	@docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@docker run -d \
		--name $(DOCKER_CONTAINER_NAME) \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		-p $(HOST_PORT):$(DB_PORT) \
		-v dvdrental-volume:/var/lib/postgresql/data \
		$(DOCKER_IMAGE_NAME):latest
```

Step by step:
1. `run: build` — chains the whole pipeline: Colima → image build → container
   start, all from one command.
2. The `stop`/`rm` lines are a **cleanup-before-create** pattern. Docker won't
   let you `docker run` a container with a name that's already taken by an
   existing (even stopped) container, so this guarantees `make run` is
   idempotent — safe to run repeatedly without manual cleanup.
3. `-d` — detached mode; the container runs in the background instead of
   attaching your terminal to its stdout.
4. `-e` flags — inject environment variables into the container. The official
   `postgres` image's entrypoint script reads `POSTGRES_USER`,
   `POSTGRES_PASSWORD`, and `POSTGRES_DB` on **first initialization only**
   (when the data directory is empty) to bootstrap the default role and
   database. Setting these post-first-run has no effect until the volume is
   wiped.
5. `-p $(HOST_PORT):$(DB_PORT)` — maps host port to container port
   (`host:container`). This is what makes `localhost:5432` on your Mac
   actually reach Postgres running inside the Linux VM inside the container.
6. `-v dvdrental-volume:/var/lib/postgresql/data` — this is the single most
   important line for data persistence. `/var/lib/postgresql/data` is where
   Postgres stores its actual data files inside the container. Without a
   volume, that directory lives in the container's writable layer, which is
   **destroyed** when the container is removed (`docker rm`). By mounting a
   **named volume** (`dvdrental-volume`, managed by Docker, stored on the
   Colima VM's disk) at that path, the data outlives the container itself —
   you can `docker rm` and recreate the container and the data is still
   there, because it lives in the volume, not the container.

This also explains a subtlety worth knowing: `make clean` removes the
container and image but **not** the volume — so `make run` after `make clean`
will restore instantly from the existing volume without re-running
`import-data.sh` at all (see doc 02, §2, on why the restore script is
idempotent). Only `make reset`, via `docker system prune -af --volumes`,
actually wipes the volume and forces a fresh restore.

### `status`, `health`, `health-quick`, `health-db`

These are read-only diagnostic targets built on `docker inspect`, `docker ps`,
and `psql`:

- `status` — lists Colima state and any running container matching the name
  filter, using Go template formatting (`--format "table {{.Names}}..."`) to
  print a clean table instead of raw JSON.
- `health` — a five-part deeper check: container state, uptime (parsed from
  `docker inspect`'s `State.StartedAt`), an actual `SELECT version();` query
  to confirm Postgres itself (not just the container) is responsive, memory
  usage via reading the container's host PID and querying `ps`, and the last
  5 log lines for quick triage.
- `health-db` — narrower: just confirms the target database exists in
  `pg_database`, which is a different failure mode than "container running
  but Postgres still starting up" or "container running but wrong DB name."

The distinction between `health-quick` (is the container up) and `health-db`
(is *this specific database* queryable) matters in practice — a container can
be `Up` while Postgres is still replaying WAL or still running
`import-data.sh` inside `docker-entrypoint-initdb.d`, so `docker ps` alone can
report "running" a few seconds before the database is actually ready to
accept queries.

### `clean` vs `reset`

```make
clean: stop
	@docker rm ...
	@docker rmi ...

reset: colima-stop clean
	@docker system prune -af --volumes
```

- `clean` removes the specific container and image by name — surgical,
  leaves the volume (and therefore your data) intact.
- `reset` is destructive at the system level: `docker system prune -af
  --volumes` removes **all** unused containers, images, networks, *and
  volumes* on the entire Colima VM, not just this project's. The `-a` flag
  extends pruning to all unused images (not just dangling ones), and `-f`
  skips the confirmation prompt. This is the "start completely over" button —
  worth knowing it isn't scoped only to this project before running it on a
  machine with other Docker projects.

### The `.PHONY` declaration and `.DEFAULT_GOAL`

```make
.PHONY: help colima-start colima-stop build run stop logs clean connect status env-file
.DEFAULT_GOAL := help
```

`.PHONY` tells Make that these target names aren't actual files to check the
existence/timestamp of — without it, if a file literally named `build` or
`clean` ever existed in the directory, Make would assume the target was
already "up to date" and skip running the recipe. `.DEFAULT_GOAL` makes
running bare `make` (no target) equivalent to `make help`, which is a nice
usability touch — new contributors get the command list instead of Make's
default (running the first target in the file) or an error.

---

## 4. What "reproducible local infra" actually buys you

Putting this together: `make run` deterministically takes you from "nothing"
to "a running, populated Postgres instance," through a chain that's fully
declarative — Colima config → Dockerfile → environment variables → named
volume. Nothing depends on manual steps or the state of your Mac outside of
having Colima and Docker CLI installed. That reproducibility is the same
property that matters in production infra-as-code (Terraform, Helm charts,
etc.) — this Makefile is a small, honest version of the same idea: **the
environment is defined in version-controlled files, not in someone's head or
their terminal history.**

---

*Next: `02_database_restore_internals.md` — the dockerfile build layers,
`docker-entrypoint-initdb.d`, and what `pg_restore` is actually doing with
`dvdrental.tar`.*

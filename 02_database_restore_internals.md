# 02 — Database Restore Internals: dockerfile, docker-entrypoint-initdb.d & pg_restore

This document covers what happens *inside* the container between "image
built" and "database ready to query" — specifically how a 3MB `dvdrental.tar`
file turns into a fully populated, queryable schema, automatically, on first
boot.

---

## 1. The dockerfile, line by line

```dockerfile
FROM postgres:17-alpine
```

`postgres:17-alpine` is the official Postgres image built on **Alpine
Linux** rather than Debian. Alpine uses `musl` libc instead of `glibc` and
BusyBox instead of GNU coreutils, which is what gets the base image down to
roughly 40MB vs. ~230MB+ for the Debian-slim variant. For a project you're
tearing down and rebuilding repeatedly with `make reset`, that size
difference directly shortens the build/pull time. The trade-off — worth
knowing even though it doesn't bite here — is that `musl`'s subtly different
libc behavior occasionally breaks native extensions that assume `glibc`
(some Postgres extensions, some Python C-extensions in other Alpine-based
images). For plain Postgres with no custom extensions, it's a safe choice.

```dockerfile
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=dvdrental
```

These are **build-time defaults**, baked into the image itself. They matter
for one specific reason: precedence. `docker run -e VAR=value` overrides an
`ENV` set in the image, but if you *forget* to pass `-e` at runtime, the
container still boots correctly using these fallbacks instead of the
official image's own defaults (which just default `POSTGRES_USER` to
`postgres` anyway, but explicitly setting `POSTGRES_DB` here means you get a
`dvdrental` database even if the Makefile's `-e` flags were somehow omitted).

```dockerfile
COPY dvdrental.tar /tmp/dvdrental.tar
```

Copied to `/tmp` deliberately — not to `/docker-entrypoint-initdb.d/`. That
directory (see §2) is scanned by the entrypoint script and anything ending in
`.sh`, `.sql`, or `.sql.gz` gets **executed automatically**. A `.tar` file
dropped in there would just sit there ignored (wrong extension), so keeping
the data file in `/tmp` and having the shell script explicitly `pg_restore`
it from that path is the correct pattern — the init directory holds
*instructions*, not raw data.

```dockerfile
COPY import-data.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/import-data.sh
```

This is the actual hook into Postgres's own initialization system —
explained fully in §2. `chmod +x` is necessary because `COPY` preserves
whatever permission bits existed on your host filesystem, which for a
freshly-written `.sh` file is typically `644` (not executable). Without this
line, the entrypoint script would find the file but fail to execute it.

```dockerfile
HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=3 \
    CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost
```

`HEALTHCHECK` is a Docker directive that runs a command *inside* the
container on a schedule and uses its exit code to set the container's health
status (visible in `docker ps` as `healthy`/`unhealthy`/`starting`) — this is
what your Makefile's `health` target is partially inspecting.

- `--interval=10s` — run the check every 10 seconds after the start period ends.
- `--timeout=5s` — if the check itself doesn't return within 5s, count that
  attempt as a failure.
- `--start-period=40s` — a grace window right after container start during
  which failures **don't** count toward `--retries`. This exists because
  Postgres's own startup (and, on first boot, the entire restore process in
  §3) can legitimately take longer than one interval — without this, Docker
  would mark the container unhealthy while it's still doing expected first-run
  work.
- `--retries=3` — three consecutive failures *after* the start period before
  the container flips to `unhealthy`.
- `pg_isready` — a small utility bundled with Postgres that checks whether
  the server is accepting connections, without actually needing valid
  credentials or running a query. It's the standard lightweight
  liveness/readiness probe for Postgres, which is why it's used here instead
  of a full `psql -c "SELECT 1"`.

---

## 2. `docker-entrypoint-initdb.d/` — how the restore gets triggered automatically

This is the part that makes the whole setup "just work" with zero manual
steps, so it's worth understanding precisely rather than treating as magic.

The official `postgres` image ships an entrypoint script
(`docker-entrypoint.sh`) that runs every time the container starts. On
**first startup only** — specifically, when it detects that
`$PGDATA` (`/var/lib/postgresql/data`) is empty — it:

1. Runs `initdb` to create a fresh Postgres data directory and cluster.
2. Starts a **temporary** Postgres server, listening only on a Unix socket
   (not exposed on any TCP port yet), specifically so that init scripts can
   connect to it without external clients being able to touch a half-initialized DB.
3. Creates the user/database from `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`.
4. **Scans `/docker-entrypoint-initdb.d/` and runs every file it finds, in
   alphabetical order by filename** — `.sh` files are executed (sourced, with
   `psql` environment variables like `PGUSER` already set), `.sql` files are
   piped into `psql`, `.sql.gz` files are decompressed first.
5. Stops the temporary server and starts the real one, now listening on TCP.

This is exactly why `import-data.sh` doesn't need to be invoked from
anywhere in the Makefile or dockerfile explicitly — placing it in that
directory *is* the invocation. It also explains an important behavioral
detail: **this entire sequence only happens when the data directory is
empty.** Once a volume has data in it (see doc 01, §3, on the `-v
dvdrental-volume:...` mount), subsequent container starts skip `initdb` and
all init scripts entirely and just start Postgres directly against the
existing data. This is *why* `make clean` (which removes the container but
not the volume) followed by `make run` boots instantly without re-restoring
— and *why* only `make reset` (which prunes volumes too) forces the whole
restore sequence to run again.

---

## 3. `import-data.sh`, line by line

```bash
#!/bin/bash
set -e
```

`set -e` makes the script exit immediately if any command returns a non-zero
exit code, rather than continuing on and potentially leaving the database in
a half-restored state. This matters specifically because this script runs
during container *initialization* — a silent partial failure here would be
much harder to notice than a script that fails loudly and stops the container
from claiming to be healthy.

```bash
if psql -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = 'dvdrental'" | grep -q 1; then
    echo "dvdrental database already exists, skipping creation."
else
    createdb -U "$POSTGRES_USER" dvdrental
fi
```

- `psql -tc "..."` — `-t` strips column headers and row-count footers
  (tuples-only output), `-c` runs a single command non-interactively. The
  query checks Postgres's own catalog (`pg_database`) for a row matching the
  target database name.
- `grep -q 1` — silently checks whether that query returned the literal value
  `1` (the `SELECT 1` projection), i.e. whether a matching row exists at all.
- This whole block is a **defensive idempotency check**. Given what §2
  explains — this script only ever runs on a fresh, empty data directory —
  you might reasonably ask why this check exists at all if `dvdrental` can
  never already exist at this point. The answer is that it's good practice
  independent of that guarantee: if someone ever manually re-runs this script
  inside a running container (e.g. `docker exec` to debug/re-seed), it won't
  crash trying to `createdb` a database that's already there.

```bash
pg_restore -U "$POSTGRES_USER" -d dvdrental --no-owner --no-privileges /tmp/dvdrental.tar
```

This is the actual restore. A few things worth understanding about
`pg_restore` specifically, since it's a different tool from `psql < dump.sql`:

- **`dvdrental.tar` is a custom-format dump** (created originally via
  `pg_dump -Fc`), not a plain SQL script. Custom format is a
  Postgres-specific binary archive containing a **table of contents (TOC)**
  plus compressed data for each database object. This format is what enables
  `pg_restore`-specific capabilities that a plain `.sql` file can't offer —
  selective restore (`--table=`, `--schema-only`, etc.), and critically,
  **parallel restore** via `-j N`, since the TOC lets `pg_restore` know
  which objects have no interdependencies and can be loaded concurrently.
  This script doesn't use `-j`, so it restores serially — a reasonable
  choice for a dataset this small (dvdrental is a few MB), but worth noting
  as an easy performance lever (`-j 4`, say) if this pattern gets reused
  for a larger dataset later.
- **`--no-owner`** — the original dump was taken from *some* source database
  where the objects were owned by whatever role did the dump (commonly a
  specific superuser or the original `postgres` role on a different system).
  Without this flag, `pg_restore` tries to `ALTER ... OWNER TO` each object
  to match the original owner — which fails, or restores under the wrong
  role, if that exact role doesn't exist in this fresh container. `--no-owner`
  makes every restored object owned by whichever role runs the restore (here,
  `$POSTGRES_USER`), which is what you want when restoring into a brand-new,
  differently-provisioned instance.
- **`--no-privileges`** (a.k.a. `--no-acl`) — skips restoring `GRANT`/`REVOKE`
  statements from the original dump. Same underlying reason: those
  privileges reference roles from the source system that don't exist here.
  Without this flag, you'd get a wall of "role does not exist" errors during
  restore (non-fatal by default, but noisy, and can leave permissions in an
  inconsistent state).

---

## 4. The full sequence, end to end

Putting docs 01 and 02 together, here's precisely what happens from
`make run` to a queryable database, in order:

1. Make ensures Colima is running, builds the image (`postgres:17-alpine` +
   your `COPY`/`HEALTHCHECK` layers), then runs the container with a named
   volume mounted at `/var/lib/postgresql/data`.
2. The container's entrypoint checks that mounted volume — empty on first run.
3. `initdb` creates a new cluster; a temporary local-only Postgres starts.
4. The `postgres`/`postgres`/`dvdrental` role and database get created from
   your `-e` environment variables.
5. `/docker-entrypoint-initdb.d/import-data.sh` runs (alphabetically, and
   it's the only script present): it double-checks the database exists,
   then `pg_restore`s `/tmp/dvdrental.tar` into it — schema *and* data,
   ownership and privileges stripped to fit the new environment.
6. The temporary server stops; the real Postgres server starts, now
   listening on TCP inside the container, which the `-p 5432:5432` mapping
   exposes to `localhost` on your Mac.
7. From ~10s after that (per `--start-period=40s` and `--interval=10s`),
   Docker's `HEALTHCHECK` starts polling `pg_isready`, and `docker ps` starts
   reporting the container as `healthy`.
8. Every *subsequent* `make run` (as long as the volume survives) skips
   steps 2–5 entirely and just starts Postgres directly against the existing,
   already-restored data — which is why restarts are fast and `make clean`
   doesn't cost you your data, only `make reset` does.

---

*Next: `03_dbt_transformation_layer.md` — why staging models are 1:1 views,
the reasoning behind each star-schema design decision (grain choice,
pre-aggregating payments, rolling up many-to-many categories), and how the
generic + singular dbt tests actually catch data quality problems.*

# Setup and operation

## Native development

`npm run setup` installs the Python hash lock and npm lock, seeds only an empty pilot database, and builds assets. `npm run dev` starts API, worker and Vite; `npm start` starts API, worker and built assets. Both stop their own child processes on Ctrl+C. Node 22.12+, Python 3.12 and uv are required; the current environment uses Node 24.19 and Python 3.12.14.

Use existing isolated checkouts. Do not create a Git worktree unless explicitly requested. Preserve `.local/`: it contains accounts, database, originals in snapshots, and private backups. No runtime passwords are tracked.

Settings (configure before starting):

| Variable | Meaning |
| --- | --- |
| DATABASE_URL | SQLAlchemy URL; default local SQLite. PostgreSQL: postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE, supplied privately |
| MESSI_DATA_DIR | Private state directory; default repository/.local; Docker /data |
| MESSI_ORIGINS | Comma-separated exact browser origins; no wildcard. Defaults loopback dev ports 5173/8000 |
| MESSI_SECURE_COOKIES | Set 1 for HTTPS deployments; local HTTP pilot uses 0 |
| API_HOST / API_PORT | Default 127.0.0.1 / 8000; container host 0.0.0.0 within private network |
| CHROMIUM_PATH | Approved Chromium executable for E2E; default /usr/bin/chromium |
| MESSI_E2E_URL / MESSI_E2E_ACCOUNTS | Override test application and private synthetic account file |
| MESSI_TEST_DATABASE_URL | Dedicated disposable database for backend tests; tables are dropped/recreated. NEVER use a real project database |
| UV_CACHE_DIR / NPM_CONFIG_CACHE | Writable package caches when the user's home directory is read-only |

API health is `/api/health`. Actual readiness requires login, project retrieval and a successful validated schedule, not just health/PID/port. `npm run smoke` exercises those operations on a new synthetic project and checks the export hash; it intentionally retains that labelled project. Interactive API documentation is `/docs` when the API server is running; mutation commands still need the correct Origin and CSRF token. Project data/routes are always authorized.

## PostgreSQL containers

```bash
python3 scripts/compose-env.py
docker compose --env-file .local/compose.env up --build -d
```

The generator creates a random private database password and refuses to overwrite an existing environment file. Compose starts a private PostgreSQL service and the compiled application/worker, publishing only loopback port 8000 by default. `MESSI_HTTP_PORT` may change that host port. The browser origin must match `MESSI_ORIGINS` exactly. Do not expose the database publicly.

The first boot writes private synthetic login credentials into the app's `/data/bootstrap-users.json` volume. Access them through an authorised private editor/administrator workflow, not logs or chat. Do not publish these values. Native `.local/bootstrap-users.json` credentials are a different installation and do not sign in to the container database.

To stop processes while retaining data:

```bash
docker compose --env-file .local/compose.env down
```

Do not add `-v` unless you explicitly intend to destroy that installation's data. Container builds preserve pip hashes, npm lock integrity and TLS verification. The Dockerfile accepts an optional `build_ca` BuildKit secret for a trusted organisational CA; this is used only during verified package installation and is not copied to image layers. In this cloud runner Docker build DNS may need the existing egress proxy hostname mapping; see validation evidence. Do not disable certificate/checksum checks to work around networking.

## Provision and revoke accounts

```bash
PYTHONPATH=backend .venv/bin/python -m messi.manage create-user planner@your-domain --name "Mine Planner"
PYTHONPATH=backend .venv/bin/python -m messi.manage reset-password planner@your-domain
```

The CLI prompts privately; passwords never enter command arguments or saved documentation. Password reset revokes that account's existing sessions. An owner adds the account to a project through Project team. There is no public self-registration endpoint. Viewer access permits exports; choose membership accordingly. Logout revokes the server session, and polling tabs clear their private workspace on the next unauthorized response.

## Backup and fresh restore

```bash
npm run backup
```

This writes a mode-0600 logical JSON backup plus SHA-256 sidecar under `.local/backups/`. It contains password hashes, private mine data and immutable source/result snapshots, but no login sessions or plaintext bootstrap passwords. Treat the entire backup as confidential. Checksums detect accidental corruption; store backups in separately protected storage because a checksum is not an authenticity signature.

Backups use a consistent PostgreSQL repeatable-read transaction or a SQLite write-lock snapshot. A restore refuses any nonempty target and checks schema/checksum. Point `DATABASE_URL` at a **fresh** target, stop application workers, and run:

```bash
PYTHONPATH=backend .venv/bin/python -m messi.backup --restore /absolute/private/backup.json
```

Unfinished restored jobs become cancelled, requiring explicit new submission. Approved results remain preserved. Restore excludes sessions, so users must sign in again. Test counts, hashes and recomputed validators before using restored data. Do not restore into a live pilot; never change production `DATABASE_URL` to a test database accidentally. This utility is not production PostgreSQL PITR.

## Remote/production prerequisites

Before remote use: own-domain HTTPS reverse proxy, `MESSI_ORIGINS` and secure cookies, identity lifecycle/SSO decision, external rate limiting, database/network restrictions, protected backups/restore drill, monitored worker heartbeats/storage, tested recovery objectives and site engineering acceptance. No public website, enterprise SSO, reserve certification, real fleet integration or regional data-residency verification is delivered by a local successful run.

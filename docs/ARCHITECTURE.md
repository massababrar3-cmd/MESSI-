# Implemented architecture and decisions

## 0.1 vertical slice

React/TypeScript + Three.js browser → same-origin FastAPI API → PostgreSQL or SQLite metadata/snapshots → separate durable database-polling planning worker → validated immutable result → shared browser/Gantt/reports.

- `backend/messi/domain.py`: typed units/model contracts, CSV/OBJ parsing and validation.
- `scheduler.py`: deterministic baseline and independent engineering validator.
- `db.py`: transactional users, sessions, projects, memberships, scenarios, runs and audit.
- `api.py`: authenticated project commands, revision checks, reports and approval.
- `worker.py`: persisted jobs, compare-and-set leases, progress/cancellation/recovery.
- `backup.py`: consistent logical snapshots, checksums and fresh-database restore.
- `frontend/src`: shared planning screens and Three.js model interaction.

## ADR-001 · Data-store scope

PostgreSQL is supported and tested for the team route. SQLite/WAL is a deliberate zero-service local-development option and a small-pilot fallback. Both use SQLAlchemy and the same domain contracts. Do not place a SQLite database on a multi-host/shared network filesystem. Server-controlled JSON snapshots are stored transactionally in the database, including bounded source files; this avoids an unimplemented distributed metadata/object-commit protocol during this pilot.

The proposed Parquet/Arrow/S3 large-model architecture is **not implemented**. The release enforces much smaller input limits. Revisit it before removing those limits or making million-block performance promises. Schema v1 uses create-on-first-start; there is no tested upgrade migration from future schemas yet. Back up before changing schema and add explicit migrations for the next schema release.

## ADR-002 · Durable jobs without Redis

For this pilot a separate Python worker polls durable run rows rather than introducing Redis/RQ before it is required. Submission serializes on the project (PostgreSQL row lock, SQLite write transaction), enforces idempotency, and prevents a duplicate queued/running submission for that project. Workers claim a queued run with conditional update and unique lease token. Results commit only if the lease is still owned and cancellation was not requested.

Abandoned `running` leases are requeued after 120 seconds. Progress checkpoints refresh the heartbeat. Long future non-cooperative geometry/solver calls need a separate heartbeat/resource supervisor before deployment at larger scale. The current scheduler checks once per activity. One worker is launched by default; no arbitrary parallelism, CPU isolation or 10-planner benchmark is claimed.

A tab closing leaves a job running. Reopening polls authoritative database state. Queue cancellation and mid-run cancellation are tested. Retrying a duplicate delivery cannot overwrite a committed finished result. API downtime and worker downtime have separate recovery behavior.

## ADR-003 · Local identity first

The pilot implements scrypt password hashing, random private bootstrap passwords, hashed session tokens, 8-hour HttpOnly SameSite cookies, mutation CSRF tokens, strict Origin checks and project-scoped server authorization. Owners manage membership and approve; planners edit/run; reviewers approve; viewers read/export. Project IDs, run IDs and scenario IDs alone grant no access. Local server administrators can provision/reset users through a private interactive CLI.

OIDC/enterprise SSO, MFA, centrally managed identity lifecycle and a distributed rate limiter are **not implemented**. The current login throttle is an in-process IP limit; production needs reverse-proxy/identity-provider rate limiting and lifecycle controls. Enable secure cookies and HTTPS before any remote access. No long-lived browser credentials or localStorage tokens are used. Application audit rows have no edit/delete API; database administrators remain trusted and can alter storage.

## ADR-004 · Engineering precision

Persist finite Float64 engineering coordinates and derive bank quantities from canonical blocks only. Render around a local origin and do not compute tonnes from GPU geometry. OBJ surfaces are visual context, including when their edge topology is closed. No implicit solids, pit-limit optimisation or geological interpolation is inferred from a 3D appearance.

## ADR-005 · Deployment boundaries

The default dev launcher binds loopback and starts API/worker/Vite. The built launcher serves a compiled SPA with API/worker. Docker Compose adds PostgreSQL and private durable volumes. These are working deployment mechanisms, not proof of a secure Internet deployment or operational mine acceptance. An organisation-owned HTTPS reverse proxy, identity plan, backup retention, data residency and engineering sign-off remain deployment prerequisites.

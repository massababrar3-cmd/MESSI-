# Validation evidence · 28 October 2026

This records executed checks for release 0.1. Proposed original SRS/ENG coverage is not treated as executed evidence.

| Check | Actual outcome |
| --- | --- |
| Python engineering/API/backup suite, isolated SQLite | **35 passed**, 0 failed/skipped |
| Same suite, isolated PostgreSQL 17 container | **35 passed**, 0 failed/skipped |
| Chromium E2E against compiled SPA + FastAPI/worker + PostgreSQL Compose installation | **8 passed**, 0 failed/skipped, 41.8 s |
| TypeScript type check | Passed |
| Vite compiled production build | Passed; large bundle advisory remains (~777 kB JS, ~212 kB gzip, largely Three.js) |
| Repeat installation through npm run setup | Passed noninteractively; existing private accounts/data preserved |
| Native compiled startup + real npm run smoke | Passed: login, synthetic project creation, queued worker run, 10/10 blocks, zero violations and export/hash reconciliation |
| Logical backup and fresh empty-database restore | Passed in both backend suite runs; checksum tampering rejected; no login sessions restored |
| npm dependency audit | 0 known vulnerabilities at time checked |
| Python pip-audit hash lock | 0 known vulnerabilities at time checked |
| Small synthetic baseline performance measurement | 1,000 blocks, 40,000,000 t, feasible, zero violations, **0.341 s** on this runner; not a general scale/concurrency result |

Two identical 35-test backend runs are reported separately for database coverage, not described as 70 unique tests. The 8 browser flows include actual WebGL rendering, CSV rejection/import and analytic quantity checks, OBJ reference surface import, schedule/exports/approval, scenario independence, stale inputs, viewer restrictions, two-tab revision conflicts, narrow-screen navigation and cross-tab logout.

## Engineering references actually exercised

- Ten non-overlapping 10 × 10 × 10 m blocks at 2.5 t/m³ produce 10,000 m³ and 25,000 t.
- Synthetic coal pilot produces 160,000 m³, 112,000 t coal and 200,000 t waste; weighted dry coal ash 11.8%.
- 1,000 t at 10% ash plus 1,000 t at 20% ash, same basis, produces 2,000 t at 15%.
- Resource exclusivity, predecessor order, maintenance, unavailable days, date/resource locks and destination capacity are checked.
- A DST transition has correct real elapsed working time.
- Tampered rates/quantities, headline totals, stock balance/quality and daily production are detected by the independent validator.
- Simultaneous duplicate submissions create one durable job; queued/running cancellation and abandoned-lease recovery are exercised.
- Guessed IDs do not expose another project's scenario/run/export/member/audit data.

## Container troubleshooting and trust

The cloud Docker build initially failed because its build namespace could not resolve the environment's egress proxy. Supplying the existing proxy variables plus a hostname mapping restored routing; the next request correctly failed TLS because the stock image lacked the environment's trusted CA. Mounting the already-trusted host CA bundle as an optional BuildKit secret resolved verification. TLS, pip artifact hashes and npm lock integrity remained enabled throughout. The CA and proxy credentials are not copied into the image or repository.

A subsequent runtime failure was traced to cloud-created source files having restrictive modes when copied as root into an unprivileged image. The Dockerfile now makes application code readable/traversable while retaining root ownership; `/data` is owned by the application user. The corrected unprivileged image started and passed the 8 browser tests with PostgreSQL. Docker image builds also verify pinned package hashes.

## Limits of evidence

- Browser tests ran in Linux Chromium with software WebGL and a mobile viewport. Physical Windows Chrome/Edge/GPU driver combinations and actual mobile hardware are unverified.
- Public HTTPS hosting, OIDC/MFA, enterprise penetration testing, regional hosting/data residency, production backup/PITR and engineering site acceptance are not verified.
- No million-block, 10,000-activity, 10-concurrent-planner or globally optimal scheduling claim is made.
- The current dependency scan reports known advisories only; it is not an assurance of vulnerability-free software.
- A Starlette test-client deprecation warning recommends a future httpx2 migration; the current 35-test runs pass. It does not indicate skipped tests.
- No SPRY LMS lesson, transcript, video or audio was accessed. Source-based feature-parity analysis remains unavailable.

See IMPLEMENTATION.md for every deferred/partial FR requirement. Successful build/tests do not turn those future requirements into implemented features.

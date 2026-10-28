# MESSI development instructions

Read docs/ENGINEERING.md and docs/IMPLEMENTATION.md before changing mining calculations or claiming feature support. docs/BLUEPRINT.md is long-term proposed scope; only tested implementation is available.

- Preserve authoritative float64 coordinates, explicit units/quality bases, source lineage and immutable run snapshots.
- Never compute engineering quantities from rendered/LOD geometry or call a heuristic result globally optimal.
- Keep the independent validator independent of the scheduler's allocation algorithm; test negative/tampered cases.
- Enforce project permissions on every API, job, object and export path. Use revision comparisons for edits.
- Keep passwords, sessions, live models and backups under ignored private state. Never print bootstrap credentials.
- Backend tests drop/recreate test tables. MESSI_TEST_DATABASE_URL must name a dedicated disposable database.
- Validate changes with npm test, npm run typecheck, npm run build and relevant existing browser tests against a running synthetic pilot.
- Use the existing isolated checkout. Do not create a Git worktree unless the user asks.
- Do not overwrite unrelated repositories or silently change the saved environment repository selection.

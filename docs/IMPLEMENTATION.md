# Release 0.1 support matrix and backlog

This release implements a useful end-to-end engineering pilot, **not all features in the proposed SRS**. No LMS videos/transcripts were reviewed; course endpoints were blocked. All feature claims below refer to the original implementation and executed tests, not SPRY parity.

Legend: **Working** = implemented within documented pilot limits; **Partial** = a narrower explicit subset; **Deferred** = no implementation/claim. Relevant engineering/API tests live in backend/tests and browser acceptance flows in frontend/tests. See VALIDATION.md for actual runs; the original ENG list remains proposed reference coverage, not evidence every ENG fixture has executed.

| FR | Status | Implemented boundary / remaining work |
| --- | --- | --- |
| FR-001 | Partial | Projects and scenarios persist; copy via branch. Project archive/delete administration is deferred |
| FR-002 | Partial | Validated CSV blocks with fixed canonical schema; Parquet/mapping wizard deferred |
| FR-003 | Partial | Restricted triangular OBJ surface import; DXF/DWG deferred |
| FR-004 | Working | Original CSV/OBJ, hashes, revision/source metadata and immutable run snapshots |
| FR-005 | Partial | Explicit project CRS/datum, input m/ft and compatible density/quality bases; no CRS/datum transforms |
| FR-006 | Working | Preview, row errors, complete-model validation and atomic import |
| FR-007 | Working | Orbit/plan, layers, block selection, section and attribute inspection within model limits |
| FR-008 | Partial | Block geometry editing and block-origin distances; strings/polygons/advanced CAD deferred |
| FR-009 | Partial | One mining activity per rectangular block; multi-stage drill/blast/rehab task generation deferred |
| FR-010 | Deferred | Solid/surface-derived quantity algorithms not implemented |
| FR-011 | Partial | Coal/waste, density and ash/basis; custom schemas, swell and recovery deferred |
| FR-012 | Partial | Zero-lag finish-to-start, priority, locks and cycle diagnostics; spatial safety rules/other dependency types deferred |
| FR-013 | Working | Exclusive fleet pools, material eligibility, t/h rates, utilisation and date outages |
| FR-014 | Working | Deterministic feasible baseline with separate result validator; no global feasibility/optimality proof |
| FR-015 | Partial | Exact activity start/resource locks; project frozen periods deferred |
| FR-016 | Partial | Selectable Gantt and inspector-based manual lock edits; drag/drop and impact preview deferred |
| FR-017 | Working | Date-based block completion playback from the same run; not progressive cut geometry |
| FR-018 | Partial | Coal ROM/waste destinations and cumulative capacity; plant/export logistics deferred |
| FR-019 | Partial | Opening/receipts/closing ledger; reclaim/loss entry and movement transactions deferred |
| FR-020 | Partial | Compatible-basis weighted ash; energy/moisture/multi-property blending deferred |
| FR-021 | Deferred | Plant yield/recovery and product transformation |
| FR-022 | Deferred | Haul-route geometry, cycle/fleet bottlenecks and simulation |
| FR-023 | Partial | Hard resource/calendar/destination constraints; time-phased targets and soft penalties deferred |
| FR-024 | Deferred | Solver optimisation/bounds/gaps |
| FR-025 | Partial | Branches, immutable runs and fleet/horizon/status comparison; full common-basis KPI comparison deferred |
| FR-026 | Deferred | Cash flow, price/currency models and valuation |
| FR-027 | Deferred | Actual-production import and variance reconciliation |
| FR-028 | Working | CSV/Excel/PDF/JSON with reconciled quantities and run provenance |
| FR-029 | Partial | Schema-v1 backup/checksum/fresh restore; upgrade migration framework deferred |
| FR-030 | Working | Transactional saves, durable jobs, cancellation, restart lease recovery and validated publication |
| FR-031 | Partial | Browser client needs no developer runtimes; verified on Linux Chromium, Windows/Edge acceptance pending |
| FR-032 | Working | Local authenticated project roles, membership, approvals and team storage; enterprise OIDC deferred |
| FR-033 | Partial | Typed API/OpenAPI; public plugin/batch SDK stability deferred |
| FR-034 | Deferred | Monte Carlo/uncertainty/correlation models |
| FR-035 | Deferred | Advanced CAD/geological interpretation/strategic optimisation/underground modules |
| FR-036 | Working | Server-side project scope on API, runs, membership, audit and exports; isolation tests |
| FR-037 | Working | Import/edit/run/approval/membership/export audit, without user-facing rewrite endpoints |
| FR-038 | Partial | Bounded UTF-8 CSV/OBJ with validation; archives and resumable uploads unsupported |
| FR-039 | Working | Optimistic concurrency, atomic idempotent submissions, worker CAS leases and immutable results |
| FR-040 | Partial | Health, persisted jobs/progress, logical backups/restore; external alerting and PITR deferred |

## Next delivery milestones

1. **Site-calibrated planning:** review sample formats, density/quality basis, actual fleet/task rates and access rules with a mine planner. Add approved lag/sequence constraints, targets and frozen periods with engineering fixtures.
2. **Material movement:** reclaim/loss transactions, stock depletion, processing yield/recovery and actual-versus-plan. Add property-specific blend equations only after agreeing bases.
3. **Scale and identity:** OIDC/MFA, distributed throttling, large immutable Parquet/Arrow datasets and private object storage, resumable imports, measured concurrency and resource supervision.
4. **Optimisation/haulage:** tiny enumerated solver benchmarks, bounded CP-SAT model, shared haul fleets and calibrated road/cycle-time models. Preserve truthful statuses and independent checks.
5. **Advanced modelling:** supported DXF/vendor adapters, validated solids, pit/bench/ramp and spoil workflows; specialist geometry/licensing/domain acceptance.

No deferred capability is represented by fake operational numbers or a disabled screen presented as completed functionality. The application displays only supported controls. Model quantities, resource rates and schedule ledgers are real computations; synthetic seed inputs are clearly labelled.

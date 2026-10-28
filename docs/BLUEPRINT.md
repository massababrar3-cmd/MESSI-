# MESSI — Development Blueprint aur Proposed SRS

**User-supplied name:** Mining Engineering Scheduling Software Institute (MESSI)
**Product:** Independent mine planning, scheduling aur 3D modelling platform
**Document version:** 0.1 — engineering discovery baseline
**Prepared:** 28 October 2026
**Status:** Proposed design; stakeholder-approved SRS ya implemented software nahi.

## 1. Executive direction aur evidence ki had

Aap ka maqsad ek independent, configurable mining engineering product banana hai jisme mine data import, 3D viewing/modelling, practical production schedules, equipment allocation, haulage, material quality, scenario comparison aur reporting ek workflow mein kaam karein. MESSI ko operational mine-planning tool banane ke liye reliable engineering calculations aur explainable scheduling ko pehle establish karna hoga; attractive 3D screen akeli kaafi nahi.

**SPRY/LMS access status:** Diya gaya Adobe Learning Manager URL aur Precision Mining ke public homepage/product URL ko access karne ki koshish ki gayi. Teenon requests ko environment proxy ne HTTP 403 Forbidden se reject kiya. LMS login nahi hua; koi lesson, video, audio, transcript, module list ya exact SPRY feature is task mein inspect nahi hua. Neeche diya gaya design user ke goal aur general software/mining engineering design par mabni original proposal hai. Isay SPRY ki verified specification, transcript summary ya feature-parity assessment na samjhein.

**Source register:**

| Source | Is document mein status | Kya conclude ho sakta hai |
| --- | --- | --- |
| User request | Available | Mine planning, scheduling, 3D modelling aur custom requirements chahiye |
| User-provided Adobe LMS link | Access denied by proxy | Course contents aur learner permissions unknown |
| https://precisionmining.com/ | Access denied by proxy | Product capabilities independently verify nahi huin |
| https://precisionmining.com/spry/ | Access denied by proxy; page existence unverified | Koi feature evidence hasil nahi hua |
| Existing Software checkout | Earlier onboarding mein operational hub inspect hua | Uski installation mine-planning engine ki availability prove nahi karti |

Training material baad mein milne par section 18 ki traceability process se add hoga. Original requirements aur independently written algorithms use karein. Training ko dekhne ki permission proprietary code, private APIs, exact assets ya redistribution rights nahi deti.

## 2. Working assumptions aur scope boundaries

User ne **open-cut coal** aur **browser-based team application** confirm ki hai. Baqi points proposed defaults hain:

1. Confirmed: pehla pilot open-cut coal operation hai. Open-pit metals/quarry adaptations architecture mein possible hon, lekin production support separately validate ho.
2. Confirmed: primary product browser-based team application hai. Heavy computation central workers par hogi. Windows par current Chrome/Edge primary browser targets hain; Linux server/CI. Desktop app aur offline scheduling first release ka scope nahi.
3. Default site timezone Australia/Brisbane hai; har project apni IANA timezone configure kar sakta hai.
4. Engineering calculations mein internal metric base units aur explicit conversion use hogi. Coal quality ke wet/dry aur as-received bases ko interchange nahi kiya jayega.
5. Initial geological input engineer-supplied, validated surfaces/block tables honge. Exploration database, resource estimation aur geological interpretation ko first release mein recreate nahi kiya jayega.
6. Commercial production deployment se pehle site engineer pilot data, quantities, calendars, practical sequences aur outputs validate karega.
7. Existing mine-operations hub se integration optional adapter hoga. Mine-planning engine ko us application's unrelated workflows se tightly couple nahi kiya jayega.

**Scope distinction:**

| Capability | First working pilot | Mature product / later |
| --- | --- | --- |
| Model data | CSV/Parquet blocks, triangulated terrain/designs, explicit units/CRS | Geological vendor adapters, point clouds, advanced sub-blocks |
| 3D | Inspect, select, measure, section, simple strings/blocks/bench activities | Advanced CAD solids, detailed road/pit design tools |
| Scheduling | Deterministic feasible schedule, manual locks, precedence, calendars | Target optimization, uncertainty, multi-site planning |
| Materials | Waste/coal classification, basic stocks and quality tracking | Complex blending, plant recovery/yield and reclaim strategies |
| Haulage | Destination movement and equipment-capacity assumptions explicitly recorded | Configured cycle times/shared fleet, then route profiles and dynamic simulation |
| Economics | Export reconciled physical quantities and stated economic inputs | Validated cash-flow comparison, then strategic pit/pushback optimisation |
| Mine types | One agreed open-cut coal pilot | Underground development/stoping, fleet and ventilation constraints |
| Collaboration | Shared projects, role-based access, version conflicts and plan approval | Advanced simultaneous editing and multi-site federation |

First release ko geological resource-estimation package, real-time dispatch system, geotechnical approval system, ya certified reserve-reporting software na label karein. Inmein har ek separate engineering scope hai.

## 3. Product outcomes aur user roles

**Primary outcome:** Planner imported physical quantities ko engineer-defined rules aur equipment constraints ke mutabiq period-wise production plan mein convert kare; har result source data aur rules tak traceable ho.

Roles:

- **Mine planner:** models, dependencies, scenarios aur period targets manage kare.
- **Geologist / surveyor:** imported model, surfaces, classifications, quantities aur reference system review kare.
- **Production engineer:** dig rates, fleets, shifts, road conditions aur operational constraints define kare.
- **Planning superintendent:** scenarios compare, exceptions review aur plan approve/publish kare.
- **Viewer / reporting user:** approved results dekhe aur permitted reports export kare.
- **System administrator:** installation, access, backup aur team-server settings maintain kare.

Team application mein authenticated identity aur server-side project permissions mandatory hain. Browser mein role selector ya hidden button security control nahi. Administrative account ko automatically plan-approval authority na dein; project roles explicit hon.

## 4. End-to-end planning workflow

1. Project banayein: site name, CRS, vertical datum, timezone, unit schema aur planning horizon.
2. Survey/design surfaces aur block/material data import karein; dry-run report mein errors aur unresolved mappings dekhein.
3. Original source aur content hash preserve karein; canonical model create karein; quantities reconcile karein.
4. 3D view mein terrain, coal/waste, pit, benches, dumps aur stock locations inspect karein.
5. Operational planning units define karein: pit → stage/strip → bench/seam → mining block → activity.
6. Drill, blast, prestrip, excavate, haul, coal clean/recover aur rehabilitation activities configure karein, jahan applicable hon.
7. Engineer-approved spatial/sequence rules ko explicit dependency graph mein expand karein; exceptions review karein.
8. Calendars, equipment, productivity, haulage, destinations, costs aur material-quality bases configure karein.
9. Locked/manual commitments add karein. Data validation aur a fast infeasibility precheck run karein.
10. Feasible baseline generate karein. Conflicts ko identifiable activities/resources/periods ke saath show karein.
11. Alternative scenario branch karein; rates, fleets, sequences ya targets change karke rerun karein.
12. Gantt, 3D time animation, physical/quality reconciliation aur cash-flow compare karein.
13. Engineer review ke baad immutable plan revision publish karein. PDF/Excel/CSV export karein.
14. Actual production import karke actual-versus-plan dekhein; original baseline preserve rahe.

## 5. Functional requirements — proposed SRS

Priority: **M = first operational pilot**, **S = next release**, **L = later specialised scope**. Har M requirement ka implementation test aur domain acceptance evidence chahiye.

| ID | Requirement | Priority | Minimum acceptance evidence |
| --- | --- | --- | --- |
| FR-001 | Create/open/copy/archive a project with units, timezone, CRS and schema version | M | Save/reopen se metadata aur stable IDs preserve hon |
| FR-002 | Import CSV/Parquet block/activity tables through a mapping wizard | M | Required columns, type/range checks, duplicate IDs aur row-level error report |
| FR-003 | Import triangulated surfaces/meshes from agreed OBJ and restricted DXF profiles | M | Supported entity list documented; unsupported entities explicitly reported |
| FR-004 | Preserve source files, import mappings, hashes and revision provenance | M | Schedule se exact imported revision identify ho |
| FR-005 | Require CRS, datum, axis orientation, units and density/quality basis | M | Missing/ambiguous reference system or quantity units block affected calculations |
| FR-006 | Preview import and reject/explicitly acknowledge errors before commit | M | Failed import partial active data na chhore |
| FR-007 | 3D orbit/pan/zoom, layers, legend, selection, visibility, clipping and section | M | Reference model ke selected objects correct IDs/attributes dikhayein |
| FR-008 | Measure distance/elevation and create simple planning strings and block boundaries | M | Known geometry ke against tolerance-defined measurement checks |
| FR-009 | Generate activities from validated block quantities and engineer-defined stages | M | No silent duplicate activities or double-counted material |
| FR-010 | Derive quantities from approved surfaces/solid boundaries | S | Closed geometry, non-overlap and benchmark volume reconciliation |
| FR-011 | Configure material types, seams, density, swell/shrink and quality attributes | M | Units/bases explicit; incompatible quality blends reject hon |
| FR-012 | Configure precedence, release dates, access rules, lags and spatial dependencies | M | Cycles aur inaccessible activities identifiable conflict report dein |
| FR-013 | Configure equipment pools, compatible tasks, quantity rates and maintenance calendars | M | Unsupported resource/task assignment reject ho |
| FR-014 | Build a resource/calendar-feasible baseline schedule | M | Independent validator precedence, quantities and resource capacity verify kare |
| FR-015 | Support manual dates, resource locks and approved frozen periods | M | Impossible lock hard conflict de; silently unlock na ho |
| FR-016 | Display editable Gantt with dependency links and a before/after impact preview | M | Manual move engine ke through revalidate ho, sirf visual move na ho |
| FR-017 | Animate scheduled extraction/placement in 3D by date or period | M | Display quantities same schedule results se reconcile hon |
| FR-018 | Track movement to ROM, waste dump, stockpile, plant or export destination | M | Destination capacity aur mass balance violations expose hon |
| FR-019 | Track basic stock opening, receipts, reclaims, losses and closing | M | Negative inventory aur inconsistent ledger posting reject ho |
| FR-020 | Calculate basis-aware weighted quality and product tonnes | M | Hand-calculated coal quality/tonnage fixtures match hon |
| FR-021 | Add explicit plant yield/recovery or processing model | S | Feed, product, rejects and declared losses reconcile hon |
| FR-022 | Support haul routes, measured/configured cycle times and truck allocation | S | Travel, loading, queue assumptions aur fleet bottleneck report available |
| FR-023 | Evaluate time-phased production targets and hard/soft rules | M | Hard conflicts infeasible status; soft deviations quantified |
| FR-024 | Optimise a bounded selected model for configured objectives | S | Feasibility verified; best bound/gap or unknown status accurately reported |
| FR-025 | Branch immutable scenario inputs and compare common-basis KPIs | M | Parent scenario change se completed run mutate na ho |
| FR-026 | Compute configured costs, revenue and period cash flow | S | Currency, price basis, time basis aur reference examples reconcile hon |
| FR-027 | Import actuals and report actual-versus-baseline with revisions | S | Duplicate import idempotent; baseline never overwritten |
| FR-028 | Export auditable schedule, quantities, quality, assumptions and exception reports | M | CSV/Excel/PDF totals result dataset se reconcile hon |
| FR-029 | Version project schema and migrate with recovery/rollback path | M | Backup/staging migration verify ho; failure mein previous service/data restore hon |
| FR-030 | Recover safely from cancellation, crash or interrupted save | M | Last committed revision recover ho; incomplete jobs publish na hon |
| FR-031 | Provide supported-browser team workflow without client runtimes | M | Clean Windows Chrome/Edge client se HTTPS par import, view, schedule and export work kare |
| FR-032 | Provide authenticated users, project roles, approvals and shared storage | M | Cross-project denial, privilege checks and concurrent-edit conflict tests |
| FR-033 | Provide documented batch/API extension points | S | Versioned schema, unit-aware inputs and reproducible result contract |
| FR-034 | Add uncertainty cases for rates, availability, geology and weather | L | Seeds, distributions, correlations and percentiles traceable hon |
| FR-035 | Support advanced CAD, optimisation and underground modules | L | Separate approved SRS and domain-specific acceptance suite |
| FR-036 | Enforce project roles on API, workers, datasets, downloads and exports | M | User of project A cannot discover/read/change project B using guessed IDs |
| FR-037 | Record imports, edits, jobs, approvals and exports in an audit trail | M | Actor, project, revision and time captured; ordinary users cannot rewrite history |
| FR-038 | Recover large uploads and validate hostile/malformed files | M | Interrupted upload resumes or fails cleanly; traversal/zip-bomb inputs quarantined |
| FR-039 | Preserve multi-user revision consistency and job idempotency | M | Stale edits conflict; duplicate queue delivery cannot publish duplicate results |
| FR-040 | Provide operational monitoring and tested metadata/object restore | M | Failed worker recoverable; fresh-staging restore validates all referenced objects |

## 6. 3D modelling aur geometric integrity

### 6.1 Representation

- **Terrain/design surface:** triangulated irregular network; x/y/z in declared CRS and vertical datum. A surface alone does not define a closed volume.
- **Solid:** closed, oriented manifold mesh with explicit tolerances; otherwise volume unavailable or flagged.
- **Regular block:** origin/centroid convention, dimensions, rotation if supported, density, material and quality. Overlap rules explicit hon.
- **Planning activity geometry:** selectable association to source blocks/solids and quantity attribution; display mesh original engineering quantities ko replace na kare.
- **Strings/polylines:** surveyed/design lines with closed/open semantics; a drawn polygon automatic mineable solid nahi.
- **Road graph:** nodes, directed segments, grades, restrictions and time-dependent availability; optional advanced module.

Phase-one restricted DXF importer accepted entity types explicitly document kare. DWG aur proprietary mine-model readers tab add karein jab SDK access, licensing aur reference fixtures available hon; universal compatibility ka dawa na karein. LAS/LAZ, GeoTIFF aur specialised formats later adapters hain, automatically supported nahi.

### 6.2 Coordinate and accuracy rules

Engineering coordinates Float64 mein authoritative rahenge. Rendering camera ke qareeb local origin se Float32 buffers use kar sakti hai. Project origin, CRS aur datum retain hon; export par coordinates exact agreed tolerance mein restore hon. Arbitrary local grids ko false EPSG code assign na karein. CRS conversion aur vertical datum/geoid conversion separate operations hain; required grid files unavailable hon to stop/flag karein.

Geometry validation includes missing/non-finite coordinates, degenerate triangles, inverted faces, self-intersections where relevant, non-manifold edges, overlaps, extreme extents and incompatible units. Open surfaces ko silently close ya repair na karein. Repair explicit copy/revision par ho aur changed quantities report hon.

### 6.3 Performance approach

Spatial indexing, chunked loading, frustum culling, instancing, level-of-detail and BVH-based picking use karein. LOD engineering quantity calculation mein use na ho. Large block tables ke visible subset ko GPU par load karein; every attribute ko every frame copy na karein. Heavy geometry and quantities UI thread se bahar compute hon.

First release sirf supported block/surface workflows ka reliable modeller hoga. Advanced pit/ramp design, fault modelling, geological interpolation, implicit solids and geostatistics separate capabilities hain.

### 6.4 Coal-specific modelling roadmap

Coal planning must preserve roof/floor/seam and parting identities where supplied, not turn every source into undifferentiated cubes. The first pilot imports validated block quantities and reference surfaces; subsequent geometry work can derive clipped strip/bench quantities from approved boundaries and roof/floor surfaces. Negative seam thickness, gaps, crossing surfaces and overlapping volumes require explicit errors or engineer-reviewed treatments.

Advanced design backlog includes strip/pit boundary editing, validated closed-solid operations, bench/berm/ramp geometry, spoil/dump capacity and stage development. Dragline range/positioning, dozer-push limits, rehandle, coal-cleaning loss/dilution and blast exclusion/access rules are specialised methods with their own units, constraints and fixtures. Initially represent supported tasks and engineer-supplied rates/sequences; do not label generic excavator scheduling as a calibrated dragline model. Drill/blast activity sequencing does not imply blast-hole or charge-design software.

Long-, medium- and short-term plans need explicit resolution and aggregation contracts. A monthly strategic bucket is not precise shift dispatch. Carry immutable parent targets and reconcile the disaggregated plan; a lower-resolution plan's apparent feasibility does not prove short-term face access or fleet feasibility.

## 7. Scheduling engine ka engineering contract

### 7.1 Input model

An activity has stable ID, source revision, geometry references, quantity by material, unit, eligible resource types, allowed destinations, predecessors, release/deadline, minimum working chunk, splitting policy, priority and optional locks.

Resources have stable IDs, pool membership, capabilities, shift availability, planned maintenance, mutually exclusive assignments, and rate rules with units. Calendars include site timezone, shifts, breaks, planned outages and exception dates. Period intervals use [start, end) to avoid double-counting boundaries. Store instants in UTC and retain site timezone for shifts/reports.

MVP time representation should be fixed, documented shift/hour buckets rather than silently mixing continuous timestamps and period totals. Jobs may continue into later buckets only under the declared split/preemption policy. A follow-on finer resolution changes the model and must be revalidated.

### 7.2 Quantities and productivity

- In-situ tonnes = bank volume × in-situ density, using compatible units and wet/dry basis.
- Loose volume = bank volume × declared swell factor; never apply swell again to mass.
- Basic time demand = scheduled quantity / compatible effective production rate.
- Where a nameplate rate and separate factors are used: effective rate = nameplate rate × availability factor × utilisation factor × other explicit deratings. If availability already removes hours from a calendar, do not multiply it into the rate again. Rate configuration must state which convention is active.
- Minimum equipment transfer/setup time and access restrictions apply independently of dig quantity.
- Coal/ore recovery and mining loss/dilution must be explicit transformations; they are not interchangeable with density or swell.

### 7.3 Constraints

Hard constraints: precedence and lag, enabled work periods, resource exclusivity/capacity, compatible task assignment, activity quantity limit, access availability, protected/frozen work, destination capacity, and stock non-negativity. Maximum concurrent faces, exclusion zones and material exposure rules become mandatory only when configured and validated for the site.

Precedence example: finish(A) + lag ≤ start(B). For partially released work, use explicit sub-activities or validated overlap semantics; do not let a single finish-to-start edge pretend to support partial exposure. Spatial assumptions such as bench access, safe batter distance or coal exposure are engineer-defined; a generic angle alone does not prove a safe mine plan.

Soft constraints: target tonnes, target quality ranges, preferred sequence, changeover reduction, overtime, movement distance and schedule deviation. The system shall show units, penalties and violations; hidden weights must not decide a plan.

### 7.4 Baseline algorithm

1. Validate import, geometry references, units, dates and IDs.
2. Expand rule templates into explicit dependency/resource constraints.
3. Detect cycles, broken references and direct lock/calendar conflicts.
4. Build a deterministic eligible-activity priority queue.
5. Allocate feasible work against remaining calendar/resource/destination capacity using stable tie-breakers.
6. Carry legitimate remaining work to later periods, respecting minimum chunk and continuation policy.
7. Stop with a complete feasible schedule, a partial schedule with unscheduled work, or a clear infeasibility/error result.
8. Run an independent result validator before allowing publication.

The greedy baseline is useful and explainable, but is not a proof of global feasibility or optimality. Failure of a heuristic to find a plan is not automatically a mathematical infeasibility proof. Status must distinguish “no plan found by this method” from “model proven infeasible.”

### 7.5 Optimisation

Begin with OR-Tools CP-SAT or another reviewed solver on a carefully bounded subset; benchmark before committing to every-mine scale. CP-SAT requires integer variables: document quantity/time scaling, rounding limits and overflow limits. Revalidate decoded results in original engineering units. A model with stock blends, equipment routes and millions of blocks may need aggregation, decomposition, rolling horizons and specialised heuristics rather than one giant model.

Use lexicographic objectives where possible: first satisfy hard rules; then meet ranked production commitments; then reduce penalties/costs. If weighted objectives are used, document scales and units. Report solver/version, method, random seed, limits, objective, best bound/gap when meaningful, and elapsed time. “Feasible,” “optimal,” “proven infeasible,” “time limit with incumbent,” “no solution found,” “cancelled,” and “error” must remain distinct.

### 7.6 Haulage and material movement

Configured cycle time = load + loaded travel + dump + empty travel + explicit fixed/queue delays. Effective truck rate uses payload and that cycle under a single declared availability convention. Fleet capacity is shared across assigned routes; one truck cannot simultaneously serve two destinations. Shovel loading and truck arrival constraints can form different bottlenecks.

Simple constant travel time is acceptable for the first haulage module if labelled. Grade/rolling resistance, speed limits, intersections, road closure, queue interaction and stochastic dispatch need later calibrated models. Do not describe a static capacity calculation as discrete-event simulation.

### 7.7 Stocks, blending and quality

For each material/destination/time bucket: closing stock = opening stock + receipts − reclaim − declared losses, all on a consistent mass basis. Reclaimed material may create a downstream feed transaction, but consolidated system totals must eliminate internal transfers. Keep bank material, loose volume, ROM coal and saleable product as distinct quantities.

Weighted quality q = sum(m_i × q_i) / sum(m_i) only where quantities and quality bases are compatible. Ash, moisture, energy and contaminant models may need dry-mass or energy corrections; nonlinear properties require approved property-specific mixing rules. Wet/dry and as-received conversions need measured/configured moisture and declared equations. Empty stock quality is undefined, not zero.

Simple perfectly mixed stockpiles are a declared assumption. FIFO, LIFO, layered and spatial reclaim rules are later selectable models; changing the model creates a new scenario revision.

## 8. Architecture aur technology selection

### 8.1 Recommended structure

**Browser UI → authenticated API → project/domain services → durable job queue → isolated geometry/scheduling workers → versioned metadata/results → browser/report exports.** Server authoritative hoga; browser UI result inspection aur interactive scene rendering karegi. Source/quantity validation aur scheduling ko client par trust na karein.

| Layer | Proposed technology | Reason / boundary |
| --- | --- | --- |
| Web frontend | React + TypeScript; Vite for an authenticated SPA | UI, tables, Gantt and scene state; SEO/SSR primary requirement nahi |
| 3D | Three.js + Web Workers + spatial index | Browser rendering; chunked geometry, local render origin, LOD and selection |
| API/domain services | Python + FastAPI + typed schemas | Mining calculations and API contracts; begin as a modular monolith |
| Background jobs | Redis + RQ, with durable job state in PostgreSQL | Heavy work HTTP request se bahar; retries, cancellation and recovery |
| Scheduling | Deterministic Python baseline; OR-Tools after bounded spike | Explainable feasible plan first; truthful optimiser status |
| Geometry/data processing | Selected validated libraries, NumPy, Arrow | Supported operations only; stream large datasets and test numerics |
| Project metadata | PostgreSQL | Transactions, identities/project membership, revisions, jobs and audit |
| Large immutable data | Parquet/Arrow in private S3-compatible storage | Source files, meshes, blocks, results and exports; self-hosted storage possible |
| Analytics | Isolated DuckDB/Arrow query workers | Read immutable datasets; avoid copying full block tables into PostgreSQL/browser |
| Identity | Standards-based OIDC provider | Enterprise SSO or self-hosted identity; do not invent browser-only authentication |
| Deployment | Containers + reverse proxy/HTTPS | Linux VM/on-prem or approved cloud; Kubernetes later only if needed |
| Verification | pytest/property tests, API tests, Playwright and load tests | Engineering truth, project isolation, browser behavior and operational recovery |

Ye stack proposal hai, already installed/validated MESSI system nahi. Early spikes upload/geometry streaming, renderer precision, job recovery and numerical performance benchmark karein. Mandatory GPU/browser feature detection honi chahiye; unsupported client ko useful message dein. WebGPU-only design tab tak na choose karein jab tak target fleet validate na ho.

### 8.2 Team concurrency and immutable runs

Project/scenario objects carry revision numbers. Mutating request expected revision bheje; stale update HTTP 409/conflict response aur diff/context de. Initial release optimistic concurrency use kar sakti hai; Google-Docs-style simultaneous geometry editing zaroori nahi. Optional short edit leases expire safely and are not the source of truth.

Run inputs are an immutable snapshot manifest: source datasets, unit schema, calendars, rates, dependencies, settings and scenario revision. Kisi user ke concurrent edits running/completed schedule ko mutate na karein. Publish approved immutable run, not an editable scenario pointer. Reviewer aur approver permissions project policy mein defined hon.

### 8.3 Jobs, persistence and recovery

Each job has idempotency key, input manifest hash, owner/project, engine version, state, progress, heartbeat, resource limits, cancellation flag and result manifest. PostgreSQL is authoritative for durable job/result state. Queue delivery can happen more than once: workers must be idempotent and use leases/compare-and-set state transitions. A restart reconciliation job repairs queued/running state without silently rerunning non-idempotent commits.

Heavy jobs run in isolated processes/containers, not API event loops. Enforce CPU/memory/time limits and fair per-project concurrency. Cooperative cancellation checkpoints release resources; terminated output stays staged and unpublished. Progress is delivered by SSE/WebSocket or polling; reconnect fetches authoritative job state. Browser tab close does not cancel an authorised server job unless explicitly requested.

Upload source files into a private quarantine/staging area. Validate type/signature, byte limits, schema, archive expansion ratio and safe paths before promotion. Use resumable/multipart upload for large files; hash uploaded content. Never execute uploaded scripts or trust a filename extension.

Write data/results to immutable object keys, verify hashes/validation, then commit a manifest reference in PostgreSQL. An outbox/reconciliation/garbage-collection protocol handles failures between object-store and database operations; the two systems are not magically one atomic transaction. Do not delete datasets referenced by any approved/recoverable revision. DuckDB reads immutable copies/partitions and does not independently rewrite authoritative project metadata.

### 8.4 Authentication, access and data protection

All app/API traffic uses HTTPS. OIDC-based login, secure sessions, CSRF protection where cookie sessions are used, input validation and server-side project authorization are required from the pilot. Deploy SPA and API under a controlled same-origin configuration where practical. Long-lived credentials do not belong in browser localStorage.

Every API command, job status, dataset query, object download and export checks project/organisation scope. Private object buckets use short-lived scope-limited signed access only after authorization. Never trust a client-supplied project ID as proof of permission. Background jobs use scoped service credentials and do not accept arbitrary paths or shell expressions. PostgreSQL row-level security may provide defence in depth, but application-level project authorization and cross-project tests remain mandatory.

Audit who changed/imported/reran/approved/exported what, with revision IDs and timestamps. Diagnostic logs should not include raw geological tables, personal data, tokens or signed URLs. Credentials stay in managed server secrets. Encryption, retention, backup location and data residency follow the organisation's requirements; using an Australian timezone does not prove Australian data residency.

### 8.5 Deployment and operating model

Development uses documented container startup or native development commands with pinned dependencies. Local fixtures and test identities must be synthetic and clearly separate from production. A single Linux VM may run an early controlled pilot with API, workers, Redis, PostgreSQL and private object storage, but backup and failure boundaries must be explicit. Production sizing/high availability follow measured concurrency and recovery needs, not marketing expectations.

Internet-independent on-prem deployment is possible if the organisation hosts the application, storage and identity provider on its internal network and supplies offline dependency updates. This is different from a browser tab performing offline planning: first release requires connectivity to its server. Desktop offline sync is a later separately designed capability.

Proposed initial operational targets: metadata recovery point objective up to 24 hours and recovery time objective up to 4 hours for a pilot, subject to stakeholder approval. Production mine requirements may be stricter. Backups need a consistent metadata/object reference cutoff, protected retention and fresh-staging restore tests. Monitoring covers API errors, job wait/runtime, failed workers, object-store capacity, DB health and backup age. A deployment is not validated just because containers are running.

### 8.6 Suggested new product repository

Keep the new product separate from the existing operational hub unless a later integration task is approved.

- apps/web — authenticated UI, Gantt and 3D scene.
- services/api — identity integration, projects, revisions and commands.
- engine/domain — quantities, units, materials, calendars and invariants.
- engine/geometry — import validation, indexes and supported geometry.
- engine/scheduling — heuristic, solver adapters and independent validator.
- workers — job lifecycle, resource limits, staging and result publication.
- packages/contracts — versioned schemas and generated interface types.
- infrastructure — container builds, HTTPS config, storage and restore runbooks.
- tests/fixtures — synthetic/reference projects and expected outputs.
- tests/engineering — numerical, calendar and constraint cases.
- tests/security — project isolation, permission and file-upload cases.
- tests/e2e — supported-browser and concurrent-user workflows.
- docs — SRS, architecture decisions, data dictionary and operating guides.

## 9. Canonical data model aur contracts

| Entity | Required content |
| --- | --- |
| Project | ID, name, CRS/datum/local origin, unit schema, timezone, schema version, organisation/project access scope |
| ModelRevision | Source hashes, import mapping, author, timestamp, validation status |
| Surface/Mesh | Revision, vertices/faces references, reference frame, topology status |
| BlockPartition | ID, immutable dataset reference, schema, extents and index |
| MaterialDefinition | Type, density basis, quantity units, quality property schemas |
| PlanningUnit | Pit/stage/strip/bench/seam/block path with stable IDs |
| Activity | Planning unit, geometry/source refs, quantities, task type and split policy |
| Dependency | Upstream/downstream IDs, relation, lag and originating rule |
| Resource / Calendar | Capabilities, units, rates, shifts, exceptions and maintenance |
| Destination / Stock | Geometry ref, capacity, inventory and quality/reclaim model |
| Movement / StockLedger | Source/destination, time, material, mass/volume basis, lineage |
| ScenarioRevision | Parent, immutable overrides, input dataset revisions and approvals |
| ScheduleRun | Input hash, engine/solver versions, settings, seed and truthful status |
| Allocation | Activity, time interval/bucket, resource, quantity and destination |
| ConstraintViolation | Rule, affected IDs, severity, explanation and quantified residual |
| ActualsBatch | Source, import hash, deduplication key, reconciliation state |
| PublishedPlan | Approved immutable run, reviewer, rationale and report checksums |

Use stable UUIDs or deterministic stable IDs; display names are editable labels, not foreign keys. Units and nullability form part of schema. Missing density is unknown and blocks tonnes conversion; it is never silently 1.0. Unbounded targets, zero values, missing values and disabled rules are distinct.

Job/API commands include import.preview, import.commit, model.validate, scenario.branch, schedule.precheck, schedule.run, job.cancel, schedule.validate, report.export and project.backup/restore. Large files travel by managed file references, not giant JSON payloads. Requests carry expected revision so stale edits fail visibly. Repeated commits use idempotency keys.

## 10. User interface specification

Workspace layout: project/layer tree on left, central 3D viewport, contextual properties/validation panel on right, Gantt/time slider and job progress below. Large tables open in dedicated views rather than overloading the viewport.

Required screens:

1. Project launcher with last revision, health and backup state.
2. Import/mapping wizard with source preview, units, CRS and reject report.
3. 3D model workspace with layer legends, selection and cross-section.
4. Planning units and activity editor with source quantity lineage.
5. Equipment/rates/calendars editor with visible effective capacity.
6. Sequence and rule manager with dependency graph and conflict navigation.
7. Schedule/Gantt with locks, milestones, filter and impact preview.
8. Stocks, destinations and quality balance view.
9. Scenario comparison using the same horizon, units and price basis.
10. Reports and plan review/publication.
11. Actuals reconciliation and variance reporting in a later release.
12. Settings, diagnostics, import history and restore workflow.

Every result screen shows scenario revision, run status and units. Stale outputs show “inputs changed; rerun required.” Manual overrides require a reason, audit entry and validation. UI may permit a planner to explore an infeasible draft, but cannot publish it as a feasible approved plan.

## 11. Non-functional requirements aur proposed targets

These are initial acceptance targets, not measured performance claims. Agree benchmark data and hardware in discovery; revise targets if measurements justify it.

| ID | Proposed requirement | Verification |
| --- | --- | --- |
| NFR-001 | Core import, model inspection, baseline scheduling and reports work through authenticated HTTPS | Clean Chrome/Edge test with project permissions; interrupted-network behavior tested separately |
| NFR-002 | Reference client: Windows 11, current Chrome/Edge, 16 GB RAM, agreed WebGL2 GPU. Initial server benchmark: 16 vCPU, 64 GB RAM, SSD, bounded worker concurrency | Publish actual browser/GPU and server/container configuration; sizing is a benchmark assumption |
| NFR-003 | Navigate a 1M-block attributes dataset and 2M-triangle scene through aggregation/LOD; aim at 30 fps under documented visible load | Median/p95 frame-time, selection correctness and peak memory measurements |
| NFR-004 | Baseline 10,000 activities × 365 daily periods × 50 resource pools within 60 seconds on benchmark workload | Representative sparse constraints; p95 over fixed runs; solver optimization has a separate user-set time budget |
| NFR-005 | Metadata edits commit atomically; crash cannot corrupt last published plan | Fault injection during saves and result publication |
| NFR-006 | Identical inputs/engine/settings reproduce physical results within declared tolerances | Deterministic heuristic; solver version/threads/settings recorded; no unwarranted bit-identical cross-platform promise |
| NFR-007 | All published quantities trace to input revisions and transformations | Automated lineage completeness checks |
| NFR-008 | Import rejection and infeasibility errors actionable with row/object IDs | User acceptance against deliberately broken fixtures |
| NFR-009 | No credential or confidential model content in ordinary diagnostics | Log/export inspection; crash bundle opt-in with redaction |
| NFR-010 | Versioned container builds, verified dependencies, SBOM and controlled rollback | CI/staging deployment, rollback, dependency-integrity and access tests |
| NFR-011 | Server backup and restore includes PostgreSQL metadata, object datasets and revision manifests | Fresh staging restore, consistent snapshot/cutoff, hash/count/recomputed-results checks |
| NFR-012 | Long jobs report progress, remain cancellable and release worker resources | Cancellation at import, geometry, scheduling and export checkpoints |
| NFR-013 | Initial pilot benchmark: 10 concurrent planners, up to 2 heavy jobs active; small metadata requests aim p95 < 500 ms excluding network | Publish workload, server limits, queue latency and large-query exceptions; target, not measured claim |
| NFR-014 | Cross-project isolation on every data access path | Negative API, export, signed-object-link, job-stream and background-worker tests |

Define numeric tolerances per operation. Simple analytical block tests may target 1e-9 relative arithmetic agreement; mesh-volume tolerances depend on tessellation/source accuracy and must not inherit that number blindly. Rendering measurements, coordinates, quantities and financial rounding each need separate tolerances. Never round authoritative tonnes early just to make a report look tidy.

## 12. Test strategy aur engineering acceptance

Testing begins with tiny hand-checkable projects; a large schedule that “looks right” is weak evidence.

| Test ID | Fixture / action | Expected evidence |
| --- | --- | --- |
| ENG-001 | Ten disjoint 10 × 10 × 10 m blocks at 2.5 t/m³ | 10,000 m³ and 25,000 t before declared transformations |
| ENG-002 | Metres and feet variants with known local origin | Same physical dimensions/tonnes after explicit conversion |
| ENG-003 | Open mesh and incompatible CRS/vertical datum | Reject quantity calculation or require declared supported conversion |
| ENG-004 | A → B → C and an injected C → A edge | Valid order first; cycle objects and rule IDs reported second |
| ENG-005 | Exclusive excavator on overlapping activities | No simultaneous exclusive assignments after scheduling |
| ENG-006 | Non-working shift and maintenance shutdown | Zero assigned work inside unavailable time |
| ENG-007 | Locked date conflicting with predecessor/calendar | Actionable conflict; no silent lock removal |
| ENG-008 | 1,000 t at 10% ash plus 1,000 t at 20%, same dry basis | 2,000 t at 15% ash; incompatible basis case rejected |
| ENG-009 | 100 t opening + 80 receipt − 50 reclaim − 5 loss | 125 t closing; reclaim cannot exceed available inventory |
| ENG-010 | Route cycle: 5 min load + 10 loaded + 2 dump + 8 return + 5 delay | 30 min cycle; 100 t payload → 200 t/h before declared derating |
| ENG-011 | 100 t/h for 8 working hours; downtime represented once | 800 t gross; chosen convention applies each factor exactly once |
| ENG-012 | Impossible hard target and a separate soft shortfall | Hard-model status correctly explained; soft case reports quantified penalty |
| ENG-013 | Same deterministic heuristic input and stable tie-breaks | Same allocation and validation results |
| ENG-014 | Cancellation/power-loss injection during staged output | Last committed revision reopenable; incomplete result not published |
| ENG-015 | Compare Gantt, 3D animation, stock ledger and export | Same period/material totals; no internal-transfer double-counting |
| ENG-016 | Small solver instance with exhaustive enumerated optimum | Correct optimum/status; time-limited case not falsely called optimal |
| ENG-017 | Calendar across DST transition in a non-Brisbane project | Correct UTC instants and real working duration; no duplicate shift hours |
| ENG-018 | New scenario changes rate after baseline publication | Original results unchanged; new run references new inputs |
| ENG-019 | Clean supported browser, no developer runtimes, HTTPS | Login → import → view → schedule → report → close/reopen succeeds |
| ENG-020 | Database/object backup restored to fresh staging | All referenced hashes and published outputs match; no production messages dispatched |
| ENG-021 | Planner from project A requests project B data/job/export | Denied without disclosing private object content |
| ENG-022 | Two users edit same scenario revision | One success, one explicit conflict; no silent lost update |
| ENG-023 | Same job delivered twice; worker crashes after staged upload | One committed result; lease/state reconciliation safe |
| ENG-024 | Uploaded archive contains traversal paths or excessive expansion | Rejected/quarantined within resource limits |
| ENG-025 | Browser disconnects during schedule job, then reconnects | Job continues; progress/result reloaded from authoritative state |
| ENG-026 | Viewer attempts publish/admin action by direct API call | Server rejects regardless of hidden/visible UI controls |

Also use property-based checks for conservation, quantity limits and resource capacity; mutation tests for the validator where useful; fuzz tests for malformed files; and large synthetic performance tests. Where a legacy planning tool is available, compare matched inputs/rules and explain differences. Numerical agreement with another package does not replace validation of real operating assumptions.

**Pilot acceptance gate:** a mine planner and independent reviewer accept source reconciliation, dependency/access rules, physical capacity, period production, stock/quality balance, limitations and exported reports. Publishing requires zero unexplained hard-constraint violations and complete provenance. Software does not certify geotechnical safety or reserves.

## 13. Delivery roadmap aur realistic resourcing

Estimate assumptions: one open-cut pilot, supplied usable reference models, no new geological estimator, no universal CAD compatibility, prompt access to planners, and an experienced multidisciplinary team. Durations are planning ranges, not a quote; overlapping workstreams can shorten elapsed time.

| Stage | Indicative duration | Deliverable / exit gate |
| --- | --- | --- |
| 0 — Discovery and risk spikes | 3–4 weeks | Site workflows, 3 gold datasets, signed scope, upload/job pipeline/3D precision benchmarks |
| 1 — First vertical slice | 4–6 weeks | Small CSV blocks → 3D → activities → simple feasible schedule → CSV report through authenticated browser UI |
| 2 — Reliable planning foundation | 6–8 weeks | Import pipeline, project revisions, geometry validation, resources/calendars and engineering fixtures |
| 3 — Operational pilot scheduling | 8–12 weeks | Full baseline, Gantt/locks, stock/quality tracking, scenario comparison, pilot calibration |
| 4 — Hardening and controlled release | 6–10 weeks | Crash tests, deployment/restore drills, performance, user manuals and independent review |
| 5 — Advanced modules | Further 6–18+ months | Optimisation, detailed haulage, advanced design, advanced collaboration and uncertainty per approved SRS |

A controlled useful pilot commonly needs roughly 6–9 months under these assumptions; a robust commercial product may require 12–18 months, and broad mature-suite coverage 18–30+ months. Discovery will replace these ranges with a team-specific plan. One prompt or one engineer cannot responsibly deliver and validate the entire mature scope in a few weeks.

Recommended core team: 1 product lead/business analyst, 1 senior mine-planning domain lead, 1 technical lead, 2 engine/optimisation engineers, 1 graphics/geometry engineer, 1–2 web/frontend engineers, 1 QA automation engineer, and part-time deployment/security/UX specialists. Pilot planners/surveyors/geologists also need allocated review time. A 3–4 person team can build a narrower prototype; it should reduce scope rather than promise the same delivery date.

Budget model: sum(each role's loaded monthly rate × allocated months) + equipment + test/review data preparation + build/deployment infrastructure + optional SDK/solver licences + support/training + contingency. Obtain local rates before quoting currency totals. Reserve roughly 20–30% contingency initially for geometry, legacy formats, web-scale data handling and model calibration risk; refine using discovery results.

## 14. Major risks aur engineering decisions

| Risk | Required mitigation |
| --- | --- |
| Bad input data appears plausible in 3D | Mandatory import validation and quantity reconciliation before schedules |
| GPU coordinates lose precision | Float64 authoritative coordinates, local render origin, round-trip tests |
| Schedule model too large | Aggregate blocks to mineable units; benchmark; decompose/rolling horizon |
| Incorrect production from double-counted downtime | One documented rate/calendar convention plus engineering fixtures |
| Geometry engine cannot do robust solids | Limit first release geometry; prototype accepted operations; reject unsupported cases |
| Quality/volume/stock bases mixed | Typed units and bases; ledger; explicit conversions; engineer review |
| GUI edits bypass constraints | All edits through domain commands; independent validation before publish |
| Large models overload browser/network | Chunking, LOD, scoped caching, upload recovery and agreed browser/GPU benchmarks |
| Training features mistaken for approved requirements | Source-to-requirement mapping with evidence and applicability status |
| Concurrent team edits overwrite work | Server revisions, optimistic concurrency, immutable run inputs and explicit conflict UI |
| Vendor/proprietary format lock-in | Canonical open data model and round-trip exports; reviewed adapters |
| Optimiser emits misleading claims | Explicit solution status, limits, residual checks and method provenance |

Architecture decision records should cover team identity, PostgreSQL/object-store consistency, worker isolation, queue recovery, quantity bases, calendar semantics, scheduling resolution, geometry formats, solver choice and plan-publication rules.

## 15. Configuration aur customisation strategy

User requirements ko scattered hard-coded conditions mein convert na karein. Versioned project configuration mein material schemas, task types, rate units, equipment eligibility, work calendars, destinations, priorities, target bands and report definitions store hon. Changes new scenario revision create karein. New engineering algorithms reviewed plugins/modules hon, arbitrary untrusted Python pasted into the UI nahi.

Configuration examples: coal/waste and seam names; site hierarchy; excavator compatibility; minimum mining chunk; maintenance dates; target production per shift/month; stock limits; weather derating; quality band; approved sequencing rules; currency; financial period definition. Every field ka unit, allowed range, default/required state and effect documented ho.

External integration contracts may later accept survey updates, fleet actuals, laboratory assays and ERP costs. They require timestamp/revision provenance, deduplication, explicit trust boundary and reconciliation, not direct overwrite of active planning records.

## 16. Definition of done aur first implementation instruction

A feature done tab hai jab typed contract, working implementation, server-side permissions, negative/error cases, relevant engineering fixtures, UI behavior, team-concurrency behavior, persistence/reopen and documented limitations verified hon. New algorithms need independent numerical or enumerated reference checks. “Build passes” ya placeholder UI engineering acceptance nahi.

First implementation task should be a narrow end-to-end slice: a 10-block synthetic CSV import with unit/CRS metadata, selectable 3D blocks, activity generation, one equipment calendar, a deterministic precedence-constrained schedule and reconciled CSV output. Deploy it behind HTTPS with real project authorization and exercise save/reopen plus a two-user stale-edit conflict. Do not start by building every screen with mocked numbers.

No application code is implemented by this document. Existing checkout files are not changed. Development begins in a separately agreed product repository/task.

## 17. Open decisions for discovery

Required before site-specific engineering acceptance:

- Detailed open-cut coal methods, material process and planning horizon/time resolution; broad mine type is already confirmed.
- Representative models, format versions, CRS, vertical datum and property dictionary.
- Pilot activity/block counts and available planner workstation specification.
- Existing rate conventions, calendars, shift boundaries and practical access rules.
- Product/ROM quality bases, yield/recovery rules and stock management assumptions.
- Required equipment/haulage fidelity and validated travel/rate data.
- Hosting/data-residency policy, company data handling, network restrictions and browser support.
- Definition of an approved plan, reviewers and acceptance datasets.
- Team, budget, timeline and commercial/open-source distribution preference.

These are refinement decisions. They do not block this proposal or the small synthetic vertical slice; they do block claims that an operational site plan is validated.

## 18. LMS videos/transcripts ko SRS mein convert karne ka process

Use only material the user is authorised to access/export. Passwords, session cookies or bearer tokens chat mein na mangein. Platform-approved authentication or exported transcripts/PDFs/course files use karein. A course URL with user/account query parameters alone authenticated session establish nahi karta; share reports mein learner identifiers repeat na karein.

1. Course/module/lesson inventory create karein with stable IDs and title.
2. For every authorised lesson, record availability: full video viewed, transcript reviewed, audio reviewed, attachments reviewed, partial, inaccessible or missing.
3. Preserve original transcript; add timecodes and document uncertain auto-transcription/mining terms. Transcript-only review ko video-visual review na label karein.
4. Extract each demonstrated user goal, input, command, domain rule, output, exception and configuration dependency.
5. Evidence tag use karein: documented/demonstrated, inferred, proposed, contradictory or unknown. Do not invent exact menu labels from a transcript gap.
6. Map to a proposed MESSI requirement and independent acceptance test. Record whether equivalent functionality is necessary for the user's mine.
7. Resolve duplicate/conflicting demonstrations by lesson/software version and stakeholder review.
8. Independently design interaction, schema and algorithms. Exact branding/assets, proprietary code or private interfaces copy na karein.
9. Maintain coverage: reviewed lessons / accessible inventory; requirements mapped / requirements requiring evidence. Unknown total ko “all videos reviewed” na likhein.

Traceability columns: source_id, module, lesson, software_version, timestamp_or_page, material_type, review_status, evidence_type, observed_workflow, proposed_requirement_id, acceptance_test_id, applicability, unresolved_question.

**Material milne par next deliverable:** evidence-linked feature catalogue, missing-content list, updated SRS, SPRY training observations versus MESSI proposed scope comparison, and revised implementation priorities. Yeh current document mein verified analysis ke taur par included nahi hai.

## 19. Deliverable pack ka istemal

- MESSI-Development-Blueprint-SRS.md: complete proposed blueprint/SRS baseline.
- MESSI-Master-Development-Prompt.md: reusable instruction for an AI development assistant/team.
- MESSI-Requirements-Traceability.csv: proposed requirements and test mapping; course evidence initially unreviewed.
- Word copies: sharing/review ke liye; Markdown is pack ka editable source hai.

Master prompt mein confirmed open-cut coal/browser-team direction retain karein aur baqi assumptions ko apne site data se refine karein. Phir pehle discovery plus vertical slice demand karein; full mature product ko ek single untested code dump mein request na karein.

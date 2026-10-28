# Engineering contracts · release 0.1

## Supported model

This release treats each block as an axis-aligned, non-overlapping rectangular mining unit and one splittable mining activity. Coordinates are the **minimum corner**, not centroid. Internal coordinates/dimensions are metres, density is always tonnes/m³, quantities are tonnes and m³. CSV coordinate input may be metres or feet (exact factor 0.3048); density is not converted when coordinate units change. Declared project CRS and vertical datum are retained; no reprojection/geoid transform is attempted. Float64 Python/JS values are authoritative; Three.js buffers use a local render origin.

Required CSV columns: `id,x,y,z,dx,dy,dz,density,material,basis,destination`.
Optional: `ash,predecessors,priority,locked_start,locked_resource`.

- `material`: coal or waste.
- `basis`: dry or as_received; density-derived mass and ash use this same declared basis. No wet/dry conversion is performed.
- Coal requires ash (0–100%). Waste ash may be empty.
- `predecessors`: semicolon-separated block IDs. References must exist; duplicates/self-edges are rejected. Cycles are reported by precheck and prevent job submission.
- `destination`: an existing compatible material/basis destination; sample project uses `rom` and `dump`.
- `locked_start`: ISO date at the site's shift start, or ISO timestamp with an explicit UTC offset. A lock is exact, not a “no earlier than” date.
- `locked_resource`: optional existing resource ID, subject to material compatibility.

Imports reject missing/non-finite values, non-positive dimensions/density, overlapping interiors, duplicate IDs and invalid destinations/bases. Touching faces are permitted. Maximums: 2 MB CSV, 2,000 blocks, 50 resource pools, 366-day horizon and 10 reference surfaces. Complete scenario snapshots, including retained sources, are limited to 4 MB; HTTP requests are limited to 5 MB. No million-block performance claim is made.

OBJ supports `v x y z` and positive-index triangular `f i j k`, plus object/group/smoothing labels. Texture/normal face references, negative indices, polygons, materials and other statements are explicitly unsupported. Topology checks reject invalid indices, degenerate triangles and non-manifold edges. Closed-edge topology does **not** prove orientation, non-self-intersection, safe solid geometry or geological validity. All surfaces are for visual reference; surface import never changes block volumes. Maximum 20,000 vertices and 40,000 triangles per surface. No DXF/DWG/Parquet reader is implemented yet.

## Quantities and quality

- Bank volume = dx × dy × dz.
- In-situ mass = bank volume × declared compatible density.
- Effective rate = resource rate (t/working hour) × utilisation (0–1).
- Time demand = mass / effective rate.
- Maintenance removes working windows; no separate availability multiplier is applied, preventing double-counting downtime.
- Closing destination stock = opening + scheduled receipts.
- For coal stocks on a common supported basis, ash = (opening mass × opening ash + sum(receipt mass × receipt ash)) / closing mass.

Empty stock quality is undefined/null. Coal opening mass needs opening ash. Mixed dry/as-received receipts to a destination are rejected. There is no plant yield, recovery, dilution, swell, stock reclaim/loss transaction, energy blending or moisture conversion in this release. They are not silently assumed to be zero-loss physical processes; their absence is an explicit model limitation. Reclaim/loss output fields are zero because those operations cannot be entered or scheduled yet.

## Calendar and baseline heuristic

Work shifts are same-day windows defined in a project IANA timezone. Store allocation instants as UTC, use [start,end) boundaries, and compute real elapsed time across DST. Same-day shift patterns only: shift_start + shift_hours ≤ 24. Whole-date maintenance exceptions apply per resource. No overlapping shift patterns or overtime are modelled.

The deterministic serial schedule generator chooses eligible activities by ascending priority then stable ID. It evaluates compatible resource free windows, chooses the earliest completion with resource-ID tie-breaks, and splits work across available shift windows as necessary. A block is allocated in full or left unscheduled. Finish-to-start dependencies have zero lag. Each resource is exclusive and has one homogeneous production rate.

Destination capacity is cumulative opening + receipts, with no reclaim. Locks, preceding work and finite horizons can prevent this heuristic from finding a plan. Results are `feasible`, `partial`, `no_plan_found`, `invalid`, or job lifecycle states (`queued`, `running`, `cancelled`, `error`). **No optimizer is implemented, and these results never claim optimality or a mathematical infeasibility proof.**

An independent validator checks elapsed-time/rate reconciliation, material eligibility, resource/date locks, working windows/outages, resource overlap, precedence, block quantity conservation, destination capacity/basis, stocks/weighted ash, daily production and headline totals. Approval reruns this validator against the run's immutable snapshot.

## Editing and publication

Block geometry/density/ash, dependencies, priorities and locks are edited through the inspector; save validates the complete scenario and increments its revision atomically. The Gantt is an inspection/selection view, not drag-and-drop scheduling. Manual date changes use inspector locks. A completed run is not automatically updated after edits. Its original snapshot and result remain immutable; the UI marks them stale for the changed scenario.

Each run records its SHA-256 input hash, engine version, project reference metadata, scenario revision, allocation ledger and result. Exports derive from that same result. Approval records the reviewer and time and preserves the exact run. It does not certify reserves, geotechnical safety or practical site acceptance.

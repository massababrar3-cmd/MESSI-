"""Unit-aware import contracts. Authoritative coordinates are float64 Python floats."""

from __future__ import annotations
import csv, io, math, hashlib, json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Literal

MAX_BLOCKS = 2000


class DomainError(ValueError):
    pass


class Block(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=80)
    x: float = Field(ge=-1e9, le=1e9)
    y: float = Field(ge=-1e9, le=1e9)
    z: float = Field(ge=-1e9, le=1e9)
    dx: float = Field(gt=0, le=100000)
    dy: float = Field(gt=0, le=100000)
    dz: float = Field(gt=0, le=100000)
    density: float = Field(gt=0, le=20)
    material: Literal["coal", "waste"]
    basis: Literal["dry", "as_received"]
    ash: float | None = Field(default=None, ge=0, le=100)
    predecessors: list[str] = Field(default_factory=list, max_length=200)
    priority: int = Field(default=100, ge=0, le=10000)
    destination: str = Field(min_length=1, max_length=80)
    locked_start: str | None = None
    locked_resource: str | None = None

    @field_validator("locked_start")
    @classmethod
    def lock_date(cls, value):
        if not value:
            return None
        if len(value) == 10:
            date.fromisoformat(value)
        else:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                raise ValueError("Lock timestamp needs an explicit UTC offset")
        return value

    @model_validator(mode="after")
    def check(self):
        if self.material == "coal" and self.ash is None:
            raise ValueError("Coal requires ash and its mass basis")
        if len(self.predecessors) != len(set(self.predecessors)):
            raise ValueError("Duplicate predecessors")
        if self.id in self.predecessors:
            raise ValueError("Activity cannot depend on itself")
        return self

    @property
    def volume(self):
        return self.dx * self.dy * self.dz

    @property
    def tonnes(self):
        return self.volume * self.density


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    rate: float = Field(gt=0, le=1000000, description="tonnes per working hour")
    utilization: float = Field(default=1, gt=0, le=1)
    materials: list[Literal["coal", "waste"]] = Field(min_length=1)
    outages: list[str] = Field(default_factory=list, max_length=366)

    @field_validator("outages")
    @classmethod
    def dates(cls, v):
        for x in v:
            date.fromisoformat(x)
        return v


class Destination(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    material: Literal["coal", "waste"]
    basis: Literal["dry", "as_received"]
    capacity: float = Field(gt=0, le=1e12)
    opening: float = Field(default=0, ge=0)
    opening_ash: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def check(self):
        if self.opening > self.capacity:
            raise ValueError("Opening exceeds stock capacity")
        if self.material == "coal" and self.opening and self.opening_ash is None:
            raise ValueError("Coal opening stock needs ash")
        return self


class Calendar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: str
    days: int = Field(default=30, ge=1, le=366)
    shift_start: int = Field(default=6, ge=0, le=23)
    shift_hours: int = Field(default=12, ge=1, le=24)
    weekdays: list[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4, 5], min_length=1, max_length=7
    )

    @model_validator(mode="after")
    def check(self):
        date.fromisoformat(self.start)
        if self.shift_start + self.shift_hours > 24:
            raise ValueError("This release supports same-day shifts only")
        if len(set(self.weekdays)) != len(self.weekdays) or any(
            d < 0 or d > 6 for d in self.weekdays
        ):
            raise ValueError("Invalid weekdays")
        return self


class Surface(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    vertices: list[tuple[float, float, float]] = Field(min_length=3, max_length=20000)
    faces: list[tuple[int, int, int]] = Field(min_length=1, max_length=40000)
    source_hash: str
    original_obj: str = Field(max_length=2_000_000)
    closed: bool = False

    @model_validator(mode="after")
    def geometry(self):
        edges = {}
        for vertex in self.vertices:
            if any(abs(v) > 1e9 for v in vertex):
                raise ValueError("Surface coordinates exceed supported range")
        for face in self.faces:
            if len(set(face)) != 3 or min(face) < 0 or max(face) >= len(self.vertices):
                raise ValueError("Invalid triangle index")
            a, b, c = [self.vertices[i] for i in face]
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            cross = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            ]
            if sum(x * x for x in cross) < 1e-16:
                raise ValueError("Degenerate triangle")
            for i, j in [(face[0], face[1]), (face[1], face[2]), (face[2], face[0])]:
                key = tuple(sorted((i, j)))
                edges[key] = edges.get(key, 0) + 1
        if any(count > 2 for count in edges.values()):
            raise ValueError("Non-manifold triangle edge")
        # Watertight topology alone does not establish a valid non-self-intersecting solid.
        self.closed = all(count == 2 for count in edges.values())
        return self


def parse_obj(content: str, units="m", name="Imported terrain"):
    if units not in ["m", "ft"]:
        raise DomainError("Coordinate units must be m or ft")
    factor = 1 if units == "m" else 0.3048
    vertices = []
    faces = []
    for n, line in enumerate(content.splitlines(), 1):
        parts = line.split("#", 1)[0].split()
        if not parts:
            continue
        try:
            if parts[0] == "v":
                if len(parts) != 4:
                    raise ValueError("Vertex must have x y z only")
                vertices.append(tuple(float(x) * factor for x in parts[1:]))
            elif parts[0] == "f":
                if len(parts) != 4 or any("/" in x for x in parts[1:]):
                    raise ValueError(
                        "Only positive-index triangular faces without texture/normal indices are supported"
                    )
                face = tuple(int(x) - 1 for x in parts[1:])
                if min(face) < 0:
                    raise ValueError("OBJ indices must be positive")
                faces.append(face)
            elif parts[0] not in ["o", "g", "s"]:
                raise ValueError("Unsupported OBJ statement: " + parts[0])
            if len(vertices) > 20000 or len(faces) > 40000:
                raise ValueError("Surface exceeds 20,000 vertices / 40,000 triangles")
        except ValueError as exc:
            raise DomainError(f"OBJ line {n}: {exc}")
    try:
        return Surface(
            id="surface-" + hashlib.sha256(content.encode()).hexdigest()[:16],
            name=name,
            vertices=vertices,
            faces=faces,
            source_hash=hashlib.sha256(content.encode()).hexdigest(),
            original_obj=content,
        ).model_dump()
    except ValueError as exc:
        raise DomainError(str(exc)[:1000])


class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blocks: list[Block] = Field(max_length=MAX_BLOCKS)
    surfaces: list[Surface] = Field(default_factory=list, max_length=10)
    resources: list[Resource] = Field(min_length=1, max_length=50)
    destinations: list[Destination] = Field(min_length=1, max_length=100)
    calendar: Calendar
    timezone: str = "Australia/Brisbane"
    source: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check(self):
        ZoneInfo(self.timezone)
        for name, items in [
            ("blocks", self.blocks),
            ("resources", self.resources),
            ("destinations", self.destinations),
            ("surfaces", self.surfaces),
        ]:
            ids = [i.id for i in items]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate {name} IDs")
        ids = {b.id for b in self.blocks}
        dest = {d.id: d for d in self.destinations}
        resources = {r.id for r in self.resources}
        for b in self.blocks:
            missing = set(b.predecessors) - ids
            if missing:
                raise ValueError(f"{b.id}: missing predecessors {sorted(missing)}")
            if b.destination not in dest:
                raise ValueError(f"{b.id}: unknown destination")
            d = dest[b.destination]
            if (d.material, d.basis) != (b.material, b.basis):
                raise ValueError(f"{b.id}: destination material/mass basis mismatch")
            if b.locked_resource and b.locked_resource not in resources:
                raise ValueError(f"{b.id}: unknown locked resource")
        # Sweep X to reject interior overlap; touching faces are allowed.
        active = []
        for b in sorted(self.blocks, key=lambda b: b.x):
            active = [a for a in active if a.x + a.dx > b.x + 1e-8]
            for a in active:
                if (
                    min(a.y + a.dy, b.y + b.dy) - max(a.y, b.y) > 1e-8
                    and min(a.z + a.dz, b.z + b.dz) - max(a.z, b.z) > 1e-8
                ):
                    raise ValueError(f"Overlapping blocks: {a.id} and {b.id}")
            active.append(b)
        if len(json.dumps(self.model_dump(), allow_nan=False).encode()) > 4_000_000:
            raise ValueError(
                "Project snapshot exceeds 4 MB pilot limit, including retained originals"
            )
        return self


def input_hash(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def parse_csv(content: str, units="m"):
    if units not in ["m", "ft"]:
        raise DomainError("Coordinate units must be m or ft")
    factor = 1 if units == "m" else 0.3048
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    required = {
        "id",
        "x",
        "y",
        "z",
        "dx",
        "dy",
        "dz",
        "density",
        "material",
        "basis",
        "destination",
    }
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise DomainError("Missing columns: " + ", ".join(sorted(missing)))
    blocks = []
    errors = []
    for n, row in enumerate(reader, 2):
        if n > MAX_BLOCKS + 1:
            raise DomainError(f"Maximum {MAX_BLOCKS} blocks per import in this release")
        try:
            if None in row:
                raise ValueError("Extra values or malformed CSV quoting")
            b = {k: (row.get(k) or "").strip() for k in required}
            for k in ["x", "y", "z", "dx", "dy", "dz"]:
                b[k] = float(b[k]) * factor
            b["density"] = float(
                b["density"]
            )  # density always t/m3, independent of coordinate units
            b["ash"] = float(row["ash"]) if row.get("ash", "").strip() else None
            b["predecessors"] = [
                x.strip() for x in (row.get("predecessors") or "").split(";") if x.strip()
            ]
            b["priority"] = int(row.get("priority") or 100)
            b["locked_start"] = (row.get("locked_start") or "").strip() or None
            b["locked_resource"] = (row.get("locked_resource") or "").strip() or None
            blocks.append(Block.model_validate(b).model_dump())
        except (ValueError, TypeError) as e:
            errors.append({"row": n, "message": str(e)[:450]})
    if not blocks and not errors:
        raise DomainError("CSV contains no data rows")
    return {
        "blocks": blocks,
        "errors": errors,
        "source_hash": hashlib.sha256(content.encode()).hexdigest(),
        "coordinate_input_unit": units,
        "density_unit": "t/m3",
        "volume": sum(Block(**b).volume for b in blocks),
        "tonnes": sum(Block(**b).tonnes for b in blocks),
    }


def sample_inputs():
    blocks = []
    for i in range(5):
        for material, z, density in [("waste", 220, 2.5), ("coal", 210, 1.4)]:
            bid = f"{'OB' if material == 'waste' else 'CL'}-{i + 1:03}"
            blocks.append(
                dict(
                    id=bid,
                    x=642000 + i * 40,
                    y=7490000,
                    z=z,
                    dx=40,
                    dy=40,
                    dz=10,
                    density=density,
                    material=material,
                    basis="dry",
                    ash=9 + i * 1.4 if material == "coal" else None,
                    predecessors=[f"OB-{i + 1:03}"] if material == "coal" else [],
                    priority=i + 1,
                    destination="rom" if material == "coal" else "dump",
                )
            )
    return Inputs(
        blocks=blocks,
        resources=[
            Resource(id="ex-01", name="EX-01 · Waste fleet", rate=4200, materials=["waste"]),
            Resource(id="ex-02", name="EX-02 · Coal fleet", rate=2400, materials=["coal"]),
        ],
        destinations=[
            Destination(
                id="dump", name="West waste dump", material="waste", basis="dry", capacity=1000000
            ),
            Destination(id="rom", name="North ROM", material="coal", basis="dry", capacity=300000),
        ],
        calendar=Calendar(start="2026-11-02"),
        source={"kind": "synthetic", "name": "Synthetic open-cut coal pilot; not a surveyed mine"},
    ).model_dump()

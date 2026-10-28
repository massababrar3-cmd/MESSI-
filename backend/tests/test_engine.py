from copy import deepcopy
import math
import pytest
from messi.domain import Inputs, Block, DomainError, parse_csv, sample_inputs, input_hash
from messi.scheduler import schedule, validate_result, working_windows


def simple():
    d = sample_inputs()
    d["blocks"] = []
    for i in range(10):
        d["blocks"].append(
            {
                "id": f"B{i}",
                "x": i * 10,
                "y": 0,
                "z": 0,
                "dx": 10,
                "dy": 10,
                "dz": 10,
                "density": 2.5,
                "material": "waste",
                "basis": "dry",
                "ash": None,
                "predecessors": [],
                "priority": i,
                "destination": "dump",
            }
        )
    return d


def test_analytic_volume_and_mass():
    d = simple()
    r = schedule(d)
    assert r["status"] == "feasible"
    assert r["totals"]["volume"] == 10000
    assert r["totals"]["tonnes"] == 25000
    assert not validate_result(d, r)


def test_sample_coal_waste_balance_and_quality():
    d = sample_inputs()
    r = schedule(d)
    assert r["totals"] == dict(tonnes=312000, coal=112000, waste=200000, volume=160000)
    stock = next(s for s in r["stocks"] if s["id"] == "rom")
    assert stock["ash"] == pytest.approx(11.8)
    assert stock["closing"] == 112000
    assert sum(p["coal"] for p in r["periods"]) == r["totals"]["coal"]


def test_determinism_and_source_hash():
    d = sample_inputs()
    assert schedule(d) == schedule(deepcopy(d))
    assert input_hash(d) == input_hash(deepcopy(d))
    d["resources"][0]["rate"] += 1
    assert input_hash(d) != input_hash(sample_inputs())


def test_precedence_and_exclusive_resources():
    d = sample_inputs()
    r = schedule(d)
    tasks = {a["id"]: a for a in r["activities"]}
    for b in d["blocks"]:
        for p in b["predecessors"]:
            assert tasks[b["id"]]["start"] >= tasks[p]["end"]
    for res in d["resources"]:
        rows = sorted(
            [a for a in r["allocations"] if a["resource_id"] == res["id"]], key=lambda a: a["start"]
        )
        assert all(a["end"] <= b["start"] for a, b in zip(rows, rows[1:]))


def test_cycle_diagnostic_not_optimality_claim():
    d = sample_inputs()
    d["blocks"][0]["predecessors"] = ["CL-001"]
    r = schedule(d)
    assert r["status"] == "no_plan_found"
    assert "cycle" in r["violations"][0]


def test_outages_and_non_working_days():
    d = sample_inputs()
    d["resources"][0]["outages"] = ["2026-11-02"]
    r = schedule(d)
    assert r["status"] == "feasible"
    assert all(
        not (a["resource_id"] == "ex-01" and a["start"].startswith("2026-11-01"))
        for a in r["allocations"]
    )
    assert not validate_result(d, r)


def test_locks_cannot_be_silently_removed():
    d = sample_inputs()
    d["blocks"][1]["locked_start"] = "2026-11-02"
    r = schedule(d)
    assert r["status"] == "partial"
    assert "Locked start" in next(x["reason"] for x in r["unscheduled"] if x["id"] == "CL-001")
    assert d["blocks"][1]["locked_start"] == "2026-11-02"


def test_destination_capacity_rejects_whole_activity():
    d = sample_inputs()
    d["destinations"][1]["capacity"] = 1000
    r = schedule(d)
    assert r["status"] == "partial"
    assert r["totals"]["coal"] == 0
    assert len(r["unscheduled"]) == 5
    assert all(s["closing"] <= s["capacity"] for s in r["stocks"])


def test_missing_density_incompatible_basis_and_overlap():
    d = sample_inputs()
    del d["blocks"][0]["density"]
    with pytest.raises(ValueError):
        Inputs.model_validate(d)
    d = sample_inputs()
    d["blocks"][1]["basis"] = "as_received"
    with pytest.raises(ValueError, match="basis mismatch"):
        Inputs.model_validate(d)
    d = sample_inputs()
    d["blocks"][2]["x"] = d["blocks"][0]["x"]
    with pytest.raises(ValueError, match="Overlapping blocks"):
        Inputs.model_validate(d)


def test_validator_detects_rate_and_capacity_tampering():
    d = sample_inputs()
    r = schedule(d)
    r["allocations"][0]["tonnes"] *= 2
    assert any("rate/time mismatch" in e for e in validate_result(d, r))
    r = schedule(d)
    r["totals"]["coal"] = 0
    assert "coal: result total mismatch" in validate_result(d, r)
    r = schedule(d)
    r["stocks"][0]["closing"] = 0
    assert "Stock ledger mismatch" in validate_result(d, r)


def test_empty_coal_stock_quality_is_undefined():
    d = sample_inputs()
    d["blocks"] = []
    r = schedule(d)
    assert next(s for s in r["stocks"] if s["id"] == "rom")["ash"] is None


def test_quality_and_opening_inventory():
    d = sample_inputs()
    d["blocks"] = [deepcopy(d["blocks"][1])]
    b = d["blocks"][0]
    b["predecessors"] = []
    b.update(dx=10, dy=10, dz=10, density=1, ash=20)
    d["destinations"][1].update(opening=1000, opening_ash=10)
    stock = next(s for s in schedule(d)["stocks"] if s["id"] == "rom")
    assert stock["closing"] == 2000
    assert stock["ash"] == 15


def test_utilisation_is_applied_once():
    d = simple()
    d["blocks"] = d["blocks"][:1]
    d["resources"][0].update(rate=1000, utilization=0.5)
    assert sum(a["hours"] for a in schedule(d)["allocations"]) == 5


def test_calendar_uses_real_elapsed_time_at_dst_transition():
    d = simple()
    d["blocks"] = d["blocks"][:1]
    d["blocks"][0].update(dx=10, dy=10, dz=5, density=1)
    d["resources"][0].update(rate=100, utilization=1)
    d.update(timezone="America/New_York")
    d["calendar"].update(start="2026-11-01", days=1, shift_start=0, shift_hours=4, weekdays=[6])
    r = schedule(d)
    assert r["status"] == "feasible"
    assert r["allocations"][0]["hours"] == 5
    assert r["allocations"][0]["end"] == "2026-11-01T09:00:00+00:00"


def test_csv_units_reconcile_and_row_errors():
    header = "id,x,y,z,dx,dy,dz,density,material,basis,destination\n"
    m = parse_csv(header + "A,0,0,0,10,10,10,2.5,waste,dry,dump\n")
    ft = parse_csv(
        header + f"A,0,0,0,{10 / 0.3048},{10 / 0.3048},{10 / 0.3048},2.5,waste,dry,dump\n", "ft"
    )
    assert ft["tonnes"] == pytest.approx(m["tonnes"])
    assert parse_csv(header + "A,0,0,0,nan,10,10,2.5,waste,dry,dump\n")["errors"]
    with pytest.raises(DomainError):
        parse_csv("x,y\n1,2\n")


def test_zero_rate_and_missing_quality_rejected():
    d = sample_inputs()
    d["resources"][0]["rate"] = 0
    with pytest.raises(ValueError):
        Inputs.model_validate(d)
    d = sample_inputs()
    d["blocks"][1]["ash"] = None
    with pytest.raises(ValueError):
        Inputs.model_validate(d)


def test_surface_obj_validates_topology_without_claiming_volume():
    from messi.domain import parse_obj

    mesh = parse_obj("v 0 0 0\nv 10 0 0\nv 0 10 0\nf 1 2 3\n")
    assert not mesh["closed"]
    assert len(mesh["faces"]) == 1
    with pytest.raises(DomainError, match="Degenerate"):
        parse_obj("v 0 0 0\nv 1 1 1\nv 2 2 2\nf 1 2 3\n")
    with pytest.raises(DomainError, match="Unsupported"):
        parse_obj("v 0 0 0\nmtllib arbitrary.mtl\n")
    with pytest.raises(DomainError, match="Invalid triangle"):
        parse_obj("v 0 0 0\nv 10 0 0\nv 0 10 0\nf 1 2 99\n")


def test_independent_quality_and_period_tamper_detection():
    d = sample_inputs()
    r = schedule(d)
    r["stocks"][1]["ash"] = 0
    assert any("weighted quality mismatch" in x for x in validate_result(d, r))
    r = schedule(d)
    r["periods"][0]["waste"] = 0
    assert "Period production mismatch" in validate_result(d, r)


def test_deep_dependency_graph_does_not_exceed_python_recursion_limit():
    from messi.scheduler import graph_issues

    d = simple()
    base = d["blocks"][0]
    d["blocks"] = []
    for i in range(1100):
        d["blocks"].append(
            {**base, "id": f"B{i}", "x": i * 10, "predecessors": [f"B{i - 1}"] if i else []}
        )
    assert graph_issues(Inputs.model_validate(d)) == []

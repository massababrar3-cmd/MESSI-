import csv, io, json, zipfile
import pytest
from sqlalchemy import select, update
from messi.db import Session, Scenario, Run, Audit
from messi.worker import process_once
from .conftest import login


def run_job(client, headers, key="test-run-0001"):
    r = client.post(
        f"/api/scenarios/{client.ids['scenario']}/runs",
        json={"revision": 1, "idempotency_key": key},
        headers=headers,
    )
    assert r.status_code == 202, r.text
    assert process_once()
    r = client.get("/api/runs/" + r.json()["id"])
    assert r.status_code == 200
    return r.json()


def test_authentication_csrf_origin_and_logout(client):
    assert client.get("/api/projects").status_code == 401
    h = login(client)
    assert client.get("/api/projects").status_code == 200
    assert (
        client.post("/api/auth/logout", headers={"origin": "http://testserver"}).status_code == 403
    )
    assert (
        client.post(
            "/api/auth/logout", headers={**h, "origin": "https://untrusted.invalid"}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout", headers=h).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_project_isolation_on_scenarios_runs_exports_and_members(client):
    h = login(client)
    r = run_job(client, h)
    login(client, "outsider")
    assert client.get("/api/projects").json() == []
    for path in [
        f"/projects/{client.ids['project']}/scenarios",
        f"/scenarios/{client.ids['scenario']}",
        f"/runs/{r['id']}",
        f"/runs/{r['id']}/export/json",
        f"/projects/{client.ids['project']}/members",
        f"/projects/{client.ids['project']}/audit",
    ]:
        assert client.get("/api" + path).status_code == 404, path


def test_viewer_cannot_edit_run_or_approve(client):
    owner = login(client)
    run = run_job(client, owner)
    h = login(client, "viewer")
    s = client.get("/api/scenarios/" + client.ids["scenario"]).json()
    assert (
        client.put(
            "/api/scenarios/" + s["id"],
            json={"revision": s["revision"], "inputs": s["inputs"]},
            headers=h,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/scenarios/{s['id']}/runs",
            json={"revision": 1, "idempotency_key": "viewer-not-allowed"},
            headers=h,
        ).status_code
        == 403
    )
    assert client.post("/api/runs/" + run["id"] + "/approve", headers=h).status_code == 403
    assert client.get("/api/runs/" + run["id"] + "/export/csv").status_code == 200


def test_optimistic_revision_conflict_and_immutable_snapshot(client):
    h = login(client)
    run = run_job(client, h)
    sid = client.ids["scenario"]
    s = client.get("/api/scenarios/" + sid).json()
    s["inputs"]["resources"][0]["rate"] = 1000
    body = {"revision": 1, "inputs": s["inputs"]}
    changed = client.put("/api/scenarios/" + sid, json=body, headers=h)
    assert changed.status_code == 200
    assert changed.json()["revision"] == 2
    assert client.put("/api/scenarios/" + sid, json=body, headers=h).status_code == 409
    original = client.get("/api/runs/" + run["id"]).json()
    assert original["revision"] == 1
    assert original["snapshot"]["resources"][0]["rate"] == 4200


def test_branch_does_not_mutate_parent(client):
    h = login(client)
    sid = client.ids["scenario"]
    b = client.post(
        f"/api/scenarios/{sid}/branch", json={"name": "Alternative", "revision": 1}, headers=h
    )
    assert b.status_code == 201
    s = b.json()
    s["inputs"]["resources"][0]["rate"] = 2500
    assert (
        client.put(
            "/api/scenarios/" + s["id"], json={"revision": 1, "inputs": s["inputs"]}, headers=h
        ).status_code
        == 200
    )
    assert client.get("/api/scenarios/" + sid).json()["inputs"]["resources"][0]["rate"] == 4200


def test_job_idempotency_completion_and_approval(client):
    h = login(client)
    sid = client.ids["scenario"]
    body = {"revision": 1, "idempotency_key": "duplicate-000001"}
    a = client.post(f"/api/scenarios/{sid}/runs", json=body, headers=h)
    b = client.post(f"/api/scenarios/{sid}/runs", json=body, headers=h)
    assert a.json()["id"] == b.json()["id"]
    assert process_once()
    assert not process_once()
    rid = a.json()["id"]
    r = client.get("/api/runs/" + rid).json()
    assert r["status"] == "feasible"
    assert not r["result"]["violations"]
    reviewer = login(client, "reviewer")
    approved = client.post(f"/api/runs/{rid}/approve", headers=reviewer)
    assert approved.status_code == 200
    assert approved.json()["approved_by"] == "reviewer"


def test_queued_cancellation_and_stale_worker_lease(client):
    h = login(client)
    sid = client.ids["scenario"]
    r = client.post(
        f"/api/scenarios/{sid}/runs",
        json={"revision": 1, "idempotency_key": "cancel-00001"},
        headers=h,
    ).json()
    assert client.post("/api/runs/" + r["id"] + "/cancel", headers=h).status_code == 200
    assert not process_once()
    assert client.get("/api/runs/" + r["id"]).json()["status"] == "cancelled"
    r = client.post(
        f"/api/scenarios/{sid}/runs",
        json={"revision": 1, "idempotency_key": "lease-retry-0001"},
        headers=h,
    ).json()
    with Session.begin() as db:
        db.execute(
            update(Run)
            .where(Run.id == r["id"])
            .values(status="running", heartbeat=0, worker_token="dead-worker")
        )
    assert process_once()
    assert client.get("/api/runs/" + r["id"]).json()["status"] == "feasible"


def test_import_preview_atomic_commit_and_source_provenance(client):
    h = login(client)
    sid = client.ids["scenario"]
    header = "id,x,y,z,dx,dy,dz,density,material,basis,destination\n"
    bad = header + "A,0,0,0,-10,10,10,2.5,waste,dry,dump\n"
    p = client.post(
        f"/api/scenarios/{sid}/import-preview", files={"file": ("bad.csv", bad)}, headers=h
    )
    assert p.status_code == 200
    assert p.json()["errors"]
    assert (
        client.post(
            f"/api/scenarios/{sid}/import", json={"revision": 1, "content": bad}, headers=h
        ).status_code
        == 422
    )
    assert len(client.get("/api/scenarios/" + sid).json()["inputs"]["blocks"]) == 10
    good = header + "A,0,0,0,10,10,10,2.5,waste,dry,dump\n"
    imported = client.post(
        f"/api/scenarios/{sid}/import", json={"revision": 1, "content": good}, headers=h
    )
    assert imported.status_code == 200
    assert imported.json()["inputs"]["source"]["original_csv"] == good
    assert imported.json()["revision"] == 2
    assert len(imported.json()["inputs"]["blocks"]) == 1


def test_exports_reconcile_and_audit(client):
    h = login(client)
    r = run_job(client, h)
    rid = r["id"]
    response = client.get(f"/api/runs/{rid}/export/csv")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert sum(float(a["tonnes"]) for a in rows) == pytest.approx(r["result"]["totals"]["tonnes"])
    assert all(a["input_hash"] == r["input_hash"] for a in rows)
    assert client.get(f"/api/runs/{rid}/export/pdf").content.startswith(b"%PDF")
    xlsx = client.get(f"/api/runs/{rid}/export/xlsx")
    assert zipfile.is_zipfile(io.BytesIO(xlsx.content))
    archive = client.get(f"/api/runs/{rid}/export/json").json()
    assert archive["manifest"]["input_hash"] == r["input_hash"]
    assert archive["snapshot"] == r["snapshot"]
    events = client.get(f"/api/projects/{client.ids['project']}/audit").json()
    assert sum(a["action"] == "run.exported" for a in events) == 4


def test_membership_permissions_and_cycle_precheck(client):
    h = login(client)
    pid = client.ids["project"]
    sid = client.ids["scenario"]
    assert (
        client.post(
            f"/api/projects/{pid}/members",
            json={"email": "outsider@test.invalid", "role": "viewer"},
            headers=h,
        ).status_code
        == 200
    )
    s = client.get("/api/scenarios/" + sid).json()
    s["inputs"]["blocks"][0]["predecessors"] = ["CL-001"]
    assert (
        client.put(
            "/api/scenarios/" + sid, json={"revision": 1, "inputs": s["inputs"]}, headers=h
        ).status_code
        == 200
    )
    assert client.get(f"/api/scenarios/{sid}/precheck").json()["issues"]
    assert (
        client.post(
            f"/api/scenarios/{sid}/runs",
            json={"revision": 2, "idempotency_key": "cyclic-00001"},
            headers=h,
        ).status_code
        == 422
    )
    login(client, "outsider")
    assert len(client.get("/api/projects").json()) == 1


def test_tampered_result_cannot_be_approved(client):
    h = login(client)
    r = run_job(client, h)
    with Session.begin() as db:
        row = db.get(Run, r["id"])
        result = dict(row.result)
        result["totals"] = {**result["totals"], "coal": 0}
        row.result = result
    assert client.post("/api/runs/" + r["id"] + "/approve", headers=h).status_code == 409


def test_reference_surface_import_retains_blocks_and_original_source(client):
    h = login(client)
    sid = client.ids["scenario"]
    obj = "v 642000 7490000 230\nv 642200 7490000 230\nv 642000 7490100 235\nf 1 2 3\n"
    body = {"revision": 1, "content": obj, "name": "Reference survey", "units": "m"}
    preview = client.post(f"/api/scenarios/{sid}/surface-preview", json=body, headers=h)
    assert preview.status_code == 200
    assert not preview.json()["surface"]["closed"]
    result = client.post(f"/api/scenarios/{sid}/surface", json=body, headers=h)
    assert result.status_code == 200
    assert len(result.json()["inputs"]["blocks"]) == 10
    assert result.json()["inputs"]["surfaces"][0]["original_obj"] == obj
    assert (
        client.post(
            f"/api/scenarios/{sid}/surface", json={**body, "revision": 2}, headers=h
        ).status_code
        == 409
    )


def test_running_job_cancellation_cannot_publish_results(client, monkeypatch):
    h = login(client)
    sid = client.ids["scenario"]
    r = client.post(
        f"/api/scenarios/{sid}/runs",
        json={"revision": 1, "idempotency_key": "running-cancel-01"},
        headers=h,
    ).json()

    def interrupted(snapshot, progress):
        progress(0)
        with Session.begin() as db:
            db.get(Run, r["id"]).cancel_requested = 1
        progress(50)
        raise AssertionError("Cancellation should interrupt before returning a result")

    monkeypatch.setattr("messi.worker.schedule", interrupted)
    assert process_once()
    after = client.get("/api/runs/" + r["id"]).json()
    assert after["status"] == "cancelled"
    assert after["result"] is None


def test_simultaneous_duplicate_submission_returns_one_durable_job(client):
    from concurrent.futures import ThreadPoolExecutor

    h = login(client)
    sid = client.ids["scenario"]
    body = {"revision": 1, "idempotency_key": "concurrent-duplicate-01"}

    def submit(_):
        return client.post(f"/api/scenarios/{sid}/runs", json=body, headers=h)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, range(2)))
    assert all(r.status_code == 202 for r in responses), [r.text for r in responses]
    assert responses[0].json()["id"] == responses[1].json()["id"]
    assert process_once()
    assert not process_once()


def test_actual_stream_size_is_bounded_even_without_content_length(client):
    h = login(client)

    def chunks():
        for _ in range(6):
            yield b"x" * 1_000_000

    r = client.post(
        "/api/projects", content=chunks(), headers={**h, "content-type": "application/json"}
    )
    assert r.status_code == 413

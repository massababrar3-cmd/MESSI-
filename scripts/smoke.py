"""Exercise a real server + worker with synthetic data; never print credentials."""

from pathlib import Path
import os, json, time, uuid
import httpx

ROOT = Path(__file__).resolve().parents[1]
url = os.environ.get("MESSI_SMOKE_URL", "http://127.0.0.1:8000").rstrip("/")
accounts = json.loads(
    Path(
        os.environ.get("MESSI_ACCOUNTS_FILE", str(ROOT / ".local/bootstrap-users.json"))
    ).read_text()
)
owner = next(u for u in accounts if u["role"] == "owner")


def checked(response):
    if not response.is_success:
        raise RuntimeError(
            f"Smoke endpoint failed: HTTP {response.status_code}. Check server origin, installation account file and worker logs privately."
        )
    return response.json()


with httpx.Client(base_url=url, timeout=15) as client:
    auth = checked(
        client.post(
            "/api/auth/login",
            headers={"origin": url},
            json={"email": owner["email"], "password": owner["password"]},
        )
    )
    client.headers.update({"origin": url, "x-csrf-token": auth["csrf"]})
    project = checked(
        client.post(
            "/api/projects",
            json={
                "name": "Synthetic smoke check " + uuid.uuid4().hex[:8],
                "crs": "Synthetic local metre grid",
                "datum": "Synthetic RL",
                "timezone": "Australia/Brisbane",
                "sample": True,
            },
        )
    )
    run = checked(
        client.post(
            f"/api/scenarios/{project['scenario_id']}/runs",
            json={"revision": 1, "idempotency_key": str(uuid.uuid4())},
        )
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        result = checked(client.get("/api/runs/" + run["id"]))
        if result["status"] not in ["queued", "running"]:
            break
        time.sleep(0.25)
    assert result["status"] == "feasible", "Worker did not complete a feasible run"
    assert not result["result"]["violations"]
    assert result["result"]["totals"] == {
        "tonnes": 312000,
        "coal": 112000,
        "waste": 200000,
        "volume": 160000,
    }
    archive = checked(client.get("/api/runs/" + run["id"] + "/export/json"))
    assert archive["manifest"]["input_hash"] == result["input_hash"]
    checked(client.post("/api/auth/logout"))
print(
    json.dumps(
        {
            "functional_smoke": "passed",
            "model_blocks": 10,
            "coal_tonnes": 112000,
            "waste_tonnes": 200000,
            "validation_violations": 0,
            "export_hash_matches": True,
        }
    )
)

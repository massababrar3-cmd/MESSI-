import os, subprocess, json, sys
from pathlib import Path
import pytest
from messi.backup import backup, restore
from messi.db import Session, Run
from messi.worker import process_once
from .conftest import login


def test_logical_backup_fresh_restore_and_tamper_detection(client, tmp_path):
    h = login(client)
    sid = client.ids["scenario"]
    response = client.post(
        f"/api/scenarios/{sid}/runs",
        json={"revision": 1, "idempotency_key": "backup-test-0001"},
        headers=h,
    )
    assert response.status_code == 202
    assert process_once()
    rid = response.json()["id"]
    original = client.get("/api/runs/" + rid).json()
    path = tmp_path / "backup.json"
    counts = backup(path)
    assert counts["runs"] == 1
    assert "sessions" not in json.loads(path.read_text())["tables"]
    with pytest.raises(ValueError, match="nonempty"):
        restore(path)
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "MESSI_DATA_DIR": str(fresh),
        "DATABASE_URL": "sqlite:///" + str(fresh / "restored.db"),
    }
    script = """from pathlib import Path
import sys
from messi.backup import restore
from messi.db import Session,Run
from messi.scheduler import validate_result
restore(Path(sys.argv[1]))
with Session() as db:
 r=db.get(Run,sys.argv[2]);assert not validate_result(r.snapshot,r.result);assert r.result['totals']['tonnes']==312000
print('Fresh restore validated')"""
    check = subprocess.run(
        [sys.executable, "-c", script, str(path), rid], env=env, capture_output=True, text=True
    )
    assert check.returncode == 0, check.stderr
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        restore(path)

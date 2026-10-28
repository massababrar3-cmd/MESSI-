import os, tempfile, sys
from pathlib import Path

os.environ["MESSI_DATA_DIR"] = tempfile.mkdtemp(prefix="messi-tests-")
os.environ["DATABASE_URL"] = os.environ.get(
    "MESSI_TEST_DATABASE_URL", "sqlite:///" + os.environ["MESSI_DATA_DIR"] + "/test.db"
)
os.environ["MESSI_ORIGINS"] = "http://testserver"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from messi.api import app
from messi.db import Base, engine, Session, User, Project, Scenario, Member
from messi.domain import sample_inputs
from messi.security import hash_password


@pytest.fixture
def client():
    from messi.api import login_attempts

    login_attempts.clear()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session.begin() as db:
        users = {}
        for role in ["owner", "planner", "viewer", "outsider", "reviewer"]:
            u = User(
                email=role + "@test.invalid",
                name=role,
                password=hash_password("Synthetic-test-password-42"),
            )
            db.add(u)
            db.flush()
            users[role] = u.id
        p = Project(
            name="Test mine",
            crs="Local grid metres",
            datum="Test RL",
            timezone="Australia/Brisbane",
        )
        db.add(p)
        db.flush()
        for role in ["owner", "planner", "viewer", "reviewer"]:
            db.add(Member(project_id=p.id, user_id=users[role], role=role))
        s = Scenario(project_id=p.id, name="Baseline", inputs=sample_inputs())
        db.add(s)
        db.flush()
        ids = {"project": p.id, "scenario": s.id, **users}
    with TestClient(app) as c:
        c.ids = ids
        yield c


def login(client, role="owner"):
    r = client.post(
        "/api/auth/login",
        json={"email": role + "@test.invalid", "password": "Synthetic-test-password-42"},
        headers={"origin": "http://testserver"},
    )
    assert r.status_code == 200, r.text
    return {"origin": "http://testserver", "x-csrf-token": r.json()["csrf"]}

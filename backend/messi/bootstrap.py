"""Seed synthetic local pilot. Credentials are written privately, never logged."""

import json, os, secrets
from sqlalchemy import select
from .db import initialize, Session, User, Project, Member, Scenario, DATA
from .domain import sample_inputs
from .security import hash_password


def bootstrap():
    initialize()
    with Session.begin() as db:
        if db.scalar(select(User.id).limit(1)):
            return
        accounts = []
        users = []
        for key, name in [
            ("owner", "Planning lead"),
            ("planner", "Mine planner"),
            ("viewer", "Read-only reviewer"),
        ]:
            password = secrets.token_urlsafe(20)
            user = User(email=f"{key}@messi.local", name=name, password=hash_password(password))
            db.add(user)
            db.flush()
            users.append((user, key))
            accounts.append({"role": key, "email": user.email, "password": password})
        p = Project(
            name="Bowen Basin · Pilot",
            crs="Local engineering grid (metres)",
            datum="Synthetic RL (metres)",
            timezone="Australia/Brisbane",
        )
        db.add(p)
        db.flush()
        for user, role in users:
            db.add(Member(project_id=p.id, user_id=user.id, role=role))
        db.add(Scenario(project_id=p.id, name="Baseline plan", inputs=sample_inputs()))
        path = DATA / "bootstrap-users.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(accounts, f, indent=2)
    print(
        "Synthetic pilot prepared. Private credentials: .local/bootstrap-users.json (do not publish)."
    )


if __name__ == "__main__":
    bootstrap()

"""Private, versioned logical backup. Restore only into a completely empty database."""

import argparse, json, hashlib, os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, text
from .db import engine, Base, DATA, initialize

TABLES = [
    "users",
    "projects",
    "members",
    "scenarios",
    "runs",
    "audit",
]  # Sessions intentionally excluded.


def backup(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            conn = conn.execution_options(isolation_level="REPEATABLE READ")
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            conn.begin()
        data = {
            "schema_version": 1,
            "created": datetime.now(timezone.utc).isoformat(),
            "tables": {
                name: [
                    dict(row._mapping) for row in conn.execute(select(Base.metadata.tables[name]))
                ]
                for name in TABLES
            },
        }
        conn.rollback()
    raw = json.dumps(data, sort_keys=True, allow_nan=False).encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(raw)
    checksum = hashlib.sha256(raw).hexdigest()
    checkpath = path.with_suffix(path.suffix + ".sha256")
    fd = os.open(checkpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(checksum + "\n")
    return {name: len(rows) for name, rows in data["tables"].items()}


def restore(path: Path):
    raw = Path(path).read_bytes()
    expected = Path(str(path) + ".sha256").read_text().strip()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Backup checksum verification failed")
    data = json.loads(raw)
    if data.get("schema_version") != 1 or set(data.get("tables", {})) != set(TABLES):
        raise ValueError("Unsupported backup schema")
    initialize()
    with engine.begin() as conn:
        for name in TABLES + ["sessions"]:
            if conn.execute(select(Base.metadata.tables[name]).limit(1)).first():
                raise ValueError("Restore refuses a nonempty database; choose a fresh DATABASE_URL")
        for name in TABLES:
            rows = data["tables"][name]
            if name == "runs":
                for row in rows:
                    if row["status"] in ["queued", "running"]:
                        row.update(
                            status="cancelled",
                            worker_token=None,
                            error="Restored unfinished job; submit a new run explicitly",
                        )
            if rows:
                conn.execute(Base.metadata.tables[name].insert(), rows)
    return {name: len(rows) for name, rows in data["tables"].items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore", type=Path)
    args = parser.parse_args()
    if args.restore:
        print("Restored counts:", restore(args.restore))
    else:
        path = (
            DATA
            / "backups"
            / ("messi-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
        )
        print("Backup counts:", backup(path))
        print("Private backup path:", path)


if __name__ == "__main__":
    main()

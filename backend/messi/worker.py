"""Durable DB-backed pilot worker; CAS leases prevent duplicate result commits."""

import time, secrets, signal
from sqlalchemy import select, update
from .db import Session, Run, initialize
from .scheduler import schedule


class Cancelled(Exception):
    pass


class LeaseLost(Exception):
    pass


def process_once():
    stamp = time.time()
    token = secrets.token_hex(16)
    with Session.begin() as db:
        # Requeue abandoned leases after process loss. Completed results remain immutable.
        db.execute(
            update(Run)
            .where(Run.status == "running", Run.heartbeat < stamp - 120)
            .values(status="queued", worker_token=None)
        )
        rid = db.scalar(select(Run.id).where(Run.status == "queued").order_by(Run.created).limit(1))
        if not rid:
            return False
        claim = db.execute(
            update(Run)
            .where(Run.id == rid, Run.status == "queued")
            .values(status="running", worker_token=token, heartbeat=stamp, progress=0)
        )
        if claim.rowcount != 1:
            return True
        row = db.get(Run, rid)
        snapshot = row.snapshot

    def progress(value):
        with Session.begin() as db:
            r = db.get(Run, rid)
            if r.worker_token != token or r.status != "running":
                raise LeaseLost()
            if r.cancel_requested:
                raise Cancelled()
            r.progress = value
            r.heartbeat = time.time()

    try:
        progress(0)
        result = schedule(snapshot, progress)
        with Session.begin() as db:
            r = db.get(Run, rid)
            if r.worker_token != token or r.status != "running":
                raise LeaseLost()
            if r.cancel_requested:
                raise Cancelled()
            r.result = result
            r.status = result["status"]
            r.progress = 100
            r.heartbeat = time.time()
    except LeaseLost:
        pass
    except Cancelled:
        with Session.begin() as db:
            db.execute(
                update(Run)
                .where(Run.id == rid, Run.worker_token == token, Run.status == "running")
                .values(status="cancelled", progress=0)
            )
    except Exception as exc:
        with Session.begin() as db:
            db.execute(
                update(Run)
                .where(Run.id == rid, Run.worker_token == token, Run.status == "running")
                .values(status="error", error=f"{type(exc).__name__}: {str(exc)[:700]}")
            )
    return True


def main():
    initialize()
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print("MESSI durable planning worker started.")
    while not stopping:
        if not process_once():
            time.sleep(0.5)


if __name__ == "__main__":
    main()

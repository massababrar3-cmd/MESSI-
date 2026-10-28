from __future__ import annotations
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    event,
    String,
    Text,
    Integer,
    Float,
    JSON,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("MESSI_DATA_DIR", ROOT / ".local")).resolve()
DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA / 'messi.db'}")
engine = create_engine(
    URL,
    connect_args={"check_same_thread": False, "timeout": 30} if URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
if URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")


Session = sessionmaker(engine, expire_on_commit=False)


def uid():
    return str(uuid.uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(Text)


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    csrf: Mapped[str] = mapped_column(String)
    expires: Mapped[float] = mapped_column(Float)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    created: Mapped[str] = mapped_column(String, default=now)
    crs: Mapped[str] = mapped_column(String)
    datum: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String, default="Australia/Brisbane")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String)


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    inputs: Mapped[dict] = mapped_column(JSON)
    parent_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("scenario_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    revision: Mapped[int] = mapped_column(Integer)
    created: Mapped[str] = mapped_column(String, default=now)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(String)
    input_hash: Mapped[str] = mapped_column(String)
    snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    heartbeat: Mapped[float] = mapped_column(Float, default=0)
    worker_token: Mapped[str | None] = mapped_column(String, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[int] = mapped_column(Integer, default=0)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(Text)
    created: Mapped[str] = mapped_column(String, default=now)


def initialize():
    Base.metadata.create_all(engine)


def audit(db, project, actor, action, detail=""):
    db.add(Audit(project_id=project, actor=actor, action=action, detail=detail))

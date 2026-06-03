from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from rbccps_dashboard.config import DashboardSettings, get_settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: DashboardSettings | None = None) -> Engine:
    current = settings or get_settings()
    connect_args = {"check_same_thread": False} if current.database_url.startswith("sqlite") else {}
    if current.database_url.startswith("sqlite:///"):
        Path(current.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(current.database_url, connect_args=connect_args, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


engine = make_engine()
SessionLocal = make_session_factory(engine)


def init_db(bind: Engine | None = None) -> None:
    from rbccps_dashboard import models  # noqa: F401

    Base.metadata.create_all(bind=bind or engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

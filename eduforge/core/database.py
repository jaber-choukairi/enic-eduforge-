"""
EduForge — Database Engine & Session Management
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Generator, Type, TypeVar, Optional, List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from core.models import Base

# ── URL resolution — env var wins, then .env file, then hardcoded default ─────
# We resolve the URL here directly so there is no dependency on settings
# being fully loaded before the engine is created.

_DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or "postgresql://eduforge:eduforge@localhost:5432/eduforge"
)

print(f"[EduForge] Connecting to DB: {_DATABASE_URL}")

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_engine(
    _DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    Base.metadata.drop_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def health_check() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# ── Generic Repository ────────────────────────────────────────────────────────

T = TypeVar("T")


class BaseRepository:
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id: str) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: T) -> T:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: str) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

    def save(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
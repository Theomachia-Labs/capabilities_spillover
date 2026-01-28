"""Database connection and session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session, DeclarativeBase

# Default to a local SQLite file if not specified
DATABASE_URL = os.getenv("CSP_DATABASE_URL", "sqlite:///csp.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for ORM models."""
    pass


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Create all tables in the database."""
    # Import models here to ensure they are registered with Base
    from csp.data import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

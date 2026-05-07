"""Database configuration and initialization.

Exposes a Database facade that owns the SQLAlchemy engine and provides
schema initialization and session management.
Design pattern: same as Database class in the pizza reference project.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.engine import Engine


class Database:
    """Database facade — engine, schema init, and session management in one place."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        url = database_url or os.getenv("DATABASE_URL", "sqlite:///weatherguard.db")
        # check_same_thread=False is required because NiceGUI uses multiple threads
        self._engine: Engine = create_engine(
            url, echo=False, connect_args={"check_same_thread": False}
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def init_schema(self) -> None:
        """Create all tables (does nothing if they already exist)."""
        # Import models so SQLModel knows about them before create_all
        from domain.models import User, Location, WeatherThreshold, Alert  # noqa: F401
        SQLModel.metadata.create_all(self._engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional scope — commits on success, rolls back on error."""
        session = Session(self._engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def session(self) -> Session:
        """Return a plain session (caller is responsible for closing it)."""
        return Session(self._engine)

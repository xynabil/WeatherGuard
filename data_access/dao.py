"""DAO classes for persistence.

The rest of the application does not work with raw sessions.
DAOs encapsulate all CRUD operations behind simple class-based interfaces.
Design pattern: same as PizzaDAO / OrderDAO in the pizza reference project.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from domain.models import User, Location, WeatherThreshold, Alert


class BaseDAO:
    """Holds the engine and creates sessions."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _session(self) -> Session:
        return Session(self.engine)


class UserDAO(BaseDAO):
    """DAO for user accounts."""

    def get_by_username(self, username: str) -> Optional[User]:
        with self._session() as session:
            return session.exec(select(User).where(User.username == username)).first()

    def add(self, user: User) -> User:
        """Persist a new user and return it."""
        with self._session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_password(self, username: str, new_password: str) -> bool:
        """Update password for the given user. Returns True on success."""
        with self._session() as session:
            user = session.exec(select(User).where(User.username == username)).first()
            if not user:
                return False
            user.password = new_password
            session.add(user)
            session.commit()
            return True


class LocationDAO(BaseDAO):
    """DAO for locations and their thresholds."""

    def list_all(self, user_id: int = None) -> List[Location]:
        """Return locations for a user with thresholds eagerly loaded."""
        with self._session() as session:
            stmt = select(Location)
            if user_id is not None:
                stmt = stmt.where(Location.user_id == user_id)
            locs = list(session.exec(stmt).all())
            for loc in locs:
                _ = loc.thresholds  # force-load relationship
            return locs

    def get_by_id(self, location_id: int) -> Optional[Location]:
        """Return a single location with thresholds loaded."""
        with self._session() as session:
            loc = session.get(Location, location_id)
            if loc:
                _ = loc.thresholds
            return loc

    def add(self, location: Location) -> Location:
        """Persist a new location (with its thresholds) and return it."""
        with self._session() as session:
            session.add(location)
            session.commit()
            session.refresh(location)
            return location

    def delete(self, location_id: int) -> None:
        """Delete a location (cascades to thresholds and alerts)."""
        with self._session() as session:
            loc = session.get(Location, location_id)
            if loc:
                session.delete(loc)
                session.commit()


class AlertDAO(BaseDAO):
    """DAO for weather alerts."""

    def list_all(self, limit: int = 200, user_id: int = None) -> List[Alert]:
        """Return the most recent alerts for a user with location loaded."""
        with self._session() as session:
            stmt = select(Alert).order_by(Alert.created_at.desc())
            if user_id is not None:
                location_ids = [
                    loc.id for loc in session.exec(
                        select(Location).where(Location.user_id == user_id)
                    ).all()
                ]
                if not location_ids:
                    return []
                stmt = stmt.where(Alert.location_id.in_(location_ids))
            alerts = list(session.exec(stmt.limit(limit)).all())
            for a in alerts:
                _ = a.location
            return alerts

    def list_for_location(self, location_id: int) -> List[Alert]:
        with self._session() as session:
            return list(
                session.exec(select(Alert).where(Alert.location_id == location_id)).all()
            )

    def replace_for_location(self, location_id: int, new_alerts: List[Alert]) -> None:
        """Delete all existing alerts for a location and insert the new ones."""
        with self._session() as session:
            old = list(
                session.exec(select(Alert).where(Alert.location_id == location_id)).all()
            )
            for old_a in old:
                session.delete(old_a)
            for a in new_alerts:
                session.add(a)
            session.commit()

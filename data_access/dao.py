"""DAOs - Data Access Objects.

Eine DAO-Klasse kümmert sich um eine Tabelle und stellt einfache Methoden
zum Lesen, Hinzufügen und Löschen bereit. Der Rest der App ruft nur
diese Methoden auf - so muss man nirgends sonst SQL/SQLModel-Code schreiben.

Wir haben drei DAOs:
- UserDAO     - für Benutzer-Konten
- LocationDAO - für Standorte (mit ihren Grenzwerten)
- AlertDAO    - für Wetter-Warnungen
"""

from datetime import datetime
from sqlmodel import Session, select

from domain.models import User, Location, Alert


# ---------------------------------------------------------------------------
# UserDAO
# ---------------------------------------------------------------------------

class UserDAO:
    """Verwaltet Benutzer-Konten in der Datenbank."""

    def __init__(self, engine):
        self.engine = engine

    def get_by_username(self, username):
        """Sucht einen User anhand des Benutzernamens. None falls nicht gefunden."""
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            return session.exec(statement).first()

    def add(self, user):
        """Speichert einen neuen User in der Datenbank."""
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_password(self, username, new_password):
        """Ändert das Passwort. Gibt True zurück, wenn es geklappt hat."""
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if user is None:
                return False
            user.password = new_password
            session.add(user)
            session.commit()
            return True


# ---------------------------------------------------------------------------
# LocationDAO
# ---------------------------------------------------------------------------

class LocationDAO:
    """Verwaltet Standorte (mit ihren Grenzwerten) in der Datenbank."""

    def __init__(self, engine):
        self.engine = engine

    def list_all(self, user_id=None):
        """Gibt alle Standorte eines Users zurück (oder alle, wenn user_id=None)."""
        with Session(self.engine) as session:
            statement = select(Location)
            if user_id is not None:
                statement = statement.where(Location.user_id == user_id)
            locations = list(session.exec(statement).all())
            # Wichtig: thresholds laden, solange Session noch offen ist
            for loc in locations:
                _ = loc.thresholds
            return locations

    def get_by_id(self, location_id):
        """Sucht einen Standort anhand seiner ID."""
        with Session(self.engine) as session:
            location = session.get(Location, location_id)
            if location is not None:
                _ = location.thresholds  # thresholds laden
            return location

    def add(self, location):
        """Speichert einen neuen Standort (samt Grenzwerten)."""
        with Session(self.engine) as session:
            session.add(location)
            session.commit()
            session.refresh(location)
            return location

    def delete(self, location_id):
        """Löscht einen Standort. Grenzwerte und Alerts werden automatisch mit gelöscht."""
        with Session(self.engine) as session:
            location = session.get(Location, location_id)
            if location is not None:
                session.delete(location)
                session.commit()

    def update_thresholds(self, location_id, threshold_values):
        """Aktualisiert die Werte der Grenzwerte eines Standorts.

        threshold_values ist ein Dict: {threshold_id: neuer_wert, ...}
        """
        with Session(self.engine) as session:
            location = session.get(Location, location_id)
            if location is None:
                return
            for threshold in location.thresholds:
                if threshold.id in threshold_values:
                    threshold.value = threshold_values[threshold.id]
                    session.add(threshold)
            session.commit()
# ---------------------------------------------------------------------------
# AlertDAO
# ---------------------------------------------------------------------------

class AlertDAO:
    """Verwaltet Wetter-Warnungen in der Datenbank."""

    def __init__(self, engine):
        self.engine = engine

    def list_current(self, user_id=None):
        """Gibt nur die heutigen Alerts zurück (für das Live-Dashboard)."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        with Session(self.engine) as session:
            if user_id is not None:
                loc_statement = select(Location).where(Location.user_id == user_id)
                location_ids = [loc.id for loc in session.exec(loc_statement).all()]
                if not location_ids:
                    return []
                statement = (
                    select(Alert)
                    .where(Alert.location_id.in_(location_ids))
                    .where(Alert.created_at >= today_start)
                    .order_by(Alert.created_at.desc())
                )
            else:
                statement = (
                    select(Alert)
                    .where(Alert.created_at >= today_start)
                    .order_by(Alert.created_at.desc())
                )
            alerts = list(session.exec(statement).all())
            for alert in alerts:
                _ = alert.location
            return alerts

    def list_all(self, limit=200, user_id=None):
        """Gibt die neuesten Alerts eines Users zurück (max. 'limit' Stück)."""
        with Session(self.engine) as session:
            # Filtern auf Standorte des Users, falls user_id angegeben
            if user_id is not None:
                # Erst die Standort-IDs dieses Users holen
                loc_statement = select(Location).where(Location.user_id == user_id)
                user_locations = session.exec(loc_statement).all()
                location_ids = [loc.id for loc in user_locations]
                if not location_ids:
                    return []
                statement = (
                    select(Alert)
                    .where(Alert.location_id.in_(location_ids))
                    .order_by(Alert.created_at.desc())
                    .limit(limit)
                )
            else:
                statement = select(Alert).order_by(Alert.created_at.desc()).limit(limit)

            alerts = list(session.exec(statement).all())
            # location nachladen, solange Session offen ist
            for alert in alerts:
                _ = alert.location
            return alerts

    def replace_for_location(self, location_id, since, new_alerts):
        """Löscht Alerts eines Standorts ab 'since' und fügt die neuen ein."""
        with Session(self.engine) as session:
            statement = (
                select(Alert)
                .where(Alert.location_id == location_id)
                .where(Alert.created_at >= since)
            )
            for old in session.exec(statement).all():
                session.delete(old)
            for new_alert in new_alerts:
                session.add(new_alert)
            session.commit()

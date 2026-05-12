"""DAO-Klassen (Data Access Object).

Eine DAO-Klasse fasst alle Datenbank-Operationen für EINE Tabelle zusammen:
- UserDAO     → arbeitet mit der users-Tabelle
- LocationDAO → arbeitet mit der locations-Tabelle
- AlertDAO    → arbeitet mit der alerts-Tabelle

So muss der Rest der App nie SQL schreiben - er ruft einfach
z.B. user_dao.get_by_username("admin") oder location_dao.add(loc) auf.
"""

from sqlmodel import Session, select

from domain.models import User, Location, Alert


class UserDAO:
    """Alle Datenbank-Operationen rund um User."""

    def __init__(self, engine):
        self.engine = engine

    def get_by_username(self, username):
        """Sucht einen User per Benutzername. Gibt None zurück, wenn nicht gefunden."""
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
        """Ändert das Passwort eines Users. True bei Erfolg, sonst False."""
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if user is None:
                return False
            user.password = new_password
            session.add(user)
            session.commit()
            return True


class LocationDAO:
    """Alle Datenbank-Operationen rund um Locations."""

    def __init__(self, engine):
        self.engine = engine

    def list_all(self, user_id=None):
        """Gibt alle Locations zurück.

        Wenn user_id gesetzt ist, werden nur die Locations dieses Users zurückgegeben.
        """
        with Session(self.engine) as session:
            statement = select(Location)
            if user_id is not None:
                statement = statement.where(Location.user_id == user_id)
            locations = list(session.exec(statement).all())

            # Wichtig: Grenzwerte mitladen, solange die Session noch offen ist.
            # Sonst sind sie nach session.close() nicht mehr zugreifbar.
            for loc in locations:
                _ = loc.thresholds
            return locations

    def get_by_id(self, location_id):
        """Lädt eine einzelne Location anhand ihrer ID."""
        with Session(self.engine) as session:
            loc = session.get(Location, location_id)
            if loc is not None:
                _ = loc.thresholds   # Grenzwerte mitladen
            return loc

    def add(self, location):
        """Speichert eine neue Location (samt Grenzwerten) in der Datenbank."""
        with Session(self.engine) as session:
            session.add(location)
            session.commit()
            session.refresh(location)
            return location

    def delete(self, location_id):
        """Löscht eine Location.

        Wegen cascade="all, delete-orphan" werden auch die zugehörigen
        Grenzwerte und Alerts automatisch mitgelöscht.
        """
        with Session(self.engine) as session:
            loc = session.get(Location, location_id)
            if loc is not None:
                session.delete(loc)
                session.commit()


class AlertDAO:
    """Alle Datenbank-Operationen rund um Alerts (Wetter-Warnungen)."""

    def __init__(self, engine):
        self.engine = engine

    def list_all(self, limit=200, user_id=None):
        """Gibt die neuesten Alerts zurück (höchstens 'limit' Stück).

        Wenn user_id gesetzt ist, werden nur Alerts der Locations dieses Users zurückgegeben.
        """
        with Session(self.engine) as session:
            if user_id is not None:
                # 1. IDs aller Locations des Users sammeln
                user_locs = session.exec(
                    select(Location).where(Location.user_id == user_id)
                ).all()
                location_ids = [loc.id for loc in user_locs]
                if not location_ids:
                    return []
                # 2. Nur Alerts dieser Locations holen
                statement = (
                    select(Alert)
                    .where(Alert.location_id.in_(location_ids))
                    .order_by(Alert.created_at.desc())
                    .limit(limit)
                )
            else:
                # Kein User-Filter: einfach die neuesten Alerts holen
                statement = (
                    select(Alert)
                    .order_by(Alert.created_at.desc())
                    .limit(limit)
                )

            alerts = list(session.exec(statement).all())

            # Wichtig: Location-Daten mitladen (für Anzeige des Standort-Namens)
            for a in alerts:
                _ = a.location
            return alerts

    def replace_for_location(self, location_id, new_alerts):
        """Löscht alle alten Alerts einer Location und speichert die neuen.

        Wird nach jeder Wetter-Analyse aufgerufen, damit immer nur die
        aktuellen Warnungen in der Datenbank stehen.
        """
        with Session(self.engine) as session:
            # 1. Alte Alerts dieser Location löschen
            old_alerts = session.exec(
                select(Alert).where(Alert.location_id == location_id)
            ).all()
            for old in old_alerts:
                session.delete(old)
            # 2. Neue Alerts speichern
            for new in new_alerts:
                session.add(new)
            session.commit()

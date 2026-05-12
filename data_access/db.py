"""Datenbank-Verbindung.

Die Klasse Database kümmert sich um drei Dinge:
1. Verbindung zur SQLite-Datei (engine)
2. Tabellen anlegen (create_tables)
3. Neue Datenbank-Session öffnen (new_session)
"""

from sqlmodel import SQLModel, Session, create_engine


class Database:
    """Wrappt die SQLite-Datenbank in eine einfache Klasse."""

    def __init__(self, database_url="sqlite:///weatherguard.db"):
        # check_same_thread=False brauchen wir, weil NiceGUI mehrere Threads nutzt.
        # Sonst gäbe es Fehler beim parallelen Zugriff auf die Datenbank.
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    def create_tables(self):
        """Erstellt alle Tabellen in der Datenbank (falls sie noch nicht existieren)."""
        # Modelle importieren, damit SQLModel sie kennt, bevor wir create_all() aufrufen
        from domain.models import User, Location, WeatherThreshold, Alert  # noqa: F401
        SQLModel.metadata.create_all(self.engine)

    def new_session(self):
        """Öffnet eine neue Datenbank-Session.

        Der Aufrufer muss die Session danach selbst mit session.close() schliessen,
        oder ein with-Block verwenden:
            with Session(db.engine) as session:
                ...
        """
        return Session(self.engine)

"""Datenbank-Verbindung.

Diese Klasse kümmert sich um die Verbindung zur SQLite-Datenbank
und erstellt die Tabellen, falls sie noch nicht existieren.
"""

from sqlmodel import SQLModel, Session, create_engine


class Database:
    """Verwaltet die Verbindung zur SQLite-Datenbank."""

    def __init__(self, database_url="sqlite:///weatherguard.db"):
        # check_same_thread=False ist nötig, weil NiceGUI mehrere Threads nutzt
        self.engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    def init_schema(self):
        """Erstellt alle Tabellen (macht nichts, falls sie schon existieren)."""
        # Wir importieren die Modelle hier, damit SQLModel sie kennt,
        # bevor wir create_all() aufrufen.
        from domain.models import User, Location, WeatherThreshold, Alert
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        """Gibt eine neue Datenbank-Session zurück.

        Wir nutzen die Session immer mit 'with', damit sie sich
        automatisch wieder schliesst:

            with database.get_session() as session:
                session.add(...)
                session.commit()
        """
        return Session(self.engine)

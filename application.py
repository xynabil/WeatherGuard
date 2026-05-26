"""WeatherGuardApplication - die Haupt-Klasse, die alles zusammensteckt.

Sie tut der Reihe nach:
1. Datenbank-Verbindung aufbauen und Tabellen erstellen
2. Demo-Daten einfügen (nur beim ersten Start)
3. DAOs erstellen (für DB-Zugriff)
4. Services erstellen (Wetter-API)
5. Controllers erstellen (Logik zwischen UI und DB)
6. Pages erstellen (die eigentliche Web-UI)
7. Den Web-Server starten
"""

from nicegui import ui
from sqlmodel import select

from config import DATABASE_URL, STORAGE_SECRET
from data_access.db import Database
from data_access.dao import UserDAO, LocationDAO, AlertDAO
from data_access.seed import WeatherSeeder
from services.weather_client import WeatherClient
from controllers import (
    AuthController,
    LocationController,
    AlertController,
    HistoryController,
)
from ui.pages import Pages
from domain.models import User


class WeatherGuardApplication:
    """Die Haupt-App: erstellt alle Komponenten und startet den Server."""

    def __init__(self, database_url=DATABASE_URL):
        # 1. Datenbank
        self.database = Database(database_url)
        self.database.init_schema()

        # 2. Demo-Daten einfügen, wenn DB leer ist
        self._seed_if_empty()

        # 3. DAOs (für Datenbank-Zugriff)
        user_dao = UserDAO(self.database.engine)
        location_dao = LocationDAO(self.database.engine)
        alert_dao = AlertDAO(self.database.engine)

        # 4. Services (für externe Daten)
        weather_client = WeatherClient()

        # 5. Controllers (Logik zwischen UI und DB)
        auth_controller = AuthController(user_dao)
        location_controller = LocationController(location_dao)
        alert_controller = AlertController(location_dao, alert_dao, weather_client)
        history_controller = HistoryController(alert_dao)

        # 6. Pages (die Web-UI selbst)
        self.pages = Pages(
            auth_controller=auth_controller,
            location_controller=location_controller,
            alert_controller=alert_controller,
            history_controller=history_controller,
        )

    def _seed_if_empty(self):
        """Fügt Demo-Daten ein, wenn noch keine User in der DB sind."""
        with self.database.get_session() as session:
            existing_user = session.exec(select(User)).first()
            if existing_user is None:
                seeder = WeatherSeeder()
                seeder.seed(session)

    def run(self, host="0.0.0.0", port=8080, reload=False):
        """Registriert die Routen und startet den NiceGUI-Server."""
        self.pages.register()
        ui.run(
            title="WeatherGuard",
            host=host,
            port=port,
            reload=reload,
            dark=True,
            storage_secret=STORAGE_SECRET,
        )

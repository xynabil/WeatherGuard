"""WeatherGuardApplication - die zentrale Klasse, die alles zusammenbaut.

Die Klasse erzeugt alle Objekte in der richtigen Reihenfolge
(Datenbank → DAOs → Services → Controller → Pages) und startet danach
den NiceGUI-Webserver. Aufbau wie im Pizza-Referenzprojekt.
"""

from nicegui import ui
from sqlmodel import Session, select

from config import DATABASE_URL
from data_access.db import Database
from data_access.dao import UserDAO, LocationDAO, AlertDAO
from data_access.seed import WeatherSeeder
from domain.models import User
from services.weather_client import WeatherClient
from ui.controllers import (
    AuthController,
    LocationController,
    AlertController,
    HistoryController,
)
from ui.pages import Pages


class WeatherGuardApplication:
    """Verbindet alle Bausteine und startet die App."""

    def __init__(self):
        # 1. Datenbank vorbereiten (Tabellen anlegen, falls noch nicht da)
        self.db = Database(DATABASE_URL)
        self.db.create_tables()

        # 2. Demo-Daten einfügen, wenn die Datenbank leer ist
        session = Session(self.db.engine)
        first_user = session.exec(select(User)).first()
        if first_user is None:
            seeder = WeatherSeeder()
            seeder.seed(session)
        session.close()

        # 3. DAOs (Data Access Objects - kümmern sich um die Datenbank)
        self.user_dao = UserDAO(self.db.engine)
        self.location_dao = LocationDAO(self.db.engine)
        self.alert_dao = AlertDAO(self.db.engine)

        # 4. Services
        self.weather_client = WeatherClient()

        # 5. Controller (verbinden UI mit DAOs/Services)
        self.auth_controller = AuthController(self.user_dao)
        self.location_controller = LocationController(self.location_dao)
        self.alert_controller = AlertController(
            self.location_dao, self.alert_dao, self.weather_client,
        )
        self.history_controller = HistoryController(self.alert_dao)

        # 6. Pages (alle Seiten der Web-App)
        self.pages = Pages(
            auth_controller=self.auth_controller,
            location_controller=self.location_controller,
            alert_controller=self.alert_controller,
            history_controller=self.history_controller,
        )

    def run(self):
        """Registriert alle Routen und startet den NiceGUI-Server."""
        self.pages.register()
        ui.run(
            title="WeatherGuard",
            host="0.0.0.0",
            port=8080,
            dark=True,
            storage_secret="weatherguard-secret",
            reload=False,
        )

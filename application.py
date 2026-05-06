"""Application composition root.

WeatherGuardApplication wires all dependencies together and starts the server.
Design pattern: same as PizzaApplication in the pizza reference project.
"""

from __future__ import annotations

from nicegui import ui

from data_access.db import Database
from data_access.dao import UserDAO, LocationDAO, AlertDAO
from data_access.seed import WeatherSeeder
from services.weather_client import WeatherClient
from ui.controllers import AuthController, LocationController, AlertController, HistoryController
from ui.pages import Pages


class WeatherGuardApplication:
    """Composition root — creates and connects all objects, then runs the app."""

    def __init__(self, database_url: str = None) -> None:
        # 1. Database
        self.db = Database(database_url)
        self.db.init_schema()

        # Seed demo data on first run (only if tables are empty)
        with self.db.session_scope() as session:
            from sqlmodel import select
            from domain.models import User
            if not session.exec(select(User)).first():
                WeatherSeeder().seed(session)

        # 2. DAOs
        user_dao     = UserDAO(self.db.engine)
        location_dao = LocationDAO(self.db.engine)
        alert_dao    = AlertDAO(self.db.engine)

        # 3. Services
        weather_client = WeatherClient()

        # 4. Controllers
        auth_controller     = AuthController(user_dao)
        location_controller = LocationController(location_dao)
        alert_controller    = AlertController(location_dao, alert_dao, weather_client)
        history_controller  = HistoryController(alert_dao)

        # 5. Pages
        self.pages = Pages(
            auth_controller=auth_controller,
            location_controller=location_controller,
            alert_controller=alert_controller,
            history_controller=history_controller,
        )

    def run(self, host: str = "0.0.0.0", port: int = 8080, reload: bool = False) -> None:
        """Register all routes and start the NiceGUI server."""
        self.pages.register()
        ui.run(
            title="WeatherGuard",
            host=host,
            port=port,
            reload=reload,
            dark=True,
            storage_secret="weatherguard-secret",
        )

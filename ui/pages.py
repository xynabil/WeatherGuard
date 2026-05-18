"""NiceGUI Seiten (Pages).

Diese Datei registriert nur die fünf URL-Routen.
Der eigentliche Render-Code liegt in den page_*.py-Dateien:

- page_login.py     → /          Login & Registrierung
- page_history.py   → /app       Alert History
- page_dashboard.py → /dashboard Dashboard
- page_reports.py   → /reports   Reports + Export
- page_settings.py  → /settings  Einstellungen

Gemeinsame Konstanten und Hilfsfunktionen (Sidebar, Farben …)
sind in components.py ausgelagert.
"""

from nicegui import ui

from ui.page_login     import _render_login_page
from ui.page_history   import _render_alert_history_page
from ui.page_dashboard import _render_dashboard_page
from ui.page_reports   import _render_reports_page
from ui.page_settings  import _render_settings_page


class Pages:
    """Registriert alle Seiten/Routen der Web-App."""

    def __init__(self, auth_controller, location_controller, alert_controller, history_controller):
        self.auth     = auth_controller
        self.location = location_controller
        self.alert    = alert_controller
        self.history  = history_controller

    def register(self):
        """Sagt NiceGUI, welche URL welche Funktion aufruft."""
        auth     = self.auth
        location = self.location
        alert    = self.alert
        history  = self.history

        @ui.page("/")
        def login_route():
            _render_login_page(auth)

        @ui.page("/app")
        def alert_history_route():
            _render_alert_history_page(history)

        @ui.page("/dashboard")
        def dashboard_route():
            _render_dashboard_page(location, alert)

        @ui.page("/reports")
        def reports_route():
            _render_reports_page(alert)

        @ui.page("/settings")
        def settings_route():
            _render_settings_page(auth)

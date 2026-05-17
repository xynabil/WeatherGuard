"""Auto-Refresh für das Dashboard.

Diese Klasse kümmert sich um zwei Timer:
1. Jede Sekunde: aktualisiert den Countdown-Text neben der Überschrift
2. Alle 3 Minuten: lässt die Wetter-Analyse automatisch laufen
"""

from datetime import datetime

from nicegui import ui

REFRESH_INTERVAL = 180  # 3 Minuten in Sekunden


class DashboardRefresh:
    """Verwaltet den Auto-Refresh des Dashboards."""

    def __init__(self, refresh_label, alert_controller, location_controller, refresh_callbacks, user_id):
        self.refresh_label = refresh_label
        self.alert_controller = alert_controller
        self.location_controller = location_controller
        self.refresh_callbacks = refresh_callbacks
        self.user_id = user_id
        self.last_refresh = datetime.now()

    def start(self):
        """Startet die beiden Timer."""
        ui.timer(1.0, self._update_countdown_label)
        ui.timer(REFRESH_INTERVAL, self._do_auto_refresh)

    def _update_countdown_label(self):
        """Aktualisiert den Text neben der Dashboard-Überschrift."""
        elapsed = int((datetime.now() - self.last_refresh).total_seconds())
        next_in = REFRESH_INTERVAL - elapsed

        if elapsed < 60:
            elapsed_text = "gerade eben"
        else:
            elapsed_text = f"vor {elapsed // 60} Min."

        if next_in < 60:
            next_text = f"in {next_in} Sek."
        else:
            next_text = f"in {next_in // 60} Min."

        self.refresh_label.set_text(
            f"(letzte Aktualisierung {elapsed_text} / nächste Aktualisierung {next_text})"
        )

    async def _do_auto_refresh(self):
        """Wird alle 3 Minuten aufgerufen: macht Wetter-Analyse für alle Standorte."""
        locations = self.location_controller.list_locations(user_id=self.user_id)

        for location in locations:
            try:
                self.alert_controller.run_analysis(location.id)
            except Exception as error:
                ui.notify(f"Fehler bei {location.name}: {error}", type="negative")

        self.last_refresh = datetime.now()
        self.refresh_callbacks["refresh_alerts"]()
        ui.notify("Dashboard automatisch aktualisiert", type="info", timeout=3000)

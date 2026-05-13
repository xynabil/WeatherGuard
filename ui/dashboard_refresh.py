"""Dashboard Auto-Refresh.

Stellt zwei NiceGUI-Timer bereit:
- Einen Sekunden-Ticker, der das Refresh-Info-Label neben dem H1 aktualisiert.
- Einen 3-Minuten-Timer, der alle Standorte des Nutzers neu analysiert.

Verwendung:
    from ui.dashboard_refresh import setup_refresh

    refresh_info = ui.label("").style(...)
    setup_refresh(refresh_info, alert_controller, location_controller,
                  callbacks, user_id)
"""

from __future__ import annotations

"""Auto-Refresh für das Dashboard.

Diese Klasse kümmert sich um zwei Timer:
1. Jede Sekunde: aktualisiert den Countdown-Text neben der Überschrift
2. Alle 3 Minuten: lässt die Wetter-Analyse automatisch laufen
"""

from datetime import datetime

from nicegui import ui

REFRESH_INTERVAL = 180  # Sekunden (3 Minuten)


def setup_refresh(
    refresh_info,
    alert,
    location,
    callbacks: dict,
    user_id: int | None = None,
) -> None:
    """Registriert den Countdown-Ticker und den 3-Minuten-Auto-Refresh.

    Args:
        refresh_info: NiceGUI-Label-Element neben dem Dashboard-H1.
        alert:        AlertController – wird für run_analysis() genutzt.
        location:     LocationController – liefert die Standortliste.
        callbacks:    Dict mit "refresh_alerts"-Eintrag zum Neuzeichnen.
        user_id:      ID des eingeloggten Nutzers (None = alle Standorte).
    """
    last_refresh: dict = {"ts": datetime.now()}

    # -- Sekunden-Ticker: Refresh-Label jede Sekunde aktualisieren --------
    def _update_label() -> None:
        elapsed = int((datetime.now() - last_refresh["ts"]).total_seconds())
        next_in = REFRESH_INTERVAL - elapsed

        elapsed_str = (
            "gerade eben" if elapsed < 60
            else f"vor {elapsed // 60} Min."
        )
        next_str = (
            f"in {next_in} Sek." if next_in < 60
            else f"in {next_in // 60} Min."
        )
        refresh_info.set_text(
            f"(letzte Aktualisierung {elapsed_str} / nächste Aktualisierung {next_str})"
        )

    ui.timer(1.0, _update_label)

    # -- 3-Minuten-Timer: alle Standorte neu analysieren ------------------
    async def _auto_refresh() -> None:
        locs = location.list_locations(user_id=user_id)
        for loc in locs:
            try:
                alert.run_analysis(loc.id)
            except Exception as exc:
                ui.notify(f"Fehler bei {loc.name}: {exc}", type="negative")
REFRESH_INTERVAL = 180  # 3 Minuten in Sekunden

# Intervall in Sekunden (3 Minuten = 180 Sekunden)
REFRESH_INTERVAL_SECONDS = 180


class DashboardRefresh:
    """Verwaltet den Auto-Refresh des Dashboards."""

    def __init__(self, refresh_label, alert_controller, location_controller, refresh_callbacks, user_id):
        self.refresh_label = refresh_label                # UI-Label für den Countdown
        self.alert_controller = alert_controller
        self.location_controller = location_controller
        self.refresh_callbacks = refresh_callbacks        # Dict mit "refresh_alerts": func
        self.user_id = user_id
        self.last_refresh = datetime.now()

    def start(self):
        """Startet die beiden Timer."""
        # Countdown-Text jede Sekunde aktualisieren
        ui.timer(1.0, self._update_countdown_label)
        # Auto-Analyse alle 3 Minuten
        ui.timer(REFRESH_INTERVAL_SECONDS, self._do_auto_refresh)

    def _update_countdown_label(self):
        """Aktualisiert den Text neben der Dashboard-Überschrift."""
        elapsed = int((datetime.now() - self.last_refresh).total_seconds())
        next_in = REFRESH_INTERVAL_SECONDS - elapsed

        # "vor X Min" oder "gerade eben"
        if elapsed < 60:
            elapsed_text = "gerade eben"
        else:
            elapsed_text = f"vor {elapsed // 60} Min."

        # "in X Sek" oder "in X Min"
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

        # Zeitpunkt merken und UI aktualisieren
        self.last_refresh = datetime.now()
        self.refresh_callbacks["refresh_alerts"]()
        ui.notify("Dashboard automatisch aktualisiert", type="info", timeout=3000)

    ui.timer(REFRESH_INTERVAL, _auto_refresh)
    ui.timer(1.0, update_label)
    ui.timer(REFRESH_INTERVAL, auto_refresh)

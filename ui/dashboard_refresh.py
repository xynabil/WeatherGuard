"""Auto-Refresh für das Dashboard.

Registriert zwei Timer:
- Alle 1 Sekunde: aktualisiert den Countdown-Text neben dem H1.
- Alle 3 Minuten: analysiert alle Standorte neu und lädt die Alerts neu.
"""

from datetime import datetime

from nicegui import ui


# Wie oft soll automatisch aktualisiert werden? (in Sekunden)
REFRESH_INTERVAL = 180   # = 3 Minuten


def setup_refresh(refresh_label, alert, location, callbacks, user_id):
    """Startet den Countdown-Ticker und den 3-Minuten-Auto-Refresh.

    Parameter:
        refresh_label: das ui.label, in dem der Countdown-Text steht
        alert:         der AlertController
        location:      der LocationController
        callbacks:     Dict mit refresh-Funktionen aus dem Dashboard
        user_id:       der eingeloggte User (damit nur seine Locations geprueft werden)
    """
    # Wir merken uns den Zeitpunkt der letzten Aktualisierung in einem Dict.
    # (Ein Dict, weil wir den Wert von innen drin ändern wollen.)
    last_refresh = {"timestamp": datetime.now()}

    def update_label():
        """Läuft jede Sekunde - aktualisiert den "vor X Min / in Y Min"-Text."""
        elapsed_seconds = int((datetime.now() - last_refresh["timestamp"]).total_seconds())
        next_in_seconds = REFRESH_INTERVAL - elapsed_seconds

        if elapsed_seconds < 60:
            elapsed_text = "gerade eben"
        else:
            elapsed_text = f"vor {elapsed_seconds // 60} Min."

        if next_in_seconds < 60:
            next_text = f"in {next_in_seconds} Sek."
        else:
            next_text = f"in {next_in_seconds // 60} Min."

        refresh_label.set_text(
            f"(letzte Aktualisierung {elapsed_text} / nächste Aktualisierung {next_text})"
        )

    async def auto_refresh():
        """Läuft alle 3 Minuten - analysiert alle Locations neu."""
        for loc in location.list_locations(user_id=user_id):
            try:
                alert.run_analysis(loc.id)
            except Exception as exc:
                ui.notify(f"Fehler bei {loc.name}: {exc}", type="negative")

        # Zeitpunkt der letzten Aktualisierung merken
        last_refresh["timestamp"] = datetime.now()
        # UI aktualisieren
        callbacks["refresh_alerts"]()
        ui.notify("Dashboard automatisch aktualisiert", type="info", timeout=3000)

    # Beide Timer registrieren
    ui.timer(1.0, update_label)
    ui.timer(REFRESH_INTERVAL, auto_refresh)

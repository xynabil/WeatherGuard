"""Auto-Refresh für das Dashboard.

Registriert zwei Timer:
- Alle 1 Sekunde: Aktualisiert den Countdown-Text neben dem H1.
- Alle 3 Minuten: Analysiert alle Standorte und lädt die Alerts neu.
"""

from datetime import datetime

from nicegui import ui

REFRESH_INTERVAL = 180  # 3 Minuten in Sekunden


def setup_refresh(refresh_label, alert, location, callbacks, user_id):
    """Startet den Countdown-Ticker und den 3-Minuten-Auto-Refresh."""

    last_refresh = {"ts": datetime.now()}

    def update_label():
        elapsed = int((datetime.now() - last_refresh["ts"]).total_seconds())
        next_in = REFRESH_INTERVAL - elapsed

        elapsed_text = "gerade eben" if elapsed < 60 else f"vor {elapsed // 60} Min."
        next_text    = f"in {next_in} Sek." if next_in < 60 else f"in {next_in // 60} Min."

        refresh_label.set_text(
            f"(letzte Aktualisierung {elapsed_text} / nächste Aktualisierung {next_text})"
        )

    async def auto_refresh():
        for loc in location.list_locations(user_id=user_id):
            try:
                alert.run_analysis(loc.id)
            except Exception as e:
                ui.notify(f"Fehler bei {loc.name}: {e}", type="negative")

        last_refresh["ts"] = datetime.now()
        callbacks["refresh_alerts"]()
        ui.notify("Dashboard automatisch aktualisiert", type="info", timeout=3000)

    ui.timer(1.0, update_label)
    ui.timer(REFRESH_INTERVAL, auto_refresh)

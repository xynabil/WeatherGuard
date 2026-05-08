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

        last_refresh["ts"] = datetime.now()
        callbacks["refresh_alerts"]()
        ui.notify("Dashboard automatisch aktualisiert", type="info", timeout=3000)

    ui.timer(REFRESH_INTERVAL, _auto_refresh)

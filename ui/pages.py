"""NiceGUI pages.

All routes are registered by the Pages class, which holds the controllers it needs.
Design pattern: same as the Pizza reference project (Pages class registers routes).
"""

from __future__ import annotations

import asyncio
import requests as http_requests

from nicegui import ui, app

from domain.models import Location, WeatherThreshold, Alert
from ui.controllers import (
    AuthController,
    LocationController,
    AlertController,
    HistoryController,
    BRANCH_PRESETS,
    PARAM_TO_TYPE,
    TYPE_COLORS,
)
from services.risk_analyzer import RiskAnalyzer

# ---------------------------------------------------------------------------
# Theme constants (shared across all pages)
# ---------------------------------------------------------------------------

BG_MAIN      = "#1a1a1a"
BG_SIDEBAR   = "#1f1f1f"
BG_CARD      = "#262626"
BG_CARD_SOFT = "#2d2d2d"
BG_INPUT     = "#1f1f1f"
TEXT_PRIMARY = "#e8e8e8"
TEXT_MUTED   = "#888"
ACCENT_BLUE  = "#4a9eff"
BORDER       = "#333"

SEVERITY_COLORS = {"critical": "#f47174", "warning": "#d4a24a", "info": "#4a9eff"}
SEVERITY_BG     = {"critical": "#2d1515", "warning": "#2d2215", "info": "#15202d"}
SEVERITY_STYLES = {
    "critical": {"color": "#f47174", "bg": "#3b1f22", "label": "danger"},
    "warning":  {"color": "#d4a24a", "bg": "#3a2e1a", "label": "warning"},
    "info":     {"color": "#4a9eff", "bg": "#1e2a3a", "label": "info"},
}
DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


# ---------------------------------------------------------------------------

class Pages:
    """Registers all NiceGUI routes."""

    def __init__(
        self,
        auth_controller: AuthController,
        location_controller: LocationController,
        alert_controller: AlertController,
        history_controller: HistoryController,
    ) -> None:
        self._auth     = auth_controller
        self._location = location_controller
        self._alert    = alert_controller
        self._history  = history_controller

    def register(self) -> None:
        auth     = self._auth
        location = self._location
        alert    = self._alert
        history  = self._history

        def is_logged_in() -> bool:
            return app.storage.user.get("logged_in", False)

        # ----------------------------------------------------------------
        # Login page  /
        # ----------------------------------------------------------------
        @ui.page("/")
        def login_page() -> None:
            if is_logged_in():
                ui.navigate.to("/app")
                return

            _setup_dark()

            with ui.column().classes("absolute-center items-center").style("gap: 0;"):
                # Logo
                with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
                    ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: 700;")
                    ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 28px; font-weight: 700;")

                with ui.column().style(
                    f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                    f"border-radius: 12px; padding: 32px 36px; gap: 16px; width: 340px;"
                ):
                    # Tab switcher
                    mode = {"active": "login"}  # "login" or "register"
                    content_area = ui.column().classes("w-full").style("gap: 16px;")

                    tab_row = ui.row().classes("w-full no-wrap").style(
                        f"border-bottom: 1px solid {BORDER}; margin-bottom: 4px; gap: 0;"
                    )

                    def build_tab(label: str, key: str, tab_row_ref, content_area_ref):
                        """Helper so we can rebuild both tabs cleanly."""
                        is_active = mode["active"] == key
                        style = (
                            f"color: {ACCENT_BLUE}; font-size: 15px; font-weight: 600; "
                            f"padding: 8px 0; flex: 1; text-align: center; cursor: pointer; "
                            f"border-bottom: 2px solid {ACCENT_BLUE};"
                        ) if is_active else (
                            f"color: {TEXT_MUTED}; font-size: 15px; "
                            f"padding: 8px 0; flex: 1; text-align: center; cursor: pointer; "
                            f"border-bottom: 2px solid transparent;"
                        )

                        def switch(k=key):
                            mode["active"] = k
                            tab_row_ref.clear()
                            build_tab("Anmelden",    "login",    tab_row_ref, content_area_ref)
                            build_tab("Registrieren","register", tab_row_ref, content_area_ref)
                            content_area_ref.clear()
                            if k == "login":
                                build_login_form(content_area_ref)
                            else:
                                build_register_form(content_area_ref)

                        with tab_row_ref:
                            ui.label(label).style(style).on("click", switch)

                    def build_login_form(container):
                        with container:
                            username_input = ui.input("Benutzername").classes("w-full")
                            password_input = ui.input(
                                "Passwort", password=True, password_toggle_button=True
                            ).classes("w-full")
                            error_label = ui.label("").style(
                                "color: #f47174; font-size: 13px; min-height: 20px;"
                            )

                            def try_login():
                                user = auth.verify_login(username_input.value, password_input.value)
                                if user:
                                    app.storage.user["logged_in"] = True
                                    app.storage.user["user_id"]   = user.id
                                    app.storage.user["username"]  = user.username
                                    app.storage.user["company"]   = user.company
                                    ui.navigate.to("/app")
                                else:
                                    error_label.set_text("Benutzername oder Passwort falsch.")

                            ui.button("Login", on_click=try_login, icon="login").classes("w-full").style(
                                f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
                            )
                            ui.label("Demo-Zugang: admin / admin123").style(
                                f"color: {TEXT_MUTED}; font-size: 12px; text-align: center; margin-top: 4px;"
                            )

                    def build_register_form(container):
                        with container:
                            reg_username = ui.input("Benutzername *").classes("w-full")
                            reg_company  = ui.input("Firma", placeholder="Optional").classes("w-full")
                            reg_pw       = ui.input(
                                "Passwort *", password=True, password_toggle_button=True
                            ).classes("w-full")
                            reg_pw2      = ui.input(
                                "Passwort bestätigen *", password=True, password_toggle_button=True
                            ).classes("w-full")
                            error_label  = ui.label("").style(
                                "color: #f47174; font-size: 13px; min-height: 20px;"
                            )

                            def try_register():
                                error_label.set_text("")
                                try:
                                    ok, msg = auth.register(
                                        reg_username.value, reg_pw.value,
                                        reg_pw2.value, reg_company.value,
                                    )
                                    if not ok:
                                        error_label.set_text(msg)
                                        return
                                    ui.notify("Konto erstellt! Bitte einloggen.", type="positive")
                                    ui.navigate.to("/")
                                except Exception as exc:
                                    error_label.set_text(f"Fehler: {exc}")

                            ui.button("Konto erstellen", on_click=try_register, icon="person_add").classes("w-full").style(
                                f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
                            )

                    # Initial render
                    build_tab("Anmelden",    "login",    tab_row, content_area)
                    build_tab("Registrieren","register", tab_row, content_area)
                    build_login_form(content_area)

        # ----------------------------------------------------------------
        # Alert History  /app
        # ----------------------------------------------------------------
        @ui.page("/app")
        def alert_history_page() -> None:
            if not is_logged_in():
                ui.navigate.to("/")
                return

            _setup_dark()

            with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
                _sidebar("Alert History")
                with ui.column().classes("grow").style(
                    f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
                    f"padding: 24px 32px; gap: 20px;"
                ):
                    _header_user_chip()

                    with ui.column().style("gap: 4px;"):
                        ui.label("Alert History").style(
                            f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                        )
                        ui.label("Alle Standorte · letzte 7 Tage").style(
                            f"color: {TEXT_MUTED}; font-size: 14px;"
                        )

                    user_id = app.storage.user.get("user_id")
                    kpis = history.get_kpis(user_id=user_id)
                    _kpi_row(kpis)
                    _charts_row(history.get_alerts_per_day(user_id=user_id), history.get_alerts_by_type(user_id=user_id))
                    _recent_alerts_section(history, user_id=user_id)

        # ----------------------------------------------------------------
        # Dashboard  /dashboard
        # ----------------------------------------------------------------
        @ui.page("/dashboard")
        def dashboard_page() -> None:
            if not is_logged_in():
                ui.navigate.to("/")
                return

            _setup_dark()

            user_id = app.storage.user.get("user_id")
            with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
                _sidebar("Dashboard")
                _dashboard_main(location, alert, user_id)

        # ----------------------------------------------------------------
        # Reports  /reports
        # ----------------------------------------------------------------
        @ui.page("/reports")
        def reports_page() -> None:
            if not is_logged_in():
                ui.navigate.to("/")
                return

            _setup_dark()
            user_id = app.storage.user.get("user_id")
            alerts_all = alert.list_alerts(user_id=user_id)

            with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
                _sidebar("Reports")
                with ui.column().classes("grow").style(
                    f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
                    f"padding: 24px 32px; gap: 20px;"
                ):
                    with ui.column().style("gap: 4px;"):
                        ui.label("Reports").style(
                            f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                        )
                        ui.label(f"{len(alerts_all)} Alerts insgesamt").style(
                            f"color: {TEXT_MUTED}; font-size: 14px;"
                        )

                    with ui.column().classes("w-full").style(
                        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                        f"border-radius: 10px; overflow: hidden;"
                    ):
                        _reports_table_header()
                        if not alerts_all:
                            ui.label("Keine Alerts vorhanden.").style(
                                f"color: {TEXT_MUTED}; font-style: italic; padding: 20px 16px;"
                            )
                        for i, a in enumerate(alerts_all):
                            _reports_table_row(a, alternate=(i % 2 == 1))

        # ----------------------------------------------------------------
        # Settings  /settings
        # ----------------------------------------------------------------
        @ui.page("/settings")
        def settings_page() -> None:
            if not is_logged_in():
                ui.navigate.to("/")
                return

            _setup_dark()
            username = app.storage.user.get("username", "")
            company  = app.storage.user.get("company", "")

            with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
                _sidebar("Settings")
                with ui.column().classes("grow").style(
                    f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
                    f"padding: 24px 32px; gap: 24px;"
                ):
                    ui.label("Settings").style(
                        f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                    )

                    # Account info card
                    with ui.column().style(
                        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                        f"border-radius: 10px; padding: 24px; gap: 12px; max-width: 480px;"
                    ):
                        ui.label("Benutzerkonto").style(
                            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;"
                        )
                        ui.label(f"Benutzername: {username}").style(
                            f"color: {TEXT_MUTED}; font-size: 14px;"
                        )
                        ui.label(f"Firma: {company or '—'}").style(
                            f"color: {TEXT_MUTED}; font-size: 14px;"
                        )

                    # Change password card
                    with ui.column().style(
                        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                        f"border-radius: 10px; padding: 24px; gap: 16px; max-width: 480px;"
                    ):
                        ui.label("Passwort ändern").style(
                            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;"
                        )
                        current_pw  = ui.input("Aktuelles Passwort",  password=True, password_toggle_button=True).classes("w-full")
                        new_pw      = ui.input("Neues Passwort",       password=True, password_toggle_button=True).classes("w-full")
                        confirm_pw  = ui.input("Passwort bestätigen",  password=True, password_toggle_button=True).classes("w-full")
                        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

                        def save_password():
                            error_label.set_text("")
                            if new_pw.value != confirm_pw.value:
                                error_label.set_text("Neue Passwörter stimmen nicht überein.")
                                return
                            ok, msg = auth.change_password(username, current_pw.value, new_pw.value)
                            if not ok:
                                error_label.set_text(msg)
                                return
                            current_pw.value = new_pw.value = confirm_pw.value = ""
                            ui.notify("Passwort erfolgreich geändert!", type="positive")

                        ui.button("Speichern", on_click=save_password, icon="save").style(
                            f"background: {ACCENT_BLUE}; color: white;"
                        )


# ---------------------------------------------------------------------------
# Shared layout helpers
# ---------------------------------------------------------------------------

def _setup_dark() -> None:
    ui.dark_mode().enable()
    ui.query("body").style(f"background: {BG_MAIN}; color: {TEXT_PRIMARY};")
    ui.query(".nicegui-content").style("padding: 0;")


def _sidebar(active: str) -> None:
    with ui.column().style(
        f"background: {BG_SIDEBAR}; width: 240px; min-height: 100vh; "
        f"padding: 24px 16px; border-right: 1px solid {BORDER}; "
        f"gap: 4px; flex-shrink: 0;"
    ):
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
            ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 20px; font-weight: 700;")

        _section_label("MAIN")
        _nav_item("Dashboard",     active=(active == "Dashboard"),     route="/dashboard")

        ui.element("div").style("height: 16px;")
        _section_label("HISTORY")
        _nav_item("Alert History", active=(active == "Alert History"), route="/app")
        _nav_item("Reports",       active=(active == "Reports"),       route="/reports")

        ui.element("div").style("height: 16px;")
        _section_label("ACCOUNT")
        _nav_item("Settings",      active=(active == "Settings"),      route="/settings")
        _nav_item("Logout",        active=False,                       logout=True)


def _section_label(text: str) -> None:
    ui.label(text).style(
        f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1.5px; "
        f"font-weight: 600; padding: 8px 12px 4px;"
    )


def _nav_item(text: str, active: bool, route: str = None, logout: bool = False) -> None:
    style = (
        f"background: #2a3a52; color: {ACCENT_BLUE}; "
        f"border-left: 3px solid {ACCENT_BLUE}; "
        f"padding: 10px 12px 10px 13px; font-size: 14px; "
        f"border-radius: 0 6px 6px 0; cursor: pointer; font-weight: 500;"
    ) if active else (
        f"color: {TEXT_PRIMARY}; padding: 10px 16px; font-size: 14px; "
        f"border-radius: 6px; cursor: pointer;"
    )

    def on_click():
        if logout:
            app.storage.user.clear()
            ui.navigate.to("/")
        elif route:
            ui.navigate.to(route)

    ui.label(text).style(style).classes("hover:bg-gray-800").on("click", on_click)


def _header_user_chip() -> None:
    company  = app.storage.user.get("company", "")
    username = app.storage.user.get("username", "?")
    initials = (
        "".join(w[0].upper() for w in company.split()[:2]) if company else username[:2].upper()
    )
    with ui.row().classes("w-full items-center justify-end no-wrap").style("gap: 12px;"):
        ui.label(company or username).style(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        ui.label(initials).style(
            "background: #3a5aa0; color: white; width: 36px; height: 36px; "
            "border-radius: 50%; display: flex; align-items: center; "
            "justify-content: center; font-size: 13px; font-weight: 600;"
        )


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------

def _dashboard_main(location: LocationController, alert: AlertController, user_id: int = None) -> None:
    callbacks = {}

    with ui.column().classes("grow").style(
        f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
        f"padding: 24px 32px; gap: 20px;"
    ):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            with ui.column().style("gap: 4px;"):
                ui.label("Dashboard").style(
                    f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                )
                ui.label("Standorte verwalten & Wetter analysieren").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )
            ui.button(
                "Neuer Standort", icon="add_location",
                on_click=lambda: _open_add_dialog(location, callbacks, user_id),
            ).style(f"background: {ACCENT_BLUE}; color: white;")

        with ui.row().classes("w-full").style("gap: 24px; align-items: flex-start;"):
            locations_col = ui.column().style("width: 360px; flex-shrink: 0; gap: 12px;")
            alert_col     = ui.column().classes("grow").style("gap: 12px;")

        def refresh_locations():
            locations_col.clear()
            locs = location.list_locations(user_id=user_id)
            with locations_col:
                if not locs:
                    ui.label("Noch keine Standorte — klicke auf «Neuer Standort».").style(
                        f"color: {TEXT_MUTED}; font-style: italic;"
                    )
                for loc in locs:
                    _location_card(loc, alert, callbacks)

        def refresh_alerts():
            alert_col.clear()
            with alert_col:
                ui.label("Aktuelle Warnungen").style(
                    f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 600;"
                )
                alerts = alert.list_alerts(user_id=user_id)
                if not alerts:
                    ui.label("Keine Warnungen — alles im grünen Bereich! ✓").style(
                        "color: #4ec9a8; font-style: italic; font-size: 14px;"
                    )
                for a in alerts:
                    _alert_card(a)

        callbacks["refresh_locations"] = refresh_locations
        callbacks["refresh_alerts"]    = refresh_alerts
        refresh_locations()
        refresh_alerts()


async def _open_add_dialog(location: LocationController, callbacks: dict, user_id: int = None) -> None:
    dialog = ui.dialog().props("persistent")

    with dialog, ui.card().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 12px; padding: 28px; gap: 16px; "
        f"width: 680px; max-width: 95vw;"
    ):
        ui.label("Neuer Standort").style(
            f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 600;"
        )

        with ui.row().classes("w-full no-wrap").style("gap: 12px;"):
            name_input    = ui.input("Name *", placeholder="z.B. Baustelle Zürich HB").classes("grow")
            company_input = ui.input("Firma",  value=app.storage.user.get("company", "")).classes("grow")

        branch_select = ui.select(
            label="Branche (bestimmt Grenzwert-Vorschläge)",
            options=list(BRANCH_PRESETS.keys()),
            value="Bau",
        ).classes("w-full")

        ui.label("Standort auf Karte wählen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )

        marker_state = {"marker": None, "lat": None, "lon": None}

        with ui.row().classes("w-full no-wrap items-end").style("gap: 8px;"):
            search_input = ui.input(
                "Ort suchen", placeholder="z.B. Zürich HB, Bahnhof Olten …"
            ).classes("grow").on("keydown.enter", lambda: _search_and_show(
                search_input, results_container, leaflet_map, marker_state, coords_label
            ))
            ui.button(
                "Suchen", icon="search",
                on_click=lambda: _search_and_show(
                    search_input, results_container, leaflet_map, marker_state, coords_label
                ),
            ).props("flat")

        results_container = ui.column().classes("w-full").style("gap: 4px;")
        with ui.element("div").style("height: 260px; width: 100%;"):
            leaflet_map = ui.leaflet(center=(46.8, 8.2), zoom=8).style("height: 260px;")
        coords_label = ui.label("Klicke auf die Karte oder wähle ein Suchergebnis.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )

        def on_map_click(e):
            lat = e.args["latlng"]["lat"]
            lon = e.args["latlng"]["lng"]
            marker_state["lat"] = lat
            marker_state["lon"] = lon
            if marker_state["marker"]:
                marker_state["marker"].move(lat, lon)
            else:
                marker_state["marker"] = leaflet_map.marker(latlng=(lat, lon))
            coords_label.set_text(f"📍 {lat:.4f}°N, {lon:.4f}°E  (manuell gesetzt)")
            results_container.clear()

        leaflet_map.on("map-click", on_map_click)

        ui.label("Grenzwerte anpassen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )
        ui.label("Vorschläge je nach Branche — Werte sind anpassbar.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )

        threshold_container = ui.column().classes("w-full").style("gap: 8px;")
        threshold_inputs: list = []

        def build_threshold_inputs(branch: str):
            threshold_container.clear()
            threshold_inputs.clear()
            with threshold_container:
                for preset in BRANCH_PRESETS.get(branch, []):
                    color    = SEVERITY_COLORS.get(preset["severity"], TEXT_MUTED)
                    row_data = {}
                    with ui.row().classes("w-full items-center no-wrap").style(
                        f"background: {BG_INPUT}; border-radius: 8px; padding: 10px 14px; gap: 12px;"
                    ):
                        ui.element("div").style(
                            f"width: 10px; height: 10px; border-radius: 50%; "
                            f"background: {color}; flex-shrink: 0;"
                        )
                        ui.label(preset["label"]).style(
                            f"color: {TEXT_PRIMARY}; font-size: 13px; flex-grow: 1;"
                        )
                        ui.label(f"{preset['parameter']} {preset['operator']}").style(
                            f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace; flex-shrink: 0;"
                        )
                        row_data["value_input"] = ui.number(value=preset["value"]).style(
                            "width: 90px; flex-shrink: 0;"
                        )
                        row_data["preset"] = preset
                    threshold_inputs.append(row_data)

        build_threshold_inputs(branch_select.value)
        branch_select.on_value_change(lambda e: build_threshold_inputs(e.value))

        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

        with ui.row().classes("w-full justify-end").style("gap: 8px; margin-top: 4px;"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save():
                error_label.set_text("")
                if not name_input.value.strip():
                    error_label.set_text("Bitte einen Namen eingeben.")
                    return
                if marker_state["lat"] is None:
                    error_label.set_text("Bitte einen Punkt auf der Karte wählen.")
                    return

                # Build the threshold list for the controller
                t_list = [
                    {"preset": t["preset"], "value": t["value_input"].value}
                    for t in threshold_inputs
                ]
                loc = location.add_location(
                    name=name_input.value.strip(),
                    latitude=marker_state["lat"],
                    longitude=marker_state["lon"],
                    company=company_input.value.strip(),
                    branch=branch_select.value,
                    threshold_inputs=t_list,
                    user_id=user_id,
                )
                dialog.close()
                ui.notify(f"✓ Standort '{loc.name}' wurde hinzugefügt!", type="positive", position="top")
                callbacks["refresh_locations"]()

            ui.button("Hinzufügen", icon="add", on_click=save).style(
                f"background: {ACCENT_BLUE}; color: white;"
            )

    dialog.open()
    await asyncio.sleep(0.5)
    leaflet_map.run_map_method("invalidateSize")


def _search_and_show(search_input, results_container, leaflet_map, marker_state, coords_label):
    term = search_input.value.strip()
    if not term:
        return
    results_container.clear()
    try:
        resp = http_requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": term, "format": "json", "limit": 5, "addressdetails": 1},
            headers={"User-Agent": "WeatherGuard/1.0"},
            timeout=5,
        )
        data = resp.json()
    except Exception as e:
        ui.notify(f"Suche fehlgeschlagen: {e}", type="negative")
        return

    if not data:
        with results_container:
            ui.label("Keine Ergebnisse gefunden.").style(
                f"color: {TEXT_MUTED}; font-size: 13px; padding: 8px 12px;"
            )
        return

    with results_container:
        ui.label("Ergebnisse — klicke auf den richtigen Ort:").style(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 2px 4px;"
        )
        for item in data:
            _result_row(item, results_container, leaflet_map, marker_state, coords_label)


def _result_row(item, results_container, leaflet_map, marker_state, coords_label):
    lat        = float(item["lat"])
    lon        = float(item["lon"])
    display    = item.get("display_name", "")
    parts      = [p.strip() for p in display.split(",")]
    short_name = ", ".join(parts[:2])

    def select(lat=lat, lon=lon, name=short_name):
        results_container.clear()
        marker_state["lat"] = lat
        marker_state["lon"] = lon
        leaflet_map.run_map_method("setView", [lat, lon], 14)
        if marker_state["marker"]:
            marker_state["marker"].move(lat, lon)
        else:
            marker_state["marker"] = leaflet_map.marker(latlng=(lat, lon))
        coords_label.set_text(f"📍 {name}  ({lat:.4f}°N, {lon:.4f}°E)")

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px; "
        f"padding: 10px 14px; gap: 10px; cursor: pointer;"
    ).on("click", select):
        ui.icon("location_on").style(f"color: {ACCENT_BLUE}; font-size: 18px; flex-shrink: 0;")
        with ui.column().style("gap: 1px; overflow: hidden;"):
            ui.label(short_name).style(
                f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 500; "
                f"white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
            )
            ui.label(display).style(
                f"color: {TEXT_MUTED}; font-size: 11px; "
                f"white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
            )


def _location_card(location: Location, alert: AlertController, callbacks: dict) -> None:
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 16px; gap: 10px;"
    ):
        with ui.row().classes("items-start justify-between w-full no-wrap"):
            with ui.column().style("gap: 2px;"):
                ui.label(location.name).style(
                    f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
                )
                ui.label(f"{location.company} · {location.branch}").style(
                    f"color: {TEXT_MUTED}; font-size: 13px;"
                )
                ui.label(f"{location.latitude:.4f}°N, {location.longitude:.4f}°E").style(
                    f"color: {TEXT_MUTED}; font-size: 11px; font-family: monospace;"
                )

            with ui.row().style("gap: 4px;"):
                def run_analysis(loc=location):
                    ui.notify(f"Analyse läuft für {loc.name}…", type="info")
                    try:
                        new_alerts = alert.run_analysis(loc.id)
                        if new_alerts:
                            ui.notify(f"⚠ {len(new_alerts)} Warnung(en) für {loc.name}", type="warning")
                        else:
                            ui.notify(f"✓ Keine Warnungen für {loc.name}", type="positive")
                        callbacks["refresh_alerts"]()
                    except Exception as exc:
                        ui.notify(f"Fehler: {exc}", type="negative")

                ui.button(icon="refresh", on_click=run_analysis).props("flat size=sm").tooltip(
                    "Wetter prüfen & Alerts aktualisieren"
                )

                def delete_loc(loc=location):
                    alert_controller_ref = alert  # keep reference
                    from data_access.dao import LocationDAO  # noqa
                    callbacks_ref = callbacks
                    try:
                        alert_controller_ref._location_dao.delete(loc.id)
                    except Exception as exc:
                        ui.notify(f"Fehler: {exc}", type="negative")
                        return
                    ui.notify(f"'{loc.name}' gelöscht", type="info")
                    callbacks_ref["refresh_locations"]()
                    callbacks_ref["refresh_alerts"]()

                ui.button(icon="delete", on_click=delete_loc, color="red").props(
                    "flat size=sm"
                ).tooltip("Standort löschen")

        # Auto-loading weather row
        weather_row = ui.row().style("gap: 16px; flex-wrap: wrap; min-height: 32px;")

        def load_weather(loc=location):
            weather_row.clear()
            with weather_row:
                ui.spinner(size="xs")
            try:
                forecast = alert.get_current_weather(loc.latitude, loc.longitude)
                days     = forecast.get("days", [])
                weather_row.clear()
                if days and days[0].get("hours"):
                    h = days[0]["hours"][0]
                    with weather_row:
                        _weather_stat("🌡", f"{h.get('TTT_C', '–')}°C",       "Temp")
                        _weather_stat("💨", f"{h.get('FX_KMH', '–')} km/h",   "Wind")
                        _weather_stat("🌧", f"{h.get('RRR_MM', '–')} mm",     "Regen")
                        _weather_stat("❄",  f"{h.get('FRESHSNOW_CM', '–')} cm","Schnee")
                else:
                    with weather_row:
                        ui.label("Keine Wetterdaten").style(
                            f"color: {TEXT_MUTED}; font-size: 12px;"
                        )
            except Exception as exc:
                weather_row.clear()
                with weather_row:
                    ui.label(f"Fehler: {exc}").style("color: #f47174; font-size: 12px;")

        with weather_row:
            ui.spinner(size="xs")
        ui.timer(0.1, load_weather, once=True)

        if location.thresholds:
            with ui.expansion("Grenzwerte", icon="tune").classes("w-full"):
                for t in location.thresholds:
                    color = SEVERITY_COLORS.get(t.severity, TEXT_MUTED)
                    ui.label(f"{t.label}: {t.parameter} {t.operator} {t.value}").style(
                        f"color: {color}; font-size: 13px;"
                    )


def _weather_stat(icon: str, value: str, label: str) -> None:
    with ui.column().style("align-items: center; gap: 1px;"):
        ui.label(f"{icon} {value}").style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        ui.label(label).style(f"color: {TEXT_MUTED}; font-size: 10px;")


def _alert_card(alert: Alert) -> None:
    color    = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    bg_color = SEVERITY_BG.get(alert.severity, BG_CARD)
    loc_name = alert.location.name if alert.location else "Unbekannt"
    param_label = RiskAnalyzer.PARAMETER_LABELS.get(alert.parameter, alert.parameter)

    with ui.column().style(
        f"background: {bg_color}; border: 1px solid {color}; "
        f"border-left: 4px solid {color}; border-radius: 10px; "
        f"padding: 14px 16px; gap: 4px;"
    ):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label(alert.threshold_label).style(
                f"color: {color}; font-size: 15px; font-weight: 600;"
            )
            ui.label(alert.forecast_time.strftime("%d.%m. %H:%M")).style(
                f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace;"
            )
        ui.label(f"Standort: {loc_name}").style(f"color: {TEXT_PRIMARY}; font-size: 13px;")
        ui.label(
            f"{param_label}: {alert.actual_value} (Grenzwert: {alert.threshold_value})"
        ).style(f"color: {TEXT_MUTED}; font-size: 13px;")


# ---------------------------------------------------------------------------
# Alert History helpers
# ---------------------------------------------------------------------------

def _kpi_row(kpis: dict) -> None:
    cards = [
        ("Total Alerts", kpis["total"],   TEXT_PRIMARY),
        ("Danger",       kpis["danger"],  "#f47174"),
        ("Warning",      kpis["warning"], "#d4a24a"),
        ("Heute",        kpis["heute"],   TEXT_PRIMARY),
    ]
    with ui.row().classes("w-full no-wrap").style("gap: 16px;"):
        for label, value, color in cards:
            with ui.column().classes("grow").style(
                f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                f"border-radius: 10px; padding: 18px 20px; gap: 10px;"
            ):
                ui.label(label).style(f"color: {TEXT_MUTED}; font-size: 13px;")
                ui.label(str(value)).style(
                    f"color: {color}; font-size: 32px; font-weight: 600; line-height: 1;"
                )


def _charts_row(alerts_per_day: list, alerts_by_type: list) -> None:
    with ui.row().classes("w-full no-wrap").style("gap: 16px;"):
        _alerts_per_day_card(alerts_per_day)
        _alerts_by_type_card(alerts_by_type)


def _alerts_per_day_card(data: list) -> None:
    with ui.column().classes("grow").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Alerts per day").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )
        ui.echart({
            "grid": {"left": 10, "right": 10, "top": 10, "bottom": 30, "containLabel": True},
            "xAxis": {
                "type": "category",
                "data": [d[0] for d in data],
                "axisLine": {"lineStyle": {"color": BORDER}},
                "axisLabel": {"color": TEXT_MUTED, "fontSize": 12},
                "axisTick": {"show": False},
            },
            "yAxis": {"type": "value", "show": False},
            "series": [{
                "type": "bar",
                "data": [
                    {"value": d[1], "itemStyle": {"color": "#e05659" if d[2] else "#6b9dd4"}}
                    for d in data
                ],
                "barWidth": "55%",
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            }],
        }).style("height: 180px; width: 100%;")


def _alerts_by_type_card(data: list) -> None:
    with ui.column().classes("grow").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Alerts by type").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )
        if not data:
            ui.label("Noch keine Daten vorhanden.").style(
                f"color: {TEXT_MUTED}; font-size: 13px;"
            )
            return

        max_count = max(d[1] for d in data)
        with ui.column().classes("w-full").style("gap: 12px; padding: 8px 0;"):
            for name, count, color in data:
                with ui.row().classes("w-full items-center no-wrap").style("gap: 12px;"):
                    ui.label(name).style(f"color: {TEXT_PRIMARY}; font-size: 13px; width: 60px;")
                    with ui.element("div").style(
                        "flex-grow: 1; background: #1a1a1a; height: 16px; "
                        "border-radius: 4px; overflow: hidden;"
                    ):
                        ui.element("div").style(
                            f"background: {color}; height: 100%; "
                            f"width: {(count / max_count) * 85}%; border-radius: 4px;"
                        )
                    ui.label(str(count)).style(
                        f"color: {TEXT_PRIMARY}; font-size: 13px; width: 24px; text-align: right;"
                    )


def _recent_alerts_section(history: HistoryController, user_id: int = None) -> None:
    filter_state = {"active": "All"}

    with ui.column().classes("w-full").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Recent alerts").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        chips_row  = ui.row().classes("no-wrap").style("gap: 8px;")
        alert_list = ui.column().classes("w-full").style("gap: 10px; margin-top: 4px;")

        def refresh():
            alert_list.clear()
            with alert_list:
                rows = history.get_recent_alerts(filter_state["active"], user_id=user_id)
                if not rows:
                    ui.label("Keine Warnungen vorhanden.").style(
                        f"color: {TEXT_MUTED}; font-style: italic;"
                    )
                for a in rows:
                    _alert_history_row(a)

        def set_filter(label: str):
            filter_state["active"] = label
            chips_row.clear()
            _build_chips(chips_row, label, set_filter)
            refresh()

        def _build_chips(row, active_chip: str, on_click_fn):
            with row:
                for chip_label in ["All", "Frost", "Wind", "Rain", "Snow"]:
                    _filter_chip(chip_label, active=(chip_label == active_chip),
                                 on_click=lambda lbl=chip_label: on_click_fn(lbl))

        _build_chips(chips_row, filter_state["active"], set_filter)
        refresh()


def _filter_chip(label: str, active: bool, on_click=None) -> None:
    style = (
        f"background: #1e3558; color: {ACCENT_BLUE}; "
        f"border: 1px solid {ACCENT_BLUE}; padding: 6px 16px; "
        f"border-radius: 16px; font-size: 13px; cursor: pointer;"
    ) if active else (
        f"background: transparent; color: {TEXT_MUTED}; "
        f"border: 1px solid {BORDER}; padding: 6px 16px; "
        f"border-radius: 16px; font-size: 13px; cursor: pointer;"
    )
    el = ui.label(label).style(style)
    if on_click:
        el.on("click", on_click)


def _alert_history_row(alert: Alert) -> None:
    from datetime import datetime
    sev      = SEVERITY_STYLES.get(alert.severity, SEVERITY_STYLES["info"])
    loc_name = alert.location.name if alert.location else "Unbekannt"
    now      = datetime.now()
    if alert.created_at.date() == now.date():
        when = f"heute {alert.created_at.strftime('%H:%M')}"
    elif (now.date() - alert.created_at.date()).days == 1:
        when = f"gestern {alert.created_at.strftime('%H:%M')}"
    else:
        when = alert.created_at.strftime("%d.%m. %H:%M")

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_CARD_SOFT}; border: 1px solid {BORDER}; "
        f"border-radius: 8px; padding: 12px 16px; gap: 16px;"
    ):
        ui.label(sev["label"]).style(
            f"background: {sev['bg']}; color: {sev['color']}; "
            f"padding: 3px 10px; border-radius: 4px; font-size: 12px; "
            f"font-weight: 500; min-width: 68px; text-align: center;"
        )
        with ui.column().classes("grow").style("gap: 2px;"):
            ui.label(alert.threshold_label).style(
                f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;"
            )
            ui.label(
                f"{loc_name} · {alert.actual_value} (Grenzwert: {alert.threshold_value})"
            ).style(f"color: {TEXT_MUTED}; font-size: 13px;")
        ui.label(when).style(f"color: {TEXT_MUTED}; font-size: 12px; white-space: nowrap;")


# ---------------------------------------------------------------------------
# Reports helpers
# ---------------------------------------------------------------------------

def _reports_table_header() -> None:
    columns = [
        ("Datum",            "150px"),
        ("Standort",         "180px"),
        ("Warnung",          "210px"),
        ("Severity",         "90px"),
        ("Wert / Grenzwert", "160px"),
    ]
    with ui.row().classes("w-full no-wrap").style(
        f"background: #1f1f1f; padding: 12px 16px; gap: 16px; "
        f"border-bottom: 1px solid {BORDER};"
    ):
        for col, width in columns:
            ui.label(col).style(
                f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600; "
                f"width: {width}; flex-shrink: 0;"
            )


def _reports_table_row(alert: Alert, alternate: bool) -> None:
    color    = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    label    = {"critical": "danger", "warning": "warning"}.get(alert.severity, alert.severity)
    loc_name = alert.location.name if alert.location else "Unbekannt"
    bg       = BG_CARD_SOFT if alternate else BG_CARD

    with ui.row().classes("w-full no-wrap items-center").style(
        f"background: {bg}; padding: 11px 16px; gap: 16px; "
        f"border-bottom: 1px solid {BORDER};"
    ):
        ui.label(alert.created_at.strftime("%d.%m.%Y %H:%M")).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; "
            f"font-family: monospace; width: 150px; flex-shrink: 0;"
        )
        ui.label(loc_name).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 180px; flex-shrink: 0;"
        )
        ui.label(alert.threshold_label).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 210px; flex-shrink: 0;"
        )
        ui.label(label).style(
            f"color: {color}; font-size: 13px; font-weight: 500; "
            f"width: 90px; flex-shrink: 0;"
        )
        ui.label(f"{alert.actual_value} / {alert.threshold_value}").style(
            f"color: {TEXT_MUTED}; font-size: 13px; width: 160px; flex-shrink: 0;"
        )

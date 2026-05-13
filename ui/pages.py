"""NiceGUI Seiten (Pages).

Diese Datei enthält die ganze UI:
- /          → Login & Registrierung
- /app       → Alert History (Übersicht mit Statistiken)
- /dashboard → Dashboard (Standorte verwalten + aktuelle Warnungen)
- /reports   → Tabelle mit allen Alerts
- /settings  → Benutzer-Einstellungen

Die Klasse 'Pages' registriert die fünf Routen. Pro Seite gibt es weiter
unten in dieser Datei eine eigene Funktion (z.B. _render_login_page),
damit man nicht durch eine 1000-Zeilen-Funktion scrollen muss.

Die kleinen Helper am Ende (Sidebar, KPI-Karten, ...) werden von mehreren
Seiten benutzt.
"""

import asyncio

import requests
from nicegui import ui, app

from domain.models import Alert, Location
from ui.controllers import BRANCH_PRESETS, PARAM_TO_TYPE, TYPE_COLORS
from ui.dashboard_refresh import DashboardRefresh
from services.risk_analyzer import RiskAnalyzer


# ---------------------------------------------------------------------------
# Farben & Styles (werden überall benutzt, deshalb ganz oben als Konstanten)
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

# Farben pro Schweregrad
SEVERITY_COLORS = {"critical": "#f47174", "warning": "#d4a24a", "info": "#4a9eff"}
SEVERITY_BG     = {"critical": "#2d1515", "warning": "#2d2215", "info": "#15202d"}

# Anzeige-Style für die Severity-Badges
SEVERITY_STYLES = {
    "critical": {"color": "#f47174", "bg": "#3b1f22", "label": "danger"},
    "warning":  {"color": "#d4a24a", "bg": "#3a2e1a", "label": "warning"},
    "info":     {"color": "#4a9eff", "bg": "#1e2a3a", "label": "info"},
}


# ---------------------------------------------------------------------------
# Pages-Klasse: registriert alle Routen
# ---------------------------------------------------------------------------

class Pages:
    """Registriert alle Seiten/Routen der Web-App."""

    def __init__(self, auth_controller, location_controller, alert_controller, history_controller):
        self.auth = auth_controller
        self.location = location_controller
        self.alert = alert_controller
        self.history = history_controller

    def register(self):
        """Sagt NiceGUI, welche URL welche Funktion aufruft."""
        # Lokale Referenzen für die nested Funktionen unten
        auth = self.auth
        location = self.location
        alert = self.alert
        history = self.history

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


# ---------------------------------------------------------------------------
# Hilfsfunktionen, die mehrere Seiten benutzen
# ---------------------------------------------------------------------------

def _is_logged_in():
    """Prüft, ob ein User eingeloggt ist (anhand der Session-Variable)."""
    return app.storage.user.get("logged_in", False)


def _setup_dark_mode():
    """Aktiviert das dunkle Farbschema und entfernt das Standard-Padding."""
    ui.dark_mode().enable()
    ui.query("body").style(f"background: {BG_MAIN}; color: {TEXT_PRIMARY};")
    ui.query(".nicegui-content").style("padding: 0;")


# ===========================================================================
# SEITE 1: Login / Registrierung
# ===========================================================================

def _render_login_page(auth):
    """Login- und Registrierungs-Seite (URL '/')."""
    if _is_logged_in():
        ui.navigate.to("/app")
        return

    _setup_dark_mode()

    with ui.column().classes("absolute-center items-center").style("gap: 0;"):
        # Logo
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: 700;")
            ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 28px; font-weight: 700;")

        # Karte mit Tabs
        with ui.column().style(
            f"background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: 12px; padding: 32px 36px; gap: 16px; width: 340px;"
        ):
            # Tab-Switcher: Anmelden | Registrieren
            with ui.tabs().classes("w-full").props(f"active-color={ACCENT_BLUE}") as tabs:
                login_tab = ui.tab("Anmelden")
                register_tab = ui.tab("Registrieren")

            with ui.tab_panels(tabs, value=login_tab).classes("w-full").style(f"background: {BG_CARD};"):
                # --- Login-Tab ---
                with ui.tab_panel(login_tab).style("padding: 16px 0 0 0;"):
                    _render_login_form(auth)
                # --- Registrierungs-Tab ---
                with ui.tab_panel(register_tab).style("padding: 16px 0 0 0;"):
                    _render_register_form(auth)


def _render_login_form(auth):
    """Das eigentliche Login-Formular (innerhalb des "Anmelden"-Tabs)."""
    username_input = ui.input("Benutzername").classes("w-full")
    password_input = ui.input("Passwort", password=True, password_toggle_button=True).classes("w-full")
    error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 20px;")

    def try_login():
        user = auth.verify_login(username_input.value, password_input.value)
        if user is None:
            error_label.set_text("Benutzername oder Passwort falsch.")
            return
        # Login erfolgreich: Daten in die Session schreiben
        app.storage.user["logged_in"] = True
        app.storage.user["user_id"] = user.id
        app.storage.user["username"] = user.username
        app.storage.user["company"] = user.company
        ui.navigate.to("/app")

    ui.button("Login", on_click=try_login, icon="login").classes("w-full").style(
        f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
    )
    ui.label("Demo-Zugang: admin / admin123").style(
        f"color: {TEXT_MUTED}; font-size: 12px; text-align: center; margin-top: 4px;"
    )


def _render_register_form(auth):
    """Registrierungs-Formular (innerhalb des "Registrieren"-Tabs)."""
    username_input = ui.input("Benutzername *").classes("w-full")
    company_input = ui.input("Firma", placeholder="Optional").classes("w-full")
    password_input = ui.input("Passwort *", password=True, password_toggle_button=True).classes("w-full")
    confirm_input = ui.input("Passwort bestätigen *", password=True, password_toggle_button=True).classes("w-full")
    error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 20px;")

    def try_register():
        error_label.set_text("")
        error_message = auth.register(
            username_input.value,
            password_input.value,
            confirm_input.value,
            company_input.value,
        )
        if error_message:
            error_label.set_text(error_message)
            return
        ui.notify("Konto erstellt! Bitte einloggen.", type="positive")
        ui.navigate.to("/")

    ui.button("Konto erstellen", on_click=try_register, icon="person_add").classes("w-full").style(
        f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
    )


# ===========================================================================
# SEITE 2: Alert History (Übersichts-Seite)
# ===========================================================================

def _render_alert_history_page(history):
    """Alert History mit KPIs, Charts und Recent Alerts (URL '/app')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    user_id = app.storage.user.get("user_id")

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Alert History")

        with ui.column().classes("grow").style(
            f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
            f"padding: 24px 32px; gap: 20px;"
        ):
            _render_user_chip()

            # Titel
            with ui.column().style("gap: 4px;"):
                ui.label("Alert History").style(
                    f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                )
                ui.label("Alle Standorte · letzte 7 Tage").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )

            # KPI-Karten (Total, Danger, Warning, Heute)
            kpis = history.get_kpis(user_id=user_id)
            _render_kpi_row(kpis)

            # Charts (Alerts pro Tag, Alerts pro Typ)
            _render_charts_row(
                history.get_alerts_per_day(user_id=user_id),
                history.get_alerts_by_type(user_id=user_id),
            )

            # Recent Alerts mit Filter
            _render_recent_alerts_section(history, user_id)


# ===========================================================================
# SEITE 3: Dashboard (Standorte verwalten)
# ===========================================================================

def _render_dashboard_page(location, alert):
    """Dashboard mit Standorten und Live-Warnungen (URL '/dashboard')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    user_id = app.storage.user.get("user_id")

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Dashboard")
        _render_dashboard_main(location, alert, user_id)


def _render_dashboard_main(location, alert, user_id):
    """Der Haupt-Bereich des Dashboards (alles ausser Sidebar)."""
    # Dict für die Refresh-Callbacks (damit innere Funktionen die UI updaten können)
    refresh_callbacks = {}

    with ui.column().classes("grow").style(
        f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
        f"padding: 24px 32px; gap: 20px;"
    ):
        # Header-Bereich
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            with ui.column().style("gap: 4px;"):
                with ui.row().classes("items-baseline no-wrap").style("gap: 10px;"):
                    ui.label("Dashboard").style(
                        f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                    )
                    refresh_info = ui.label("").style(
                        f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 400;"
                    )
                ui.label("Standorte verwalten & Wetter analysieren").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )

            ui.button(
                "Neuer Standort",
                icon="add_location",
                on_click=lambda: _open_add_location_dialog(location, refresh_callbacks, user_id),
            ).style(f"background: {ACCENT_BLUE}; color: white;")

        # Zwei Spalten: Standorte links, Alerts rechts
        with ui.row().classes("w-full").style("gap: 24px; align-items: flex-start;"):
            locations_column = ui.column().style("width: 360px; flex-shrink: 0; gap: 12px;")
            alerts_column = ui.column().classes("grow").style("gap: 12px;")

        # Funktion: Standort-Spalte neu aufbauen
        def refresh_locations():
            locations_column.clear()
            user_locations = location.list_locations(user_id=user_id)
            with locations_column:
                if not user_locations:
                    ui.label("Noch keine Standorte — klicke auf «Neuer Standort».").style(
                        f"color: {TEXT_MUTED}; font-style: italic;"
                    )
                for loc in user_locations:
                    _render_location_card(loc, alert, refresh_callbacks)

        # Funktion: Alert-Spalte neu aufbauen
        def refresh_alerts():
            alerts_column.clear()
            with alerts_column:
                ui.label("Aktuelle Warnungen").style(
                    f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 600;"
                )
                user_alerts = alert.list_alerts(user_id=user_id)
                if not user_alerts:
                    ui.label("Keine Warnungen — alles im grünen Bereich! ✓").style(
                        "color: #4ec9a8; font-style: italic; font-size: 14px;"
                    )
                for a in user_alerts:
                    _render_alert_card(a)

        # Callbacks registrieren und initial laden
        refresh_callbacks["refresh_locations"] = refresh_locations
        refresh_callbacks["refresh_alerts"] = refresh_alerts
        refresh_locations()
        refresh_alerts()

        # Auto-Refresh starten
        dashboard_refresh = DashboardRefresh(
            refresh_label=refresh_info,
            alert_controller=alert,
            location_controller=location,
            refresh_callbacks=refresh_callbacks,
            user_id=user_id,
        )
        dashboard_refresh.start()


# ===========================================================================
# SEITE 4: Reports (Tabelle mit allen Alerts)
# ===========================================================================

def _render_reports_page(alert):
    """Reports-Tabelle mit allen Alerts (URL '/reports')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    user_id = app.storage.user.get("user_id")
    all_alerts = alert.list_alerts(user_id=user_id)

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Reports")

        with ui.column().classes("grow").style(
            f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
            f"padding: 24px 32px; gap: 20px;"
        ):
            # Titel
            with ui.column().style("gap: 4px;"):
                ui.label("Reports").style(
                    f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                )
                ui.label(f"{len(all_alerts)} Alerts insgesamt").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )

            # Tabelle
            with ui.column().classes("w-full").style(
                f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                f"border-radius: 10px; overflow: hidden;"
            ):
                _render_reports_table_header()
                if not all_alerts:
                    ui.label("Keine Alerts vorhanden.").style(
                        f"color: {TEXT_MUTED}; font-style: italic; padding: 20px 16px;"
                    )
                for index, a in enumerate(all_alerts):
                    is_alternate_row = (index % 2 == 1)
                    _render_reports_table_row(a, is_alternate_row)


# ===========================================================================
# SEITE 5: Settings (Account & Passwort ändern)
# ===========================================================================

def _render_settings_page(auth):
    """Settings-Seite (URL '/settings')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    username = app.storage.user.get("username", "")
    company = app.storage.user.get("company", "")

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Settings")

        with ui.column().classes("grow").style(
            f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
            f"padding: 24px 32px; gap: 24px;"
        ):
            ui.label("Settings").style(
                f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
            )

            # Karte 1: Account-Infos
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

            # Karte 2: Passwort ändern
            _render_change_password_card(auth, username)


def _render_change_password_card(auth, username):
    """Die "Passwort ändern"-Karte auf der Settings-Seite."""
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 24px; gap: 16px; max-width: 480px;"
    ):
        ui.label("Passwort ändern").style(
            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;"
        )
        current_pw = ui.input("Aktuelles Passwort", password=True, password_toggle_button=True).classes("w-full")
        new_pw = ui.input("Neues Passwort", password=True, password_toggle_button=True).classes("w-full")
        confirm_pw = ui.input("Passwort bestätigen", password=True, password_toggle_button=True).classes("w-full")
        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

        def save_password():
            error_label.set_text("")

            # Prüfen, ob die beiden neuen Passwörter übereinstimmen
            if new_pw.value != confirm_pw.value:
                error_label.set_text("Neue Passwörter stimmen nicht überein.")
                return

            # Controller machen lassen
            error_message = auth.change_password(username, current_pw.value, new_pw.value)
            if error_message:
                error_label.set_text(error_message)
                return

            # Erfolgreich: Felder leeren
            current_pw.value = ""
            new_pw.value = ""
            confirm_pw.value = ""
            ui.notify("Passwort erfolgreich geändert!", type="positive")

        ui.button("Speichern", on_click=save_password, icon="save").style(
            f"background: {ACCENT_BLUE}; color: white;"
        )


# ===========================================================================
# Sidebar (linke Navigation, auf allen Seiten gleich)
# ===========================================================================

def _render_sidebar(active_page):
    """Linke Sidebar mit Logo und Navigation."""
    with ui.column().style(
        f"background: {BG_SIDEBAR}; width: 240px; min-height: 100vh; "
        f"padding: 24px 16px; border-right: 1px solid {BORDER}; "
        f"gap: 4px; flex-shrink: 0;"
    ):
        # Logo
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
            ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 20px; font-weight: 700;")

        # Section: MAIN
        _render_section_label("MAIN")
        _render_nav_item("Dashboard", active=(active_page == "Dashboard"), route="/dashboard")

        ui.element("div").style("height: 16px;")

        # Section: HISTORY
        _render_section_label("HISTORY")
        _render_nav_item("Alert History", active=(active_page == "Alert History"), route="/app")
        _render_nav_item("Reports", active=(active_page == "Reports"), route="/reports")

        ui.element("div").style("height: 16px;")

        # Section: ACCOUNT
        _render_section_label("ACCOUNT")
        _render_nav_item("Settings", active=(active_page == "Settings"), route="/settings")
        _render_nav_item("Logout", active=False, is_logout=True)


def _render_section_label(text):
    """Kleine Section-Überschrift in der Sidebar (z.B. 'MAIN')."""
    ui.label(text).style(
        f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1.5px; "
        f"font-weight: 600; padding: 8px 12px 4px;"
    )


def _render_nav_item(text, active, route=None, is_logout=False):
    """Ein klickbarer Navigations-Eintrag in der Sidebar."""
    # Style je nach aktiv/inaktiv unterschiedlich
    if active:
        style = (
            f"background: #2a3a52; color: {ACCENT_BLUE}; "
            f"border-left: 3px solid {ACCENT_BLUE}; "
            f"padding: 10px 12px 10px 13px; font-size: 14px; "
            f"border-radius: 0 6px 6px 0; cursor: pointer; font-weight: 500;"
        )
    else:
        style = (
            f"color: {TEXT_PRIMARY}; padding: 10px 16px; font-size: 14px; "
            f"border-radius: 6px; cursor: pointer;"
        )

    def on_click():
        if is_logout:
            # Session löschen und zur Login-Seite
            app.storage.user.clear()
            ui.navigate.to("/")
        elif route is not None:
            ui.navigate.to(route)

    ui.label(text).style(style).classes("hover:bg-gray-800").on("click", on_click)


def _render_user_chip():
    """Der kleine User-Avatar oben rechts auf der Alert-History-Seite."""
    company = app.storage.user.get("company", "")
    username = app.storage.user.get("username", "?")

    # Initialen für den Avatar berechnen
    if company:
        # Erste Buchstaben der ersten zwei Wörter (max.)
        words = company.split()[:2]
        initials = "".join(word[0].upper() for word in words)
    else:
        initials = username[:2].upper()

    with ui.row().classes("w-full items-center justify-end no-wrap").style("gap: 12px;"):
        ui.label(company or username).style(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        ui.label(initials).style(
            "background: #3a5aa0; color: white; width: 36px; height: 36px; "
            "border-radius: 50%; display: flex; align-items: center; "
            "justify-content: center; font-size: 13px; font-weight: 600;"
        )


# ===========================================================================
# Dashboard-Helpers: Standort-Karten, Alert-Karten, Dialog zum Hinzufügen
# ===========================================================================

async def _open_add_location_dialog(location_controller, refresh_callbacks, user_id):
    """Öffnet den Dialog zum Hinzufügen eines neuen Standorts."""
    dialog = ui.dialog().props("persistent")

    with dialog, ui.card().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 12px; padding: 28px; gap: 16px; "
        f"width: 680px; max-width: 95vw;"
    ):
        ui.label("Neuer Standort").style(
            f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 600;"
        )

        # Name + Firma
        with ui.row().classes("w-full no-wrap").style("gap: 12px;"):
            name_input = ui.input("Name *", placeholder="z.B. Baustelle Zürich HB").classes("grow")
            company_input = ui.input("Firma", value=app.storage.user.get("company", "")).classes("grow")

        # Branche
        branch_select = ui.select(
            label="Branche (bestimmt Grenzwert-Vorschläge)",
            options=list(BRANCH_PRESETS.keys()),
            value="Bau",
        ).classes("w-full")

        # Karten-Bereich
        ui.label("Standort auf Karte wählen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )

        # Marker-Zustand: wir merken uns die geklickten Koordinaten
        marker_state = {"marker": None, "lat": None, "lon": None}

        # Such-Zeile
        search_results_container = ui.column().classes("w-full").style("gap: 4px;")
        coords_label_holder = {"label": None}

        with ui.row().classes("w-full no-wrap items-end").style("gap: 8px;"):
            search_input = ui.input(
                "Ort suchen",
                placeholder="z.B. Zürich HB, Bahnhof Olten …"
            ).classes("grow")

            def do_search():
                _search_location_and_show(
                    search_input.value,
                    search_results_container,
                    leaflet_map,
                    marker_state,
                    coords_label_holder["label"],
                )

            search_input.on("keydown.enter", do_search)
            ui.button("Suchen", icon="search", on_click=do_search).props("flat")

        # Die Karte selbst
        with ui.element("div").style("height: 260px; width: 100%;"):
            leaflet_map = ui.leaflet(center=(46.8, 8.2), zoom=8).style("height: 260px;")

        coords_label = ui.label("Klicke auf die Karte oder wähle ein Suchergebnis.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )
        coords_label_holder["label"] = coords_label

        # Karten-Klick verarbeiten
        def on_map_click(event):
            lat = event.args["latlng"]["lat"]
            lon = event.args["latlng"]["lng"]
            marker_state["lat"] = lat
            marker_state["lon"] = lon

            # Marker setzen oder verschieben
            if marker_state["marker"] is None:
                marker_state["marker"] = leaflet_map.marker(latlng=(lat, lon))
            else:
                marker_state["marker"].move(lat, lon)

            coords_label.set_text(f"📍 {lat:.4f}°N, {lon:.4f}°E  (manuell gesetzt)")
            search_results_container.clear()

        leaflet_map.on("map-click", on_map_click)

        # Grenzwert-Bereich
        ui.label("Grenzwerte anpassen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )
        ui.label("Vorschläge je nach Branche — Werte sind anpassbar.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )

        threshold_container = ui.column().classes("w-full").style("gap: 8px;")
        threshold_inputs = []  # Liste der UI-Elemente mit ihren Presets

        def build_threshold_inputs(branch):
            """Zeichnet die Grenzwert-Zeilen neu (z.B. wenn Branche geändert wurde)."""
            threshold_container.clear()
            threshold_inputs.clear()

            with threshold_container:
                presets = BRANCH_PRESETS.get(branch, [])
                for preset in presets:
                    row_data = _render_threshold_input_row(preset)
                    threshold_inputs.append(row_data)

        # Initial die Grenzwerte für die Standard-Branche zeichnen
        build_threshold_inputs(branch_select.value)
        branch_select.on_value_change(lambda event: build_threshold_inputs(event.value))

        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

        # Buttons unten
        with ui.row().classes("w-full justify-end").style("gap: 8px; margin-top: 4px;"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save():
                error_label.set_text("")

                # Name prüfen
                if not name_input.value.strip():
                    error_label.set_text("Bitte einen Namen eingeben.")
                    return
                # Karten-Punkt prüfen
                if marker_state["lat"] is None:
                    error_label.set_text("Bitte einen Punkt auf der Karte wählen.")
                    return

                # Threshold-Liste für den Controller bauen
                threshold_list = []
                for row in threshold_inputs:
                    threshold_list.append({
                        "preset": row["preset"],
                        "value": row["value_input"].value,
                    })

                # Speichern
                new_location = location_controller.add_location(
                    name=name_input.value.strip(),
                    latitude=marker_state["lat"],
                    longitude=marker_state["lon"],
                    company=company_input.value.strip(),
                    branch=branch_select.value,
                    threshold_inputs=threshold_list,
                    user_id=user_id,
                )
                dialog.close()
                ui.notify(
                    f"✓ Standort '{new_location.name}' wurde hinzugefügt!",
                    type="positive", position="top",
                )
                refresh_callbacks["refresh_locations"]()

            ui.button("Hinzufügen", icon="add", on_click=save).style(
                f"background: {ACCENT_BLUE}; color: white;"
            )

    dialog.open()
    # Kleiner Hack: Karten neu rendern, nachdem der Dialog offen ist
    await asyncio.sleep(0.5)
    leaflet_map.run_map_method("invalidateSize")


def _render_threshold_input_row(preset):
    """Eine Zeile im "Grenzwerte anpassen"-Bereich des Dialogs."""
    color = SEVERITY_COLORS.get(preset["severity"], TEXT_MUTED)

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_INPUT}; border-radius: 8px; padding: 10px 14px; gap: 12px;"
    ):
        # Farb-Punkt (zeigt Schweregrad)
        ui.element("div").style(
            f"width: 10px; height: 10px; border-radius: 50%; "
            f"background: {color}; flex-shrink: 0;"
        )
        # Label
        ui.label(preset["label"]).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; flex-grow: 1;"
        )
        # Parameter und Operator (z.B. "FX_KMH >")
        ui.label(f"{preset['parameter']} {preset['operator']}").style(
            f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace; flex-shrink: 0;"
        )
        # Wert (anpassbar)
        value_input = ui.number(value=preset["value"]).style("width: 90px; flex-shrink: 0;")

    return {"preset": preset, "value_input": value_input}


def _search_location_and_show(search_term, results_container, leaflet_map, marker_state, coords_label):
    """Sucht einen Ort via OpenStreetMap und zeigt die Ergebnisse an."""
    search_term = search_term.strip()
    if not search_term:
        return

    results_container.clear()

    # API-Aufruf an OpenStreetMap Nominatim
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_term, "format": "json", "limit": 5, "addressdetails": 1},
            headers={"User-Agent": "WeatherGuard/1.0"},
            timeout=5,
        )
        results = response.json()
    except Exception as error:
        ui.notify(f"Suche fehlgeschlagen: {error}", type="negative")
        return

    # Falls keine Ergebnisse
    if not results:
        with results_container:
            ui.label("Keine Ergebnisse gefunden.").style(
                f"color: {TEXT_MUTED}; font-size: 13px; padding: 8px 12px;"
            )
        return

    # Ergebnisse anzeigen
    with results_container:
        ui.label("Ergebnisse — klicke auf den richtigen Ort:").style(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 2px 4px;"
        )
        for item in results:
            _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label)


def _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label):
    """Eine einzelne Zeile mit einem Suchergebnis."""
    lat = float(item["lat"])
    lon = float(item["lon"])
    display_name = item.get("display_name", "")
    parts = [p.strip() for p in display_name.split(",")]
    short_name = ", ".join(parts[:2])

    def on_select():
        # Karte auf den Ort zentrieren und Marker setzen
        results_container.clear()
        marker_state["lat"] = lat
        marker_state["lon"] = lon
        leaflet_map.run_map_method("setView", [lat, lon], 14)

        if marker_state["marker"] is None:
            marker_state["marker"] = leaflet_map.marker(latlng=(lat, lon))
        else:
            marker_state["marker"].move(lat, lon)

        coords_label.set_text(f"📍 {short_name}  ({lat:.4f}°N, {lon:.4f}°E)")

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px; "
        f"padding: 10px 14px; gap: 10px; cursor: pointer;"
    ).on("click", on_select):
        ui.icon("location_on").style(f"color: {ACCENT_BLUE}; font-size: 18px; flex-shrink: 0;")
        with ui.column().style("gap: 1px; overflow: hidden;"):
            ui.label(short_name).style(
                f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 500; "
                f"white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
            )
            ui.label(display_name).style(
                f"color: {TEXT_MUTED}; font-size: 11px; "
                f"white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
            )


def _render_location_card(location, alert_controller, refresh_callbacks):
    """Eine Karte mit einem Standort (im Dashboard)."""
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 16px; gap: 10px;"
    ):
        # Obere Zeile: Info links, Buttons rechts
        with ui.row().classes("items-start justify-between w-full no-wrap"):
            # Info
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
            # Buttons
            _render_location_card_buttons(location, alert_controller, refresh_callbacks)

        # Wetter-Anzeige (wird asynchron geladen)
        weather_row = ui.row().style("gap: 16px; flex-wrap: wrap; min-height: 32px;")

        def load_weather():
            _fill_weather_row(weather_row, location, alert_controller)

        # Spinner während des Ladens
        with weather_row:
            ui.spinner(size="xs")
        # Wetter nachladen (asynchron, damit die UI nicht hängt)
        ui.timer(0.1, load_weather, once=True)

        # Grenzwerte ausklappbar anzeigen
        if location.thresholds:
            with ui.expansion("Grenzwerte", icon="tune").classes("w-full"):
                for threshold in location.thresholds:
                    color = SEVERITY_COLORS.get(threshold.severity, TEXT_MUTED)
                    ui.label(
                        f"{threshold.label}: {threshold.parameter} {threshold.operator} {threshold.value}"
                    ).style(f"color: {color}; font-size: 13px;")


def _render_location_card_buttons(location, alert_controller, refresh_callbacks):
    """Die Refresh- und Lösch-Buttons in der Standort-Karte."""
    with ui.row().style("gap: 4px;"):
        # Refresh-Button: Wetter prüfen
        def run_analysis():
            ui.notify(f"Analyse läuft für {location.name}…", type="info")
            try:
                new_alerts = alert_controller.run_analysis(location.id)
                if new_alerts:
                    ui.notify(
                        f"⚠ {len(new_alerts)} Warnung(en) für {location.name}",
                        type="warning",
                    )
                else:
                    ui.notify(f"✓ Keine Warnungen für {location.name}", type="positive")
                refresh_callbacks["refresh_alerts"]()
            except Exception as error:
                ui.notify(f"Fehler: {error}", type="negative")

        ui.button(icon="refresh", on_click=run_analysis).props("flat size=sm").tooltip(
            "Wetter prüfen & Alerts aktualisieren"
        )

        # Lösch-Button
        def delete_location():
            try:
                alert_controller.location_dao.delete(location.id)
            except Exception as error:
                ui.notify(f"Fehler: {error}", type="negative")
                return
            ui.notify(f"'{location.name}' gelöscht", type="info")
            refresh_callbacks["refresh_locations"]()
            refresh_callbacks["refresh_alerts"]()

        ui.button(icon="delete", on_click=delete_location, color="red").props(
            "flat size=sm"
        ).tooltip("Standort löschen")


def _fill_weather_row(weather_row, location, alert_controller):
    """Holt die Wetterdaten und füllt die Wetter-Zeile auf der Standort-Karte."""
    weather_row.clear()

    # Erst Spinner anzeigen
    with weather_row:
        ui.spinner(size="xs")

    # Wetterdaten holen
    try:
        forecast = alert_controller.get_current_weather(location.latitude, location.longitude)
        days = forecast.get("days", [])
        weather_row.clear()

        if not days or not days[0].get("hours"):
            with weather_row:
                ui.label("Keine Wetterdaten").style(
                    f"color: {TEXT_MUTED}; font-size: 12px;"
                )
            return

        # Erste Stunde des ersten Tags
        first_hour = days[0]["hours"][0]
        with weather_row:
            _render_weather_stat("🌡", f"{first_hour.get('TTT_C', '–')}°C",       "Temp")
            _render_weather_stat("💨", f"{first_hour.get('FX_KMH', '–')} km/h",   "Wind")
            _render_weather_stat("🌧", f"{first_hour.get('RRR_MM', '–')} mm",     "Regen")
            _render_weather_stat("❄",  f"{first_hour.get('FRESHSNOW_CM', '–')} cm","Schnee")
    except Exception as error:
        weather_row.clear()
        with weather_row:
            ui.label(f"Fehler: {error}").style("color: #f47174; font-size: 12px;")


def _render_weather_stat(icon, value, label):
    """Ein kleines Wetter-Element (Icon + Wert + Label)."""
    with ui.column().style("align-items: center; gap: 1px;"):
        ui.label(f"{icon} {value}").style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        ui.label(label).style(f"color: {TEXT_MUTED}; font-size: 10px;")


def _render_alert_card(alert):
    """Eine Alert-Karte im Dashboard (rechte Spalte)."""
    color = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    bg_color = SEVERITY_BG.get(alert.severity, BG_CARD)
    location_name = alert.location.name if alert.location else "Unbekannt"
    parameter_label = RiskAnalyzer.PARAMETER_LABELS.get(alert.parameter, alert.parameter)

    with ui.column().style(
        f"background: {bg_color}; border: 1px solid {color}; "
        f"border-left: 4px solid {color}; border-radius: 10px; "
        f"padding: 14px 16px; gap: 4px;"
    ):
        # Obere Zeile: Label links, Zeitpunkt rechts
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label(alert.threshold_label).style(
                f"color: {color}; font-size: 15px; font-weight: 600;"
            )
            ui.label(alert.forecast_time.strftime("%d.%m. %H:%M")).style(
                f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace;"
            )
        # Standort
        ui.label(f"Standort: {location_name}").style(
            f"color: {TEXT_PRIMARY}; font-size: 13px;"
        )
        # Wert und Grenzwert
        ui.label(
            f"{parameter_label}: {alert.actual_value} (Grenzwert: {alert.threshold_value})"
        ).style(f"color: {TEXT_MUTED}; font-size: 13px;")


# ===========================================================================
# Alert-History-Helpers: KPIs, Charts, Recent Alerts
# ===========================================================================

def _render_kpi_row(kpis):
    """Die 4 KPI-Karten oben auf der Alert-History-Seite."""
    # Liste der Karten: (Label, Wert, Farbe)
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


def _render_charts_row(alerts_per_day, alerts_by_type):
    """Die beiden Charts (Alerts pro Tag + Alerts pro Typ) nebeneinander."""
    with ui.row().classes("w-full no-wrap").style("gap: 16px;"):
        _render_alerts_per_day_chart(alerts_per_day)
        _render_alerts_by_type_chart(alerts_by_type)


def _render_alerts_per_day_chart(data):
    """Balken-Diagramm: Alerts pro Tag (letzte 7 Tage)."""
    with ui.column().classes("grow").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Alerts per day").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        # Daten für das Diagramm aufbereiten
        # data ist eine Liste von Tupeln: (Tagesname, Anzahl, ist_heute)
        x_axis_labels = [day[0] for day in data]
        bar_data = []
        for day_name, count, is_today in data:
            # Heute = rote Farbe, andere Tage = blau
            color = "#e05659" if is_today else "#6b9dd4"
            bar_data.append({"value": count, "itemStyle": {"color": color}})

        ui.echart({
            "grid": {"left": 10, "right": 10, "top": 10, "bottom": 30, "containLabel": True},
            "xAxis": {
                "type": "category",
                "data": x_axis_labels,
                "axisLine": {"lineStyle": {"color": BORDER}},
                "axisLabel": {"color": TEXT_MUTED, "fontSize": 12},
                "axisTick": {"show": False},
            },
            "yAxis": {"type": "value", "show": False},
            "series": [{
                "type": "bar",
                "data": bar_data,
                "barWidth": "55%",
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            }],
        }).style("height: 180px; width: 100%;")


def _render_alerts_by_type_chart(data):
    """Horizontale Balken: Alerts pro Kategorie (Wind, Frost, Rain, Snow)."""
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

        # Grösste Anzahl finden (für die Balken-Skalierung)
        max_count = max(item[1] for item in data)

        with ui.column().classes("w-full").style("gap: 12px; padding: 8px 0;"):
            for name, count, color in data:
                with ui.row().classes("w-full items-center no-wrap").style("gap: 12px;"):
                    # Label
                    ui.label(name).style(f"color: {TEXT_PRIMARY}; font-size: 13px; width: 60px;")
                    # Balken-Hintergrund + bunter Balken drin
                    with ui.element("div").style(
                        "flex-grow: 1; background: #1a1a1a; height: 16px; "
                        "border-radius: 4px; overflow: hidden;"
                    ):
                        bar_width_percent = (count / max_count) * 85
                        ui.element("div").style(
                            f"background: {color}; height: 100%; "
                            f"width: {bar_width_percent}%; border-radius: 4px;"
                        )
                    # Zahl rechts
                    ui.label(str(count)).style(
                        f"color: {TEXT_PRIMARY}; font-size: 13px; width: 24px; text-align: right;"
                    )


def _render_recent_alerts_section(history, user_id):
    """Der "Recent alerts"-Abschnitt mit Filter-Chips und Alert-Liste."""
    # Dict statt Variable, weil innere Funktionen den Wert ändern müssen
    filter_state = {"active": "All"}

    with ui.column().classes("w-full").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Recent alerts").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        chips_row = ui.row().classes("no-wrap").style("gap: 8px;")
        alert_list_column = ui.column().classes("w-full").style("gap: 10px; margin-top: 4px;")

        def refresh_alert_list():
            """Liste neu zeichnen mit dem aktuellen Filter."""
            alert_list_column.clear()
            with alert_list_column:
                filtered_alerts = history.get_recent_alerts(filter_state["active"], user_id=user_id)
                if not filtered_alerts:
                    ui.label("Keine Warnungen vorhanden.").style(
                        f"color: {TEXT_MUTED}; font-style: italic;"
                    )
                for a in filtered_alerts:
                    _render_alert_history_row(a)

        def set_filter(new_filter):
            """Wird aufgerufen, wenn ein Filter-Chip geklickt wird."""
            filter_state["active"] = new_filter
            # Chips neu zeichnen (damit der aktive Chip hervorgehoben wird)
            chips_row.clear()
            _build_filter_chips(chips_row, new_filter, set_filter)
            # Alert-Liste neu zeichnen
            refresh_alert_list()

        # Initial: Chips und Liste zeichnen
        _build_filter_chips(chips_row, filter_state["active"], set_filter)
        refresh_alert_list()


def _build_filter_chips(chips_row, active_chip, on_click_callback):
    """Zeichnet die Filter-Chips (All, Frost, Wind, Rain, Snow)."""
    chip_labels = ["All", "Frost", "Wind", "Rain", "Snow"]
    with chips_row:
        for chip_label in chip_labels:
            is_active = (chip_label == active_chip)
            # Lambda mit Default-Argument, damit chip_label korrekt gebunden wird
            _render_filter_chip(
                chip_label,
                active=is_active,
                on_click=lambda label=chip_label: on_click_callback(label),
            )


def _render_filter_chip(label, active, on_click):
    """Ein einzelner Filter-Chip (klickbarer Pill-Button)."""
    if active:
        style = (
            f"background: #1e3558; color: {ACCENT_BLUE}; "
            f"border: 1px solid {ACCENT_BLUE}; padding: 6px 16px; "
            f"border-radius: 16px; font-size: 13px; cursor: pointer;"
        )
    else:
        style = (
            f"background: transparent; color: {TEXT_MUTED}; "
            f"border: 1px solid {BORDER}; padding: 6px 16px; "
            f"border-radius: 16px; font-size: 13px; cursor: pointer;"
        )
    chip_element = ui.label(label).style(style)
    if on_click is not None:
        chip_element.on("click", on_click)


def _render_alert_history_row(alert):
    """Eine Zeile in der "Recent alerts"-Liste."""
    from datetime import datetime

    severity_style = SEVERITY_STYLES.get(alert.severity, SEVERITY_STYLES["info"])
    location_name = alert.location.name if alert.location else "Unbekannt"

    # Zeitstempel hübsch formatieren
    now = datetime.now()
    alert_date = alert.created_at.date()
    if alert_date == now.date():
        when_text = f"heute {alert.created_at.strftime('%H:%M')}"
    elif (now.date() - alert_date).days == 1:
        when_text = f"gestern {alert.created_at.strftime('%H:%M')}"
    else:
        when_text = alert.created_at.strftime("%d.%m. %H:%M")

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_CARD_SOFT}; border: 1px solid {BORDER}; "
        f"border-radius: 8px; padding: 12px 16px; gap: 16px;"
    ):
        # Severity-Badge
        ui.label(severity_style["label"]).style(
            f"background: {severity_style['bg']}; color: {severity_style['color']}; "
            f"padding: 3px 10px; border-radius: 4px; font-size: 12px; "
            f"font-weight: 500; min-width: 68px; text-align: center;"
        )
        # Info-Spalte
        with ui.column().classes("grow").style("gap: 2px;"):
            ui.label(alert.threshold_label).style(
                f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;"
            )
            ui.label(
                f"{location_name} · {alert.actual_value} (Grenzwert: {alert.threshold_value})"
            ).style(f"color: {TEXT_MUTED}; font-size: 13px;")
        # Zeit
        ui.label(when_text).style(f"color: {TEXT_MUTED}; font-size: 12px; white-space: nowrap;")


# ===========================================================================
# Reports-Helpers: Tabellen-Header und -Zeilen
# ===========================================================================

# Spalten der Reports-Tabelle: (Name, Breite)
REPORT_COLUMNS = [
    ("Datum",            "150px"),
    ("Standort",         "180px"),
    ("Warnung",          "210px"),
    ("Severity",         "90px"),
    ("Wert / Grenzwert", "160px"),
]


def _render_reports_table_header():
    """Die Kopfzeile der Reports-Tabelle."""
    with ui.row().classes("w-full no-wrap").style(
        f"background: #1f1f1f; padding: 12px 16px; gap: 16px; "
        f"border-bottom: 1px solid {BORDER};"
    ):
        for column_name, column_width in REPORT_COLUMNS:
            ui.label(column_name).style(
                f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600; "
                f"width: {column_width}; flex-shrink: 0;"
            )


def _render_reports_table_row(alert, is_alternate):
    """Eine Daten-Zeile in der Reports-Tabelle."""
    color = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    # "critical" als "danger" anzeigen
    severity_label = "danger" if alert.severity == "critical" else alert.severity
    location_name = alert.location.name if alert.location else "Unbekannt"
    # Jede zweite Zeile etwas heller (Streifen-Effekt)
    background = BG_CARD_SOFT if is_alternate else BG_CARD

    with ui.row().classes("w-full no-wrap items-center").style(
        f"background: {background}; padding: 11px 16px; gap: 16px; "
        f"border-bottom: 1px solid {BORDER};"
    ):
        # Datum
        ui.label(alert.created_at.strftime("%d.%m.%Y %H:%M")).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; "
            f"font-family: monospace; width: 150px; flex-shrink: 0;"
        )
        # Standort
        ui.label(location_name).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 180px; flex-shrink: 0;"
        )
        # Warnung
        ui.label(alert.threshold_label).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 210px; flex-shrink: 0;"
        )
        # Severity
        ui.label(severity_label).style(
            f"color: {color}; font-size: 13px; font-weight: 500; "
            f"width: 90px; flex-shrink: 0;"
        )
        # Wert / Grenzwert
        ui.label(f"{alert.actual_value} / {alert.threshold_value}").style(
            f"color: {TEXT_MUTED}; font-size: 13px; width: 160px; flex-shrink: 0;"
        )

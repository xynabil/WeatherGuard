"""Gemeinsame Komponenten und Konstanten.

Alle Farben, Styles und Hilfs-Funktionen, die auf mehreren Seiten
verwendet werden (Sidebar, Navigation, User-Chip usw.).
"""

from datetime import timedelta

from nicegui import ui, app


# ---------------------------------------------------------------------------
# Farben & Styles – zentral definiert, damit alle Seiten gleich aussehen
# ---------------------------------------------------------------------------

BG_MAIN      = "#1a1a1a"   # Hintergrund der ganzen Seite
BG_SIDEBAR   = "#1f1f1f"   # Hintergrund der linken Sidebar
BG_CARD      = "#262626"   # Hintergrund von Karten und Tabellen
BG_CARD_SOFT = "#2d2d2d"   # Etwas hellere Karten (Streifen-Effekt in Tabellen)
BG_INPUT     = "#1f1f1f"   # Hintergrund von Eingabefeldern
TEXT_PRIMARY = "#e8e8e8"   # Haupt-Textfarbe (fast weiss)
TEXT_MUTED   = "#888"      # Gedämpfte Textfarbe für Labels und Hinweise
ACCENT_BLUE  = "#4a9eff"   # Akzentfarbe für Buttons, aktive Navigation usw.
BORDER       = "#333"      # Rahmenfarbe für Karten und Trennlinien

# Farben für Schweregrade (critical = rot, warning = gelb, info = blau)
SEVERITY_COLORS = {"critical": "#f47174", "warning": "#d4a24a", "info": "#4a9eff"}
SEVERITY_BG     = {"critical": "#2d1515", "warning": "#2d2215", "info": "#15202d"}

# Vollständiger Style pro Schweregrad (Farbe + Hintergrund + Anzeigetext)
SEVERITY_STYLES = {
    "critical": {"color": "#f47174", "bg": "#3b1f22", "label": "danger"},
    "warning":  {"color": "#d4a24a", "bg": "#3a2e1a", "label": "warning"},
    "info":     {"color": "#4a9eff", "bg": "#1e2a3a", "label": "info"},
}

# Zeitraum-Optionen für Dropdowns – None bedeutet kein Zeitfilter (= alle)
TIME_RANGES = {
    "All":        None,
    "Last day":   timedelta(days=1),
    "Last week":  timedelta(weeks=1),
    "Last month": timedelta(days=30),
    "Last year":  timedelta(days=365),
}


# ---------------------------------------------------------------------------
# Hilfs-Funktionen – werden auf mehreren Seiten aufgerufen
# ---------------------------------------------------------------------------

def _is_logged_in():
    """Prüft, ob ein User eingeloggt ist (anhand der Session-Variable)."""
    return app.storage.user.get("logged_in", False)


def _setup_dark_mode():
    """Aktiviert das dunkle Farbschema und entfernt das Standard-Padding."""
    ui.dark_mode().enable()
    ui.query("body").style(f"background: {BG_MAIN}; color: {TEXT_PRIMARY};")
    ui.query(".nicegui-content").style("padding: 0;")


# ---------------------------------------------------------------------------
# Sidebar – linke Navigation, auf allen Seiten identisch
# ---------------------------------------------------------------------------

def _render_sidebar(active_page):
    """Linke Sidebar mit Logo und Navigation."""
    with ui.column().style(
        f"background: {BG_SIDEBAR}; width: 240px; min-height: 100vh; "
        f"padding: 24px 16px; border-right: 1px solid {BORDER}; "
        f"gap: 4px; flex-shrink: 0;"
    ):
        # Logo oben links
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;")
            ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 20px; font-weight: 700;")

        # Abschnitt: Hauptseiten
        _render_section_label("MAIN")
        _render_nav_item("Dashboard", active=(active_page == "Dashboard"), route="/dashboard")

        ui.element("div").style("height: 16px;")

        # Abschnitt: Verlauf
        _render_section_label("HISTORY")
        _render_nav_item("Alert History", active=(active_page == "Alert History"), route="/app")
        _render_nav_item("Reports", active=(active_page == "Reports"), route="/reports")

        ui.element("div").style("height: 16px;")

        # Abschnitt: Konto
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
    # Aktiver Eintrag wird blau hervorgehoben, inaktive sind grau
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
            # Session löschen und zur Login-Seite zurück
            app.storage.user.clear()
            ui.navigate.to("/")
        elif route is not None:
            ui.navigate.to(route)

    ui.label(text).style(style).classes("hover:bg-gray-800").on("click", on_click)


def _render_user_chip():
    """Der kleine User-Avatar oben rechts auf der Alert-History-Seite."""
    company  = app.storage.user.get("company", "")
    username = app.storage.user.get("username", "?")

    # Initialen aus Firmenname (max. 2 Wörter) oder Username berechnen
    if company:
        words    = company.split()[:2]
        initials = "".join(word[0].upper() for word in words)
    else:
        initials = username[:2].upper()

    with ui.row().classes("w-full items-center justify-end no-wrap").style("gap: 12px;"):
        ui.label(company or username).style(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        # Runder Avatar mit den Initialen
        ui.label(initials).style(
            "background: #3a5aa0; color: white; width: 36px; height: 36px; "
            "border-radius: 50%; display: flex; align-items: center; "
            "justify-content: center; font-size: 13px; font-weight: 600;"
        )

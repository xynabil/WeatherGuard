"""Alert History Seite mit Dark Theme, Sidebar, KPIs und Charts.

Nutzt aktuell Mock-Daten, um das Layout aus dem Mockup zu treffen.
Später auf echte DB-Queries umstellen.
"""
from nicegui import ui


# ---------- Mock-Daten ----------

KPIS = {
    "total": 24,
    "danger": 7,
    "warning": 17,
    "unread": 3,
}

ALERTS_PER_DAY = [
    ("Mo", 3, False),
    ("Di", 5, False),
    ("Mi", 2, False),
    ("Do", 7, True),   # highlighted
    ("Fr", 4, False),
    ("Sa", 1, False),
    ("So", 2, False),
]

ALERTS_BY_TYPE = [
    ("Wind", 11, "#4a9eff"),
    ("Frost", 7, "#4ec9a8"),
    ("Rain", 6, "#b197fc"),
]

RECENT_ALERTS = [
    {
        "severity": "danger",
        "type": "Wind",
        "title": "Wind",
        "description": "Wind 72 km/h – above threshold 40 km/h",
        "when": "heute 08:14",
    },
    {
        "severity": "warning",
        "type": "Frost",
        "title": "Frost",
        "description": "Temp 1.5°C – below threshold 2°C",
        "when": "gestern 06:30",
    },
    {
        "severity": "warning",
        "type": "Rain",
        "title": "Rain",
        "description": "Precipitation 18 mm – above threshold 10 mm",
        "when": "gestern 14:55",
    },
]

SEVERITY_STYLES = {
    "danger":  {"color": "#f47174", "bg": "#3b1f22"},
    "warning": {"color": "#d4a24a", "bg": "#3a2e1a"},
    "info":    {"color": "#4a9eff", "bg": "#1e2a3a"},
}

# ---------- Theme ----------

BG_MAIN = "#1a1a1a"
BG_SIDEBAR = "#1f1f1f"
BG_CARD = "#262626"
BG_CARD_SOFT = "#2d2d2d"
TEXT_PRIMARY = "#e8e8e8"
TEXT_MUTED = "#888"
ACCENT_BLUE = "#4a9eff"
BORDER = "#333"


def build_alert_history_page():
    """Baut die komplette Alert-History-Seite."""

    # Dark Mode aktivieren + Hintergrund setzen
    ui.dark_mode().enable()
    ui.query("body").style(f"background: {BG_MAIN}; color: {TEXT_PRIMARY};")
    ui.query(".nicegui-content").style("padding: 0;")

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _build_sidebar()
        _build_main_content()


def _build_sidebar():
    """Linke Navigations-Sidebar."""
    with ui.column().style(
        f"background: {BG_SIDEBAR}; width: 240px; height: 100vh; "
        f"padding: 24px 16px; border-right: 1px solid {BORDER}; gap: 4px;"
    ):
        # Logo
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(
                f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700;"
            )
            ui.label("Guard").style(
                f"color: {ACCENT_BLUE}; font-size: 20px; font-weight: 700;"
            )

        _section_label("MAIN")
        _nav_item("Dashboard", active=False)
        _nav_item("Locations", active=False)
        _nav_item("Thresholds", active=False)

        ui.element("div").style("height: 16px;")
        _section_label("HISTORY")
        _nav_item("Alert History", active=True)
        _nav_item("Reports", active=False)

        ui.element("div").style("height: 16px;")
        _section_label("ACCOUNT")
        _nav_item("Settings", active=False)
        _nav_item("Logout", active=False)


def _section_label(text: str):
    ui.label(text).style(
        f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1.5px; "
        f"font-weight: 600; padding: 8px 12px 4px;"
    )


def _nav_item(text: str, active: bool):
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
    ui.label(text).style(style).classes("hover:bg-gray-800")


def _build_main_content():
    """Hauptinhalt rechts."""
    with ui.column().classes("grow").style(
        f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; padding: 24px 32px; gap: 20px;"
    ):
        _build_header()
        _build_title_block()
        _build_kpi_row()
        _build_charts_row()
        _build_recent_alerts()


def _build_header():
    """Top-rechts: Firma + Avatar."""
    with ui.row().classes("w-full items-center justify-end no-wrap").style("gap: 12px;"):
        ui.label("Müller Bau AG").style(f"color: {TEXT_PRIMARY}; font-size: 14px;")
        ui.label("MB").style(
            f"background: #3a5aa0; color: white; width: 36px; height: 36px; "
            f"border-radius: 50%; display: flex; align-items: center; justify-content: center; "
            f"font-size: 13px; font-weight: 600;"
        )


def _build_title_block():
    with ui.column().style("gap: 4px;"):
        ui.label("Alert history").style(
            f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
        )
        ui.label("Baustelle Olten Zentrum · last 7 days").style(
            f"color: {TEXT_MUTED}; font-size: 14px;"
        )


def _build_kpi_row():
    """4 KPI-Karten."""
    cards = [
        ("Total alerts", KPIS["total"], TEXT_PRIMARY),
        ("Danger", KPIS["danger"], "#f47174"),
        ("Warning", KPIS["warning"], "#d4a24a"),
        ("Unread", KPIS["unread"], TEXT_PRIMARY),
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


def _build_charts_row():
    """Zwei Chart-Karten nebeneinander."""
    with ui.row().classes("w-full no-wrap").style("gap: 16px;"):
        _build_alerts_per_day_card()
        _build_alerts_by_type_card()


def _build_alerts_per_day_card():
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
                "data": [d[0] for d in ALERTS_PER_DAY],
                "axisLine": {"lineStyle": {"color": BORDER}},
                "axisLabel": {"color": TEXT_MUTED, "fontSize": 12},
                "axisTick": {"show": False},
            },
            "yAxis": {"type": "value", "show": False},
            "series": [{
                "type": "bar",
                "data": [
                    {
                        "value": d[1],
                        "itemStyle": {"color": "#e05659" if d[2] else "#6b9dd4"},
                    }
                    for d in ALERTS_PER_DAY
                ],
                "barWidth": "55%",
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            }],
        }).style("height: 180px; width: 100%;")


def _build_alerts_by_type_card():
    with ui.column().classes("grow").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Alerts by type").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        with ui.column().classes("w-full").style("gap: 12px; padding: 8px 0;"):
            max_count = max(row[1] for row in ALERTS_BY_TYPE)
            for name, count, color in ALERTS_BY_TYPE:
                with ui.row().classes("w-full items-center no-wrap").style("gap: 12px;"):
                    ui.label(name).style(
                        f"color: {TEXT_PRIMARY}; font-size: 13px; width: 60px;"
                    )
                    # Bar-Container
                    with ui.element("div").style(
                        f"flex-grow: 1; background: #1a1a1a; height: 16px; "
                        f"border-radius: 4px; overflow: hidden;"
                    ):
                        ui.element("div").style(
                            f"background: {color}; height: 100%; "
                            f"width: {(count / max_count) * 85}%; border-radius: 4px;"
                        )
                    ui.label(str(count)).style(
                        f"color: {TEXT_PRIMARY}; font-size: 13px; width: 24px; text-align: right;"
                    )


def _build_recent_alerts():
    """Liste der letzten Alerts mit Filter-Chips."""
    with ui.column().classes("w-full").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Recent alerts").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        # Filter-Chips
        with ui.row().classes("no-wrap").style("gap: 8px;"):
            for i, chip in enumerate(["All", "Frost", "Wind", "Rain", "Unread"]):
                _filter_chip(chip, active=(i == 0))

        # Alert-Liste
        with ui.column().classes("w-full").style("gap: 10px; margin-top: 4px;"):
            for alert in RECENT_ALERTS:
                _alert_row(alert)


def _filter_chip(label: str, active: bool):
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
    ui.label(label).style(style)


def _alert_row(alert: dict):
    sev = SEVERITY_STYLES[alert["severity"]]
    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_CARD_SOFT}; border: 1px solid {BORDER}; "
        f"border-radius: 8px; padding: 12px 16px; gap: 16px;"
    ):
        # Severity-Badge
        ui.label(alert["severity"]).style(
            f"background: {sev['bg']}; color: {sev['color']}; "
            f"padding: 3px 10px; border-radius: 4px; font-size: 12px; "
            f"font-weight: 500; min-width: 68px; text-align: center;"
        )

        # Title + Description
        with ui.column().classes("grow").style("gap: 2px;"):
            ui.label(alert["title"]).style(
                f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;"
            )
            ui.label(alert["description"]).style(
                f"color: {TEXT_MUTED}; font-size: 13px;"
            )

        # Timestamp
        ui.label(alert["when"]).style(
            f"color: {TEXT_MUTED}; font-size: 12px; white-space: nowrap;"
        )

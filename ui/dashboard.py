from nicegui import ui

from database import get_session
from models.location import Location
from models.threshold import WeatherThreshold
from models.alert import Alert
from services.weather_client import WeatherClient
from services.risk_analyzer import RiskAnalyzer

# Vordefinierte Threshold-Vorlagen pro Branche
BRANCH_PRESETS = {
    "Bau": [
        {"parameter": "TTT_C", "operator": "<", "value": 5.0, "label": "Frost (Betonarbeiten)", "severity": "critical"},
        {"parameter": "FX_KMH", "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)", "severity": "critical"},
        {"parameter": "RRR_MM", "operator": ">", "value": 10.0, "label": "Starkregen", "severity": "warning"},
    ],
    "Event": [
        {"parameter": "FX_KMH", "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)", "severity": "critical"},
        {"parameter": "RRR_MM", "operator": ">", "value": 5.0, "label": "Regen (Outdoor)", "severity": "warning"},
        {"parameter": "TTT_C", "operator": "<", "value": 0.0, "label": "Frost (Glätte)", "severity": "warning"},
    ],
    "Lieferdienst": [
        {"parameter": "FRESHSNOW_CM", "operator": ">", "value": 5.0, "label": "Schneefall", "severity": "warning"},
        {"parameter": "FX_KMH", "operator": ">", "value": 70.0, "label": "Orkan", "severity": "critical"},
        {"parameter": "TTT_C", "operator": "<", "value": -5.0, "label": "Extremkälte", "severity": "critical"},
    ],
}

SEVERITY_COLORS = {
    "critical": "#e53935",
    "warning": "#ff9800",
    "info": "#2196f3",
}

# Gemeinsamer State damit Panels sich gegenseitig aktualisieren können
_state = {"refresh_alerts": lambda: None}


def build_dashboard():
    """Baut das komplette NiceGUI Dashboard."""
    weather_client = WeatherClient()
    analyzer = RiskAnalyzer(weather_client)

    # --- Header ---
    with ui.header().classes("bg-blue-900 text-white items-center justify-between"):
        ui.label("Weather Guard").classes("text-2xl font-bold")
        ui.label("B2B Logistics Planungstool").classes("text-sm opacity-70")

    # --- Haupt-Layout ---
    with ui.row().classes("w-full p-4 gap-4"):
        # Linke Spalte: Standorte
        with ui.column().classes("w-1/3"):
            _build_location_panel(analyzer)

        # Rechte Spalte: Alerts
        with ui.column().classes("w-2/3"):
            _build_alert_panel()


def _build_location_panel(analyzer: RiskAnalyzer):
    """Panel zum Verwalten und Analysieren von Standorten."""
    ui.label("Standorte").classes("text-xl font-bold mb-2")

    locations_container = ui.column().classes("w-full gap-2")

    def refresh_locations():
        locations_container.clear()
        session = get_session()
        locations = session.query(Location).all()
        session.close()

        with locations_container:
            if not locations:
                ui.label("Keine Standorte vorhanden.").classes("text-gray-500 italic")
            for loc in locations:
                _build_location_card(loc, analyzer, refresh_locations, lambda: _state["refresh_alerts"]())

    # --- Formular: Neuer Standort ---
    with ui.card().classes("w-full"):
        ui.label("Neuer Standort").classes("font-bold")
        name_input = ui.input("Name", placeholder="z.B. Baustelle Zürich")
        lat_input = ui.number("Breitengrad", value=47.38, format="%.4f")
        lon_input = ui.number("Längengrad", value=8.54, format="%.4f")
        company_input = ui.input("Firma", placeholder="z.B. Müller Bau AG")
        branch_select = ui.select(
            label="Branche",
            options=list(BRANCH_PRESETS.keys()),
            value="Bau",
        )

        def add_location():
            session = get_session()
            loc = Location(
                name=name_input.value,
                latitude=lat_input.value,
                longitude=lon_input.value,
                company=company_input.value,
                branch=branch_select.value,
            )
            # Vordefinierte Thresholds hinzufügen
            for preset in BRANCH_PRESETS.get(branch_select.value, []):
                t = WeatherThreshold(
                    parameter=preset["parameter"],
                    operator=preset["operator"],
                    value=preset["value"],
                    label=preset["label"],
                    severity=preset["severity"],
                )
                loc.thresholds.append(t)

            session.add(loc)
            session.commit()
            session.close()
            ui.notify(f"Standort '{name_input.value}' hinzugefügt!", type="positive")
            name_input.value = ""
            company_input.value = ""
            refresh_locations()

        ui.button("Standort hinzufügen", on_click=add_location, icon="add_location").classes("mt-2")

    refresh_locations()


def _build_location_card(location: Location, analyzer: RiskAnalyzer, refresh_fn, refresh_alerts_fn):
    """Karte für einen einzelnen Standort."""
    with ui.card().classes("w-full"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column():
                ui.label(location.name).classes("font-bold text-lg")
                ui.label(f"{location.company} | {location.branch}").classes("text-sm text-gray-600")
                ui.label(f"{location.latitude:.4f}°N, {location.longitude:.4f}°E").classes("text-xs text-gray-400")

            with ui.row():
                async def run_analysis(loc=location):
                    ui.notify(f"Analyse läuft für {loc.name}...", type="info")
                    try:
                        session = get_session()
                        # Location mit Thresholds neu laden
                        db_loc = session.query(Location).get(loc.id)
                        alerts = analyzer.analyze(db_loc)
                        # Alte Alerts löschen, neue speichern
                        session.query(Alert).filter(Alert.location_id == loc.id).delete()
                        for alert in alerts:
                            session.add(alert)
                        session.commit()
                        session.close()
                        ui.notify(f"{len(alerts)} Alerts für {loc.name}", type="positive" if not alerts else "warning")
                        refresh_alerts_fn()
                    except Exception as e:
                        ui.notify(f"Fehler: {e}", type="negative")

                ui.button(icon="refresh", on_click=run_analysis).tooltip("Wetter prüfen")

                def delete_location(loc=location):
                    session = get_session()
                    db_loc = session.query(Location).get(loc.id)
                    if db_loc:
                        session.delete(db_loc)
                        session.commit()
                    session.close()
                    ui.notify(f"'{loc.name}' gelöscht", type="info")
                    refresh_fn()
                    refresh_alerts_fn()

                ui.button(icon="delete", on_click=delete_location, color="red").tooltip("Löschen")

        # Thresholds anzeigen
        if location.thresholds:
            with ui.expansion("Grenzwerte", icon="tune").classes("w-full"):
                for t in location.thresholds:
                    color = SEVERITY_COLORS.get(t.severity, "#666")
                    ui.label(f"{t.label}: {t.parameter} {t.operator} {t.value}").style(f"color: {color}")


def _build_alert_panel():
    """Panel das alle aktuellen Alerts anzeigt."""
    ui.label("Aktuelle Warnungen").classes("text-xl font-bold mb-2")

    alert_container = ui.column().classes("w-full gap-2")

    def refresh_alerts():
        alert_container.clear()
        session = get_session()
        alerts = session.query(Alert).join(Location).order_by(Alert.severity.desc(), Alert.forecast_time).all()

        with alert_container:
            if not alerts:
                ui.label("Keine Warnungen — alles im grünen Bereich!").classes("text-green-600 italic text-lg")
            for alert in alerts:
                _build_alert_card(alert)
        session.close()

    _state["refresh_alerts"] = refresh_alerts
    refresh_alerts()


def _build_alert_card(alert: Alert):
    """Einzelne Alert-Karte."""
    color = SEVERITY_COLORS.get(alert.severity, "#666")
    bg_color = {"critical": "#ffebee", "warning": "#fff3e0", "info": "#e3f2fd"}.get(alert.severity, "#f5f5f5")

    with ui.card().classes("w-full").style(f"border-left: 4px solid {color}; background: {bg_color}"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column():
                ui.label(alert.threshold_label).classes("font-bold").style(f"color: {color}")
                loc_name = alert.location.name if alert.location else "Unbekannt"
                ui.label(f"Standort: {loc_name}").classes("text-sm")
                param_label = RiskAnalyzer.PARAMETER_LABELS.get(alert.parameter, alert.parameter)
                ui.label(f"{param_label}: {alert.actual_value} (Grenzwert: {alert.threshold_value})").classes("text-sm text-gray-600")

            ui.label(alert.forecast_time.strftime("%d.%m. %H:%M")).classes("text-sm font-mono")

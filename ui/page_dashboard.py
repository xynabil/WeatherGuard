"""Seite 3: Dashboard – Standorte verwalten & Live-Warnungen (URL '/dashboard')."""

import asyncio

import requests
from nicegui import ui, app

from services.risk_analyzer import RiskAnalyzer
from ui.components import (
    BG_MAIN, BG_CARD, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT_BLUE,
    SEVERITY_COLORS, SEVERITY_BG,
    _is_logged_in, _setup_dark_mode, _render_sidebar,
)
from ui.controllers import BRANCH_PRESETS
from ui.dashboard_refresh import DashboardRefresh


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
    refresh_callbacks = {}

    with ui.column().classes("grow").style(
        f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
        f"padding: 24px 32px; gap: 20px;"
    ):
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

        with ui.row().classes("w-full").style("gap: 24px; align-items: flex-start;"):
            locations_column = ui.column().style("width: 360px; flex-shrink: 0; gap: 12px;")
            alerts_column    = ui.column().classes("grow").style("gap: 12px;")

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

        refresh_callbacks["refresh_locations"] = refresh_locations
        refresh_callbacks["refresh_alerts"]    = refresh_alerts
        refresh_locations()
        refresh_alerts()

        dashboard_refresh = DashboardRefresh(
            refresh_label=refresh_info,
            alert_controller=alert,
            location_controller=location,
            refresh_callbacks=refresh_callbacks,
            user_id=user_id,
        )
        dashboard_refresh.start()


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

        with ui.row().classes("w-full no-wrap").style("gap: 12px;"):
            name_input    = ui.input("Name *", placeholder="z.B. Baustelle Zürich HB").classes("grow")
            company_input = ui.input("Firma", value=app.storage.user.get("company", "")).classes("grow")

        branch_select = ui.select(
            label="Branche (bestimmt Grenzwert-Vorschläge)",
            options=list(BRANCH_PRESETS.keys()),
            value="Bau",
        ).classes("w-full")

        ui.label("Standort auf Karte wählen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )

        marker_state          = {"marker": None, "lat": None, "lon": None}
        search_results_container = ui.column().classes("w-full").style("gap: 4px;")
        coords_label_holder   = {"label": None}

        with ui.row().classes("w-full no-wrap items-end").style("gap: 8px;"):
            search_input = ui.input(
                "Ort suchen", placeholder="z.B. Zürich HB, Bahnhof Olten …"
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

        with ui.element("div").style("height: 260px; width: 100%;"):
            leaflet_map = ui.leaflet(center=(46.8, 8.2), zoom=8).style("height: 260px;")

        coords_label = ui.label("Klicke auf die Karte oder wähle ein Suchergebnis.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )
        coords_label_holder["label"] = coords_label

        def on_map_click(event):
            lat = event.args["latlng"]["lat"]
            lon = event.args["latlng"]["lng"]
            marker_state["lat"] = lat
            marker_state["lon"] = lon

            if marker_state["marker"] is None:
                marker_state["marker"] = leaflet_map.marker(latlng=(lat, lon))
            else:
                marker_state["marker"].move(lat, lon)

            coords_label.set_text(f"📍 {lat:.4f}°N, {lon:.4f}°E  (manuell gesetzt)")
            search_results_container.clear()

        leaflet_map.on("map-click", on_map_click)

        ui.label("Grenzwerte anpassen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )
        ui.label("Vorschläge je nach Branche — Werte sind anpassbar.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )

        threshold_container = ui.column().classes("w-full").style("gap: 8px;")
        threshold_inputs    = []

        def build_threshold_inputs(branch):
            """Zeichnet die Grenzwert-Zeilen neu (z.B. wenn Branche geändert wurde)."""
            threshold_container.clear()
            threshold_inputs.clear()
            with threshold_container:
                for preset in BRANCH_PRESETS.get(branch, []):
                    row_data = _render_threshold_input_row(preset)
                    threshold_inputs.append(row_data)

        build_threshold_inputs(branch_select.value)
        branch_select.on_value_change(lambda event: build_threshold_inputs(event.value))

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

                threshold_list = [
                    {"preset": row["preset"], "value": row["value_input"].value}
                    for row in threshold_inputs
                ]
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
    await asyncio.sleep(0.5)
    leaflet_map.run_map_method("invalidateSize")


def _render_threshold_input_row(preset):
    """Eine Zeile im 'Grenzwerte anpassen'-Bereich des Dialogs."""
    color = SEVERITY_COLORS.get(preset["severity"], "#888")

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
        value_input = ui.number(value=preset["value"]).style("width: 90px; flex-shrink: 0;")

    return {"preset": preset, "value_input": value_input}


def _search_location_and_show(search_term, results_container, leaflet_map, marker_state, coords_label):
    """Sucht einen Ort via OpenStreetMap und zeigt die Ergebnisse an."""
    search_term = search_term.strip()
    if not search_term:
        return

    results_container.clear()

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

    if not results:
        with results_container:
            ui.label("Keine Ergebnisse gefunden.").style(
                f"color: {TEXT_MUTED}; font-size: 13px; padding: 8px 12px;"
            )
        return

    with results_container:
        ui.label("Ergebnisse — klicke auf den richtigen Ort:").style(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 2px 4px;"
        )
        for item in results:
            _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label)


def _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label):
    """Eine einzelne Zeile mit einem Suchergebnis."""
    lat          = float(item["lat"])
    lon          = float(item["lon"])
    display_name = item.get("display_name", "")
    parts        = [p.strip() for p in display_name.split(",")]
    short_name   = ", ".join(parts[:2])

    def on_select():
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
            _render_location_card_buttons(location, alert_controller, refresh_callbacks)

        weather_row = ui.row().style("gap: 16px; flex-wrap: wrap; min-height: 32px;")

        def load_weather():
            _fill_weather_row(weather_row, location, alert_controller)

        with weather_row:
            ui.spinner(size="xs")
        ui.timer(0.1, load_weather, once=True)

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
        def run_analysis():
            ui.notify(f"Analyse läuft für {location.name}…", type="info")
            try:
                new_alerts = alert_controller.run_analysis(location.id)
                if new_alerts:
                    ui.notify(f"⚠ {len(new_alerts)} Warnung(en) für {location.name}", type="warning")
                else:
                    ui.notify(f"✓ Keine Warnungen für {location.name}", type="positive")
                refresh_callbacks["refresh_alerts"]()
            except Exception as error:
                ui.notify(f"Fehler: {error}", type="negative")

        ui.button(icon="refresh", on_click=run_analysis).props("flat size=sm").tooltip(
            "Wetter prüfen & Alerts aktualisieren"
        )

        def delete_location():
            try:
                alert_controller.location_dao.delete(location.id)
            except Exception as error:
                ui.notify(f"Fehler: {error}", type="negative")
                return
            ui.notify(f"'{location.name}' gelöscht", type="info")
            refresh_callbacks["refresh_locations"]()
            refresh_callbacks["refresh_alerts"]()

        ui.button(icon="delete", on_click=delete_location, color="red").props("flat size=sm").tooltip(
            "Standort löschen"
        )


def _fill_weather_row(weather_row, location, alert_controller):
    """Holt die Wetterdaten und füllt die Wetter-Zeile auf der Standort-Karte."""
    weather_row.clear()
    with weather_row:
        ui.spinner(size="xs")

    try:
        forecast = alert_controller.get_current_weather(location.latitude, location.longitude)
        days     = forecast.get("days", [])
        weather_row.clear()

        if not days or not days[0].get("hours"):
            with weather_row:
                ui.label("Keine Wetterdaten").style(f"color: {TEXT_MUTED}; font-size: 12px;")
            return

        first_hour = days[0]["hours"][0]
        with weather_row:
            _render_weather_stat("🌡", f"{first_hour.get('TTT_C', '-')}°C",        "Temp")
            _render_weather_stat("💨", f"{first_hour.get('FX_KMH', '-')} km/h",    "Wind")
            _render_weather_stat("🌧", f"{first_hour.get('RRR_MM', '-')} mm",      "Regen")
            _render_weather_stat("❄",  f"{first_hour.get('FRESHSNOW_CM', '-')} cm","Schnee")
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
    color          = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    bg_color       = SEVERITY_BG.get(alert.severity, BG_CARD)
    location_name  = alert.location.name if alert.location else "Unbekannt"
    parameter_label = RiskAnalyzer.PARAMETER_LABELS.get(alert.parameter, alert.parameter)

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
        ui.label(f"Standort: {location_name}").style(
            f"color: {TEXT_PRIMARY}; font-size: 13px;"
        )
        ui.label(
            f"{parameter_label}: {alert.actual_value} (Grenzwert: {alert.threshold_value})"
        ).style(f"color: {TEXT_MUTED}; font-size: 13px;")

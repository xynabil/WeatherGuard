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
    """Der Haupt-Bereich des Dashboards (alles ausser Sidebar).

    Standorte werden nebeneinander angezeigt; unter jeder Standort-Karte
    stehen die zugehörigen Warnungen.
    """
    # Dict für Callbacks: innere Funktionen können damit die UI neu laden
    refresh_callbacks = {}

    with ui.column().classes("grow").style(
        f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
        f"padding: 24px 32px; gap: 20px;"
    ):
        # Header: Titel links, Button "Neuer Standort" rechts
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            with ui.column().style("gap: 4px;"):
                with ui.row().classes("items-baseline no-wrap").style("gap: 10px;"):
                    ui.label("Dashboard").style(
                        f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                    )
                    # Countdown-Label für den Auto-Refresh (wird von DashboardRefresh befüllt)
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

        # Container für die Standort-Spalten (eine Spalte pro Standort, nebeneinander)
        columns_container = ui.row().classes("w-full").style(
            "gap: 16px; flex-wrap: wrap; align-items: stretch;"
        )

        def refresh_dashboard():
            """Baut das Dashboard neu auf: pro Standort eine Spalte (Karte oben, Alerts unten)."""
            columns_container.clear()

            # Alle Standorte und Alerts laden
            user_locations = location.list_locations(user_id=user_id)
            user_alerts = alert.list_current_alerts(user_id=user_id)

            # Alerts pro Standort-ID gruppieren
            alerts_by_location = {}
            for a in user_alerts:
                if a.location_id not in alerts_by_location:
                    alerts_by_location[a.location_id] = []
                alerts_by_location[a.location_id].append(a)

            with columns_container:
                # Leerer Zustand: noch keine Standorte
                if not user_locations:
                    ui.label("Noch keine Standorte — klicke auf «Neuer Standort».").style(
                        f"color: {TEXT_MUTED}; font-style: italic;"
                    )
                    return

                # Pro Standort eine vertikale Spalte
                for loc in user_locations:
                    with ui.column().style("width: 300px; flex-shrink: 0; gap: 10px; align-items: stretch;"):
                        # Oben: Standort-Karte
                        _render_location_card(loc, location, alert, refresh_callbacks)

                        # Unten: Alerts dieses Standorts
                        location_alerts = alerts_by_location.get(loc.id, [])
                        if location_alerts:
                            for a in location_alerts:
                                _render_alert_card(a)
                        else:
                            ui.label("Keine Warnungen ✓").style(
                                "color: #4ec9a8; font-style: italic; font-size: 13px; "
                                "padding: 4px 4px;"
                            )

        # Beide alten Callbacks lösen jetzt einen kompletten Neuaufbau aus
        refresh_callbacks["refresh_locations"] = refresh_dashboard
        refresh_callbacks["refresh_alerts"]    = refresh_dashboard
        refresh_dashboard()

        # Auto-Refresh starten (aktualisiert alle 3 Minuten automatisch)
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

        # Name und Firma nebeneinander
        with ui.row().classes("w-full no-wrap").style("gap: 12px;"):
            name_input    = ui.input("Name *", placeholder="z.B. Baustelle Zürich HB").classes("grow")
            company_input = ui.input("Firma", value=app.storage.user.get("company", "")).classes("grow")

        # Branche bestimmt die Grenzwert-Vorschläge
        branch_select = ui.select(
            label="Branche (bestimmt Grenzwert-Vorschläge)",
            options=list(BRANCH_PRESETS.keys()),
            value="Bau",
        ).classes("w-full")

        ui.label("Standort auf Karte wählen").style(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; margin-top: 4px;"
        )

        # marker_state merkt sich den zuletzt gesetzten Kartenmarker
        marker_state             = {"marker": None, "lat": None, "lon": None}
       
        coords_label_holder      = {"label": None}

        # Suchfeld mit Enter-Taste und Suchen-Button
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
        search_results_container = ui.column().classes("w-full").style("gap: 4px;")        # Interaktive Karte (OpenStreetMap via Leaflet)
        
        with ui.element("div").style("height: 260px; width: 100%;"):
            leaflet_map = ui.leaflet(center=(46.8, 8.2), zoom=8).style("height: 260px;")

        coords_label = ui.label("Klicke auf die Karte oder wähle ein Suchergebnis.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )
        coords_label_holder["label"] = coords_label

        def on_map_click(event):
            # Koordinaten aus dem Klick-Event lesen und Marker setzen/verschieben
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
        threshold_inputs    = []  # Liste der Eingabefelder (Preset + Wert)

        def build_threshold_inputs(branch):
            """Zeichnet die Grenzwert-Zeilen neu wenn die Branche geändert wird."""
            threshold_container.clear()
            threshold_inputs.clear()
            with threshold_container:
                for preset in BRANCH_PRESETS.get(branch, []):
                    row_data = _render_threshold_input_row(preset)
                    threshold_inputs.append(row_data)

        # Initial die Grenzwerte für die Standard-Branche zeichnen
        build_threshold_inputs(branch_select.value)
        branch_select.on_value_change(lambda event: build_threshold_inputs(event.value))

        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

        with ui.row().classes("w-full justify-end").style("gap: 8px; margin-top: 4px;"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save():
                error_label.set_text("")
                # Pflichtfelder prüfen
                if not name_input.value.strip():
                    error_label.set_text("Bitte einen Namen eingeben.")
                    return
                if marker_state["lat"] is None:
                    error_label.set_text("Bitte einen Punkt auf der Karte wählen.")
                    return

                # Grenzwert-Liste für den Controller zusammenbauen
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
    # Kurz warten damit der Dialog geöffnet ist, dann Karte neu rendern
    await asyncio.sleep(0.5)
    leaflet_map.run_map_method("invalidateSize")


def _render_threshold_input_row(preset):
    """Eine Zeile im 'Grenzwerte anpassen'-Bereich: Farbe, Label, Parameter und Eingabefeld."""
    color = SEVERITY_COLORS.get(preset["severity"], "#888")

    with ui.row().classes("w-full items-center no-wrap").style(
        f"background: {BG_INPUT}; border-radius: 8px; padding: 10px 14px; gap: 12px;"
    ):
        # Farbpunkt zeigt den Schweregrad (rot = critical, gelb = warning)
        ui.element("div").style(
            f"width: 10px; height: 10px; border-radius: 50%; "
            f"background: {color}; flex-shrink: 0;"
        )
        # Name des Grenzwerts (z.B. "Frost (Betonarbeiten)")
        ui.label(preset["label"]).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; flex-grow: 1;"
        )
        # Parameter und Operator (z.B. "TTT_C <")
        ui.label(f"{preset['parameter']} {preset['operator']}").style(
            f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace; flex-shrink: 0;"
        )
        # Wert-Eingabe: vorausgefüllt, aber vom User anpassbar
        value_input = ui.number(value=preset["value"]).style("width: 90px; flex-shrink: 0;")

    return {"preset": preset, "value_input": value_input}


def _search_location_and_show(search_term, results_container, leaflet_map, marker_state, coords_label):
    """Sucht einen Ort via OpenStreetMap Nominatim und zeigt die Treffer an."""
    search_term = search_term.strip()
    if not search_term:
        return

    results_container.clear()

    # API-Aufruf an OpenStreetMap
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

    # Gefundene Orte als klickbare Zeilen anzeigen
    with results_container:
        ui.label("Ergebnisse — klicke auf den richtigen Ort:").style(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 2px 4px;"
        )
        for item in results:
            _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label)


def _render_search_result_row(item, results_container, leaflet_map, marker_state, coords_label):
    """Eine einzelne Zeile mit einem Suchergebnis (klickbar → Marker setzen)."""
    lat          = float(item["lat"])
    lon          = float(item["lon"])
    display_name = item.get("display_name", "")
    # Nur die ersten zwei Teile des langen Ortsnamens anzeigen
    parts      = [p.strip() for p in display_name.split(",")]
    short_name = ", ".join(parts[:2])

    def on_select():
        # Karte auf den Ort zentrieren und Marker setzen/verschieben
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


def _render_location_card(location, location_controller, alert_controller, refresh_callbacks):
    """Eine Karte mit Standort-Infos, Wetter-Vorschau und Grenzwerten."""
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 16px; gap: 10px;"
    ):
        # Obere Zeile: Info links, Buttons rechts
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
            _render_location_card_buttons(location, location_controller, alert_controller, refresh_callbacks)

        # Wetter-Zeile: wird asynchron nachgeladen (erst Spinner, dann Werte)
        weather_row = ui.row().style("gap: 6px; flex-wrap: wrap; min-height: 32px;")

        def load_weather():
            _fill_weather_row(weather_row, location, alert_controller)

        with weather_row:
            ui.spinner(size="xs")
        ui.timer(0.1, load_weather, once=True)

        # Grenzwerte ausklappbar anzeigen
        if location.thresholds:
            with ui.expansion("Grenzwerte", icon="tune").classes("w-full"):
                for threshold in location.thresholds:
                    color = SEVERITY_COLORS.get(threshold.severity, TEXT_MUTED)
                    ui.label(
                        f"{threshold.label}: {threshold.parameter} {threshold.operator} {threshold.value}"
                    ).style(f"color: {color}; font-size: 13px;")


def _render_location_card_buttons(location, location_controller, alert_controller, refresh_callbacks):
    """Die Refresh- und Lösch-Buttons in der Standort-Karte."""
    with ui.row().style("gap: 4px;"):

        def run_analysis():
            # Wetter-Analyse für diesen Standort starten
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

        ui.button(
            icon="tune",
            on_click=lambda: _open_edit_thresholds_dialog(location, location_controller, refresh_callbacks),
        ).props("flat size=sm").tooltip("Grenzwerte anpassen")

        def delete_location():
            # Standort (inkl. Grenzwerte und Alerts) aus der DB löschen
            try:
                location_controller.delete_location(location.id)
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
    """Holt Wetterdaten vom Controller und füllt die Wetter-Zeile in der Karte."""
    weather_row.clear()
    with weather_row:
        ui.spinner(size="xs")

    try:
        forecast   = alert_controller.get_current_weather(location.latitude, location.longitude)
        days       = forecast.get("days", [])
        weather_row.clear()

        if not days or not days[0].get("hours"):
            with weather_row:
                ui.label("Keine Wetterdaten").style(f"color: {TEXT_MUTED}; font-size: 12px;")
            return

        # Erste Stunde des ersten Tages anzeigen
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
    """Ein kleines Wetter-Element bestehend aus Icon, Wert und Einheits-Label."""
    with ui.column().style("align-items: center; gap: 1px;"):
        ui.label(f"{icon} {value}").style(
            f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 600;"
        )
        ui.label(label).style(f"color: {TEXT_MUTED}; font-size: 10px;")


def _render_alert_card(alert):
    """Eine Alert-Karte im Dashboard (rechte Spalte) mit Schweregrad-Farbe."""
    color           = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    bg_color        = SEVERITY_BG.get(alert.severity, BG_CARD)
    location_name   = alert.location.name if alert.location else "Unbekannt"
    # Lesbaren Parameter-Namen aus dem RiskAnalyzer holen (z.B. "TTT_C" → "Temperatur")
    parameter_label = RiskAnalyzer.PARAMETER_LABELS.get(alert.parameter, alert.parameter)

    with ui.column().style(
        f"background: {bg_color}; border: 1px solid {color}; "
        f"border-left: 4px solid {color}; border-radius: 10px; "
        f"padding: 14px 16px; gap: 4px;"
    ):
        # Obere Zeile: Warnung-Label links, Zeitpunkt rechts
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
        # Gemessener Wert und der Grenzwert der überschritten wurde
        ui.label(
            f"{parameter_label}: {alert.actual_value} (Grenzwert: {alert.threshold_value})"
        ).style(f"color: {TEXT_MUTED}; font-size: 13px;")

def _open_edit_thresholds_dialog(location, location_controller, refresh_callbacks):
    """Dialog zum Anpassen der Grenzwert-Schwellen eines bestehenden Standorts."""
    if not location.thresholds:
        ui.notify("Keine Grenzwerte vorhanden.", type="warning")
        return

    dialog = ui.dialog().props("persistent")

    with dialog, ui.card().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 12px; padding: 28px; gap: 16px; "
        f"width: 520px; max-width: 95vw;"
    ):
        ui.label(f"Grenzwerte bearbeiten: {location.name}").style(
            f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 600;"
        )
        ui.label("Passe die Schwellenwerte an. Label und Operator bleiben unverändert.").style(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )

        # Pro Grenzwert eine Zeile mit Eingabefeld
        threshold_inputs = []  # Liste von (threshold_id, ui.number-Element)

        for threshold in location.thresholds:
            color = SEVERITY_COLORS.get(threshold.severity, TEXT_MUTED)

            with ui.row().classes("w-full items-center no-wrap").style(
                f"background: {BG_INPUT}; border-radius: 8px; padding: 10px 14px; gap: 12px;"
            ):
                # Farb-Punkt (zeigt Schweregrad)
                ui.element("div").style(
                    f"width: 10px; height: 10px; border-radius: 50%; "
                    f"background: {color}; flex-shrink: 0;"
                )
                # Label (nicht editierbar)
                ui.label(threshold.label).style(
                    f"color: {TEXT_PRIMARY}; font-size: 13px; flex-grow: 1;"
                )
                # Parameter + Operator (nicht editierbar)
                ui.label(f"{threshold.parameter} {threshold.operator}").style(
                    f"color: {TEXT_MUTED}; font-size: 12px; font-family: monospace; flex-shrink: 0;"
                )
                # Wert (editierbar)
                value_input = ui.number(value=threshold.value).style(
                    "width: 90px; flex-shrink: 0;"
                )
                threshold_inputs.append((threshold.id, value_input))

        # Buttons unten
        with ui.row().classes("w-full justify-end").style("gap: 8px; margin-top: 8px;"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save():
                # Werte sammeln und an Controller weitergeben
                new_values = {}
                for threshold_id, value_input in threshold_inputs:
                    new_values[threshold_id] = value_input.value
                location_controller.update_thresholds(location.id, new_values)
                dialog.close()
                ui.notify(
                    f"✓ Grenzwerte für '{location.name}' aktualisiert.",
                    type="positive",
                )
                refresh_callbacks["refresh_locations"]()

            ui.button("Speichern", icon="save", on_click=save).style(
                f"background: {ACCENT_BLUE}; color: white;"
            )

    dialog.open()
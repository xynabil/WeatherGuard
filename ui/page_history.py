"""Seite 2: Alert History – KPIs, Charts, Recent Alerts (URL '/app')."""

from datetime import datetime

from nicegui import ui, app

from ui.components import (
    BG_MAIN, BG_CARD, BG_CARD_SOFT, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT_BLUE,
    SEVERITY_STYLES, TIME_RANGES,
    _is_logged_in, _setup_dark_mode, _render_sidebar, _render_user_chip,
)


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
            # User-Avatar oben rechts
            _render_user_chip()

            with ui.column().style("gap: 4px;"):
                ui.label("Alert History").style(
                    f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                )
                ui.label("Alle Standorte").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )

            # KPI-Karten: Total, Danger, Warning, Heute
            kpi_container = ui.row().classes("w-full no-wrap").style("gap: 16px;")

            def refresh_kpis(since=None):
                kpi_container.clear()
                with kpi_container:
                    _render_kpi_row(history.get_kpis(user_id=user_id, since=since))

            refresh_kpis()

            # Zwei Charts nebeneinander: Alerts pro Tag + Alerts pro Typ
            charts_container = ui.row().classes("w-full no-wrap").style("gap: 16px;")

            def refresh_charts(since=None):
                charts_container.clear()
                with charts_container:
                    _render_alerts_per_day_chart(
                        history.get_alerts_per_day(user_id=user_id, since=since)
                    )
                    _render_alerts_by_type_chart(
                        history.get_alerts_by_type(user_id=user_id, since=since)
                    )

            refresh_charts()

            def refresh_all(since=None):
                refresh_kpis(since)
                refresh_charts(since)

            # Gefilterte Alert-Liste mit Zeitraum-Dropdown und Typ-Chips
            _render_recent_alerts_section(history, user_id, on_time_change=refresh_all)


def _render_kpi_row(kpis):
    """Die 4 KPI-Karten oben auf der Alert-History-Seite."""
    # (Label, Wert, Farbe) pro Karte
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



def _render_alerts_per_day_chart(data):
    """Balken-Diagramm: Alerts pro Tag (letzte 7 Tage), heute rot markiert."""
    with ui.column().classes("grow").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        ui.label("Alerts per day").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        # Achsenbeschriftung und Balkendaten aufbereiten
        x_axis_labels = [day[0] for day in data]
        bar_data = []
        for day_name, count, is_today in data:
            # Heutiger Tag wird rot eingefärbt, alle anderen blau
            color = "#e05659" if is_today else "#6b9dd4"
            bar_data.append({"value": count, "itemStyle": {"color": color}})

        ui.echart({
            "grid": {"left": 10, "right": 10, "top": 10, "bottom": 30, "containLabel": True},
            "xAxis": {
                "type": "category",
                "data": x_axis_labels,
                "axisLine":  {"lineStyle": {"color": BORDER}},
                "axisLabel": {"color": TEXT_MUTED, "fontSize": 12},
                "axisTick":  {"show": False},
            },
            "yAxis": {
                "type": "value",
                "show": True,
                "minInterval": 1,
                "axisLabel": {"color": TEXT_MUTED, "fontSize": 11},
                "splitLine": {"lineStyle": {"color": BORDER, "type": "dashed"}},
            },
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

        # Grösste Anzahl für die Skalierung der Balken
        max_count = max(item[1] for item in data)

        with ui.column().classes("w-full").style("gap: 12px; padding: 8px 0;"):
            for name, count, color in data:
                with ui.row().classes("w-full items-center no-wrap").style("gap: 12px;"):
                    ui.label(name).style(f"color: {TEXT_PRIMARY}; font-size: 13px; width: 60px;")
                    # Grauer Hintergrund-Balken mit farbigem Füll-Balken
                    with ui.element("div").style(
                        "flex-grow: 1; background: #1a1a1a; height: 16px; "
                        "border-radius: 4px; overflow: hidden;"
                    ):
                        bar_width_percent = (count / max_count) * 85
                        ui.element("div").style(
                            f"background: {color}; height: 100%; "
                            f"width: {bar_width_percent}%; border-radius: 4px;"
                        )
                    ui.label(str(count)).style(
                        f"color: {TEXT_PRIMARY}; font-size: 13px; width: 24px; text-align: right;"
                    )


def _render_recent_alerts_section(history, user_id, on_time_change=None):
    """Der 'Recent alerts'-Abschnitt mit Zeitraum-Dropdown, Filter-Chips und Alert-Liste."""
    # Dict statt Variable, damit innere Funktionen die Werte ändern können
    filter_state = {"active": "All", "time_range": "All"}

    with ui.column().classes("w-full").style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 20px; gap: 16px;"
    ):
        # Titelzeile mit Zeitraum-Dropdown rechts
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label("Recent alerts").style(
                f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
            )
            # Zeitraum-Auswahl: All, Last day, Last week, Last month, Last year
            time_select = ui.select(
                options=list(TIME_RANGES.keys()),
                value="All",
            ).style(f"color: {TEXT_PRIMARY}; font-size: 13px; min-width: 120px;")

        chips_row         = ui.row().classes("no-wrap").style("gap: 8px;")
        alert_list_column = ui.column().classes("w-full").style("gap: 10px; margin-top: 4px;")

        def refresh_alert_list():
            """Alert-Liste neu zeichnen mit aktivem Typ-Filter und Zeitraum."""
            alert_list_column.clear()

            # Startzeitpunkt aus dem gewählten Zeitraum berechnen
            delta = TIME_RANGES[filter_state["time_range"]]
            since = datetime.now() - delta if delta else None

            with alert_list_column:
                filtered_alerts = history.get_recent_alerts(
                    filter_state["active"],
                    user_id=user_id,
                    since=since,
                )
                if not filtered_alerts:
                    # Meldung je nach aktivem Filter anpassen
                    active_type  = filter_state["active"]
                    active_range = filter_state["time_range"]
                    has_type     = active_type  != "All"
                    has_range    = active_range != "All"

                    if has_type and has_range:
                        msg = f"Keine {active_type}-Alerts im Zeitraum '{active_range}' gefunden."
                    elif has_range:
                        msg = f"Keine Alerts im Zeitraum '{active_range}' gefunden."
                    elif has_type:
                        msg = f"Keine {active_type}-Alerts vorhanden."
                    else:
                        msg = "Noch keine Alerts vorhanden."

                    ui.label(msg).style(f"color: {TEXT_MUTED}; font-style: italic;")

                for a in filtered_alerts:
                    _render_alert_history_row(a)

        def on_time_range_change(e):
            """Wird aufgerufen wenn ein anderer Zeitraum gewählt wird."""
            filter_state["time_range"] = e.value
            delta = TIME_RANGES[e.value]
            since = datetime.now() - delta if delta else None
            refresh_alert_list()
            if on_time_change:
                on_time_change(since)

        time_select.on_value_change(on_time_range_change)

        def set_filter(new_filter):
            """Wird aufgerufen wenn ein Typ-Chip geklickt wird."""
            filter_state["active"] = new_filter
            # Chips neu zeichnen damit der aktive Chip hervorgehoben wird
            chips_row.clear()
            _build_filter_chips(chips_row, new_filter, set_filter)
            refresh_alert_list()

        # Initial: Chips und Liste zeichnen
        _build_filter_chips(chips_row, filter_state["active"], set_filter)
        refresh_alert_list()


def _build_filter_chips(chips_row, active_chip, on_click_callback):
    """Zeichnet alle Filter-Chips (All, Frost, Wind, Rain, Snow)."""
    chip_labels = ["All", "Frost", "Wind", "Rain", "Snow"]
    with chips_row:
        for chip_label in chip_labels:
            # Lambda mit Default-Argument damit chip_label korrekt gebunden wird
            _render_filter_chip(
                chip_label,
                active=(chip_label == active_chip),
                on_click=lambda label=chip_label: on_click_callback(label),
            )


def _render_filter_chip(label, active, on_click):
    """Ein einzelner Filter-Chip: aktiv = blau, inaktiv = grau."""
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
    """Eine Zeile in der 'Recent alerts'-Liste mit Badge, Info und Zeitstempel."""
    severity_style = SEVERITY_STYLES.get(alert.severity, SEVERITY_STYLES["info"])
    location_name  = alert.location.name if alert.location else "Unbekannt"

    # Zeitstempel: "heute HH:MM", "gestern HH:MM" oder "DD.MM. HH:MM"
    now        = datetime.now()
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
        # Severity-Badge (danger / warning / info)
        ui.label(severity_style["label"]).style(
            f"background: {severity_style['bg']}; color: {severity_style['color']}; "
            f"padding: 3px 10px; border-radius: 4px; font-size: 12px; "
            f"font-weight: 500; min-width: 68px; text-align: center;"
        )
        # Info: Warnung-Label und Wert/Standort
        with ui.column().classes("grow").style("gap: 2px;"):
            ui.label(alert.threshold_label).style(
                f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;"
            )
            ui.label(
                f"{location_name} · {alert.actual_value} (Grenzwert: {alert.threshold_value})"
            ).style(f"color: {TEXT_MUTED}; font-size: 13px;")
        # Relativer Zeitstempel rechts
        ui.label(when_text).style(
            f"color: {TEXT_MUTED}; font-size: 12px; white-space: nowrap;"
        )

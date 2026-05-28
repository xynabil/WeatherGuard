"""Seite 4: Reports – Alerts-Tabelle mit Export (URL '/reports')."""

import json
from datetime import datetime

from fpdf import FPDF
from nicegui import ui, app

from ui.components import (
    BG_MAIN, BG_CARD, BG_CARD_SOFT, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT_BLUE,
    SEVERITY_COLORS, TIME_RANGES,
    _is_logged_in, _setup_dark_mode, _render_sidebar,
)


# Spalten der Reports-Tabelle: (Spaltenname, Breite)
REPORT_COLUMNS = [
    ("Datum",            "150px"),
    ("Standort",         "180px"),
    ("Warnung",          "210px"),
    ("Severity",         "90px"),
    ("Wert / Grenzwert", "160px"),
]


def _render_reports_page(alert):
    """Reports-Tabelle mit allen Alerts (URL '/reports')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    user_id    = app.storage.user.get("user_id") 
    all_alerts = alert.list_alerts(user_id=user_id) # Alle Alerts des eingeloggten Users abrufen

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Reports")

        with ui.column().classes("grow").style(
            f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
            f"padding: 24px 32px; gap: 20px;"
        ):
            # Titelzeile: Überschrift links, Export-Box rechts
            count_label = None
            with ui.row().classes("w-full items-start").style(
                "justify-content: space-between; gap: 16px;"
            ):
                with ui.column().style("gap: 4px;"):
                    ui.label("Reports").style(
                        f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
                    )
                    count_label = ui.label(f"{len(all_alerts)} Alerts insgesamt").style(
                        f"color: {TEXT_MUTED}; font-size: 14px;"
                    )

                # Export-Box oben rechts (gibt time_select zurück)
                time_select = _render_export_box(all_alerts)

            # Tabelle als refreshbare Spalte
            table_container = ui.column().classes("w-full").style(
                f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                f"border-radius: 10px; overflow: hidden;"
            )

            def refresh_table(range_key):
                filtered = _filter_alerts_by_range(all_alerts, range_key) 
                count_label.set_text(f"{len(filtered)} Alerts insgesamt") # Anzahl aktualisieren
                table_container.clear()
                with table_container:
                    _render_reports_table_header()
                    if not filtered:
                        ui.label("Keine Alerts vorhanden.").style(
                            f"color: {TEXT_MUTED}; font-style: italic; padding: 20px 16px;"
                        )
                    for index, a in enumerate(filtered):
                        _render_reports_table_row(a, is_alternate=(index % 2 == 1))

            time_select.on_value_change(lambda e: refresh_table(e.value))
            refresh_table("All") 


def _render_export_box(all_alerts):
    """Box oben rechts: Zeitraum wählen und als JSON oder PDF exportieren.

    Returns the time_select widget so the caller can bind a table refresh.
    """
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 10px; "
        f"padding: 16px 20px; gap: 12px; min-width: 260px;"
    ):
        ui.label("Export").style(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;"
        )

        # Zeitraum-Dropdown – gleiche Optionen wie in der Alert History
        time_select = ui.select(
            options=list(TIME_RANGES.keys()),
            value="All",
            label="Zeitraum",
        ).style(f"color: {TEXT_PRIMARY}; font-size: 13px;").classes("w-full")

        with ui.row().classes("items-center").style("gap: 8px;"):

            async def export_json(): 
                # Alerts filtern, in Dicts umwandeln und als .json herunterladen
                alerts  = _filter_alerts_by_range(all_alerts, time_select.value)
                data    = _alerts_to_dicts(alerts)
                content = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
                ui.download(content, "weatherguard_report.json")

            ui.button("JSON", on_click=export_json).props("no-caps").style(
                f"background: {ACCENT_BLUE}; color: white; font-size: 13px;"
            )

            async def export_pdf():
                # Alerts filtern, PDF erstellen und herunterladen
                alerts    = _filter_alerts_by_range(all_alerts, time_select.value)
                pdf_bytes = _build_pdf(alerts, time_select.value)
                ui.download(pdf_bytes, "weatherguard_report.pdf")

            ui.button("PDF", on_click=export_pdf).props("no-caps").style(
                f"background: #3a3a3a; color: {TEXT_PRIMARY}; font-size: 13px;"
            )

    return time_select


def _filter_alerts_by_range(alerts, range_key):
    """Gibt nur die Alerts zurück, die in den gewählten Zeitraum fallen."""
    delta = TIME_RANGES.get(range_key)
    if delta is None:
        # "All" → keine Filterung, alle Alerts zurückgeben
        return alerts
    since = datetime.now() - delta
    return [a for a in alerts if a.created_at >= since] # Nur Alerts, die neuer sind als "since"


def _alerts_to_dicts(alerts):
    """Wandelt Alert-Objekte in einfache Dicts um (für den JSON-Export)."""
    return [
        {
            "datum":     a.created_at.strftime("%d.%m.%Y %H:%M"),
            "standort":  a.location.name if a.location else "Unbekannt",
            "warnung":   a.threshold_label,
            "severity":  a.severity,
            "wert":      a.actual_value,
            "grenzwert": a.threshold_value,
            "parameter": a.parameter,
        }
        for a in alerts
    ]


def _build_pdf(alerts, range_label):
    """Erstellt ein PDF im A4-Querformat mit einer Tabelle aller Alerts."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    # Titel und Datum
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"WeatherGuard Report - {range_label}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Tabellen-Header mit grauem Hintergrund
    col_widths = [38, 46, 60, 24, 30, 30, 30]
    headers    = ["Datum", "Standort", "Warnung", "Severity", "Wert", "Grenzwert", "Parameter"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(80, 80, 80)
    pdf.set_text_color(230, 230, 230)
    for header, width in zip(headers, col_widths):
        pdf.cell(width, 7, header, border=1, fill=True)
    pdf.ln()

    # Tabellen-Zeilen mit abwechselndem Hintergrund (weiss / hellgrau)
    pdf.set_font("Helvetica", "", 8)
    for i, a in enumerate(alerts):
        location_name = a.location.name if a.location else "Unbekannt"
        row = [
            a.created_at.strftime("%d.%m.%Y %H:%M"),
            location_name, a.threshold_label, a.severity,
            str(a.actual_value), str(a.threshold_value), a.parameter,
        ]
        pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(30, 30, 30)
        for value, width in zip(row, col_widths):
            pdf.cell(width, 6, str(value), border=1, fill=True)
        pdf.ln()

    # Bytes zurückgeben – kein Dateisystem nötig
    return bytes(pdf.output())


def _render_reports_table_header():
    """Die Kopfzeile der Reports-Tabelle mit allen Spalten-Titeln."""
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
    color          = SEVERITY_COLORS.get(alert.severity, TEXT_MUTED)
    # "critical" wird in der Tabelle als "danger" angezeigt
    severity_label = "danger" if alert.severity == "critical" else alert.severity
    location_name  = alert.location.name if alert.location else "Unbekannt"
    # Jede zweite Zeile leicht heller (Streifen-Effekt für bessere Lesbarkeit)
    background     = BG_CARD_SOFT if is_alternate else BG_CARD

    with ui.row().classes("w-full no-wrap items-center").style(
        f"background: {background}; padding: 11px 16px; gap: 16px; "
        f"border-bottom: 1px solid {BORDER};"
    ):
        ui.label(alert.created_at.strftime("%d.%m.%Y %H:%M")).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; "
            f"font-family: monospace; width: 150px; flex-shrink: 0;"
        )
        ui.label(location_name).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 180px; flex-shrink: 0;"
        )
        ui.label(alert.threshold_label).style(
            f"color: {TEXT_PRIMARY}; font-size: 13px; width: 210px; flex-shrink: 0;"
        )
        ui.label(severity_label).style(
            f"color: {color}; font-size: 13px; font-weight: 500; "
            f"width: 90px; flex-shrink: 0;"
        )
        ui.label(f"{alert.actual_value} / {alert.threshold_value}").style(
            f"color: {TEXT_MUTED}; font-size: 13px; width: 160px; flex-shrink: 0;"
        )

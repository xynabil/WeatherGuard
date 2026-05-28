"""HistoryController - Statistiken (KPIs, Charts) für die Alert-History-Seite."""

from collections import defaultdict
from datetime import datetime, timedelta


# Wetter-Parameter zu Kategorie: für Filter-Chips in der Alert-History
PARAM_TO_TYPE = {
    "TTT_C":        "Frost",
    "FF_KMH":       "Wind",
    "FX_KMH":       "Wind",
    "RRR_MM":       "Rain",
    "FRESHSNOW_CM": "Snow",
}

# Farbe pro Kategorie für die "Alerts by type"-Anzeige
TYPE_COLORS = {
    "Wind":  "#4a9eff",
    "Frost": "#4ec9a8",
    "Rain":  "#b197fc",
    "Snow":  "#a8d8ea",
    "Other": "#888888",
}

DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


class HistoryController:
    """Berechnet Statistiken (KPIs, Charts) für die Alert-History-Seite."""

    def __init__(self, alert_dao):
        self.alert_dao = alert_dao

    def get_kpis(self, user_id=None, since=None):
        """Gibt die 4 KPI-Zahlen oben auf der Seite zurück.

        Returns: Dict mit Schlüsseln 'total', 'danger', 'warning', 'heute'.
        """
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        if since:
            all_alerts = [a for a in all_alerts if a.created_at >= since]
        today = datetime.now().date()

        total   = len(all_alerts)
        danger  = 0
        warning = 0
        heute   = 0

        for alert in all_alerts:
            if alert.severity == "critical":
                danger += 1
            elif alert.severity == "warning":
                warning += 1
            if alert.created_at.date() == today:
                heute += 1

        return {
            "total": total,
            "danger": danger,
            "warning": warning,
            "heute": heute,
        }

    def get_alerts_per_day(self, user_id=None, since=None):
        """Daten für das Balken-Diagramm: Alerts pro Tag (letzte 7 Tage).

        Returns: Liste von Tupeln (Tagesname, Anzahl, ist_heute).
        """
        today  = datetime.now().date()
        cutoff = since.date() if since else today - timedelta(days=6)
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        recent_alerts = [a for a in all_alerts if a.created_at.date() >= cutoff]

        # Alerts pro Datum zählen
        counts_by_date = defaultdict(int)
        for alert in recent_alerts:
            counts_by_date[alert.created_at.date()] += 1

        # Alle Tage vom cutoff bis heute bauen (ältester zuerst)
        result = []
        num_days = (today - cutoff).days + 1
        for days_ago in range(num_days - 1, -1, -1):
            day      = today - timedelta(days=days_ago)
            day_name = day.strftime("%d.%m") if num_days > 7 else DAY_NAMES[day.weekday()]
            count    = counts_by_date.get(day, 0)
            is_today = (day == today)
            result.append((day_name, count, is_today))

        return result

    def get_alerts_by_type(self, user_id=None, since=None):
        """Daten für das Kategorie-Diagramm.

        Returns: Liste von Tupeln (Typ-Name, Anzahl, Farbe), sortiert nach Anzahl.
        """
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        if since:
            all_alerts = [a for a in all_alerts if a.created_at >= since]

        # Pro Typ zählen (Frost, Wind, Rain, Snow, Other)
        counts_by_type = defaultdict(int)
        for alert in all_alerts:
            type_name = PARAM_TO_TYPE.get(alert.parameter, "Other")
            counts_by_type[type_name] += 1

        # Liste mit Farben bauen, nur Typen mit count > 0
        result = []
        for type_name in TYPE_COLORS:
            count = counts_by_type[type_name]
            if count > 0:
                color = TYPE_COLORS[type_name]
                result.append((type_name, count, color))

        # Nach Anzahl sortieren (grösste zuerst)
        result.sort(key=lambda item: item[1], reverse=True)
        return result

    def get_recent_alerts(self, filter_type="All", user_id=None, since=None):
        """Liste der Alerts, optional nach Zeitraum und Typ gefiltert."""
        # Alle Alerts laden damit die Zeitraum-Filter vollständig arbeiten
        alerts = self.alert_dao.list_all(limit=500, user_id=user_id)

        # Nach Zeitraum filtern: nur Alerts nach dem Startzeitpunkt behalten
        if since:
            alerts = [a for a in alerts if a.created_at >= since]

        # Nach Typ filtern (Frost, Wind, Rain, Snow)
        if filter_type != "All":
            alerts = [a for a in alerts if PARAM_TO_TYPE.get(a.parameter) == filter_type]

        return alerts #an UI zurückgeben.

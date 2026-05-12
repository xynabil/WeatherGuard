"""Controller-Klassen.

Die Controller sind die Brücke zwischen UI (Pages) und den DAOs/Services:
- Ein Klick im Browser → ruft eine Controller-Methode auf
- Der Controller benutzt die DAOs/Services und macht die eigentliche Arbeit
- Die UI bekommt das Ergebnis und zeigt es an

So muss die UI nichts über die Datenbank wissen, und die Datenbank-Klassen
müssen nichts über die UI wissen. Saubere Trennung.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from domain.models import User, Location, WeatherThreshold
from services.risk_analyzer import RiskAnalyzer


# =====================================================================
# Konstanten für die UI
# =====================================================================

# Branchen-Vorlagen: welche Grenzwerte schlagen wir je Branche vor?
# Wird im "Neuer Standort"-Dialog verwendet.
BRANCH_PRESETS = {
    "Bau": [
        {"parameter": "TTT_C",        "operator": "<", "value": 5.0,  "label": "Frost (Betonarbeiten)", "severity": "critical"},
        {"parameter": "FX_KMH",       "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)",  "severity": "critical"},
        {"parameter": "RRR_MM",       "operator": ">", "value": 10.0, "label": "Starkregen",            "severity": "warning"},
    ],
    "Event": [
        {"parameter": "FX_KMH",       "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)",  "severity": "critical"},
        {"parameter": "RRR_MM",       "operator": ">", "value": 5.0,  "label": "Regen (Outdoor)",       "severity": "warning"},
        {"parameter": "TTT_C",        "operator": "<", "value": 0.0,  "label": "Frost (Glätte)",        "severity": "warning"},
    ],
    "Lieferdienst": [
        {"parameter": "FRESHSNOW_CM", "operator": ">", "value": 5.0,  "label": "Schneefall",            "severity": "warning"},
        {"parameter": "FX_KMH",       "operator": ">", "value": 70.0, "label": "Orkan",                 "severity": "critical"},
        {"parameter": "TTT_C",        "operator": "<", "value": -5.0, "label": "Extremkälte",           "severity": "critical"},
    ],
}

# Zuordnung Parameter → Kategorie (für die Filter-Chips in der History)
PARAM_TO_TYPE = {
    "TTT_C":          "Frost",
    "FF_KMH":         "Wind",
    "FX_KMH":         "Wind",
    "RRR_MM":         "Rain",
    "FRESHSNOW_CM":   "Snow",
    "RELHUM_PERCENT": "Other",
}

# Farben für die Kategorien (im "Alerts by type"-Chart)
TYPE_COLORS = {
    "Wind":  "#4a9eff",
    "Frost": "#4ec9a8",
    "Rain":  "#b197fc",
    "Snow":  "#a8d8ea",
    "Other": "#888888",
}

# Tagesnamen für das "Alerts per day"-Chart
DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


# =====================================================================
# Controller-Klassen
# =====================================================================

class AuthController:
    """Kümmert sich um Login, Registrierung und Passwortänderung."""

    def __init__(self, user_dao):
        self.user_dao = user_dao

    def verify_login(self, username, password):
        """Prüft Login-Daten. Gibt den User zurück oder None bei falschem Passwort."""
        user = self.user_dao.get_by_username(username)
        if user is not None and user.check_password(password):
            return user
        return None

    def register(self, username, password, confirm_password, company):
        """Registriert einen neuen User. Gibt (erfolg, fehlermeldung) zurück."""
        # Validierung
        if not username.strip() or not password:
            return False, "Bitte Benutzername und Passwort eingeben."
        if len(password) < 6:
            return False, "Passwort muss mindestens 6 Zeichen haben."
        if password != confirm_password:
            return False, "Passwörter stimmen nicht überein."
        if self.user_dao.get_by_username(username.strip()) is not None:
            return False, "Benutzername ist bereits vergeben."

        # User anlegen und speichern
        new_user = User(
            username=username.strip(),
            password=password,
            company=company.strip(),
        )
        self.user_dao.add(new_user)
        return True, ""

    def change_password(self, username, current_password, new_password):
        """Ändert das Passwort eines Users. Gibt (erfolg, fehlermeldung) zurück."""
        if not current_password or not new_password:
            return False, "Bitte alle Felder ausfüllen."
        if len(new_password) < 6:
            return False, "Passwort muss mindestens 6 Zeichen haben."

        user = self.user_dao.get_by_username(username)
        if user is None or not user.check_password(current_password):
            return False, "Aktuelles Passwort ist falsch."

        self.user_dao.update_password(username, new_password)
        return True, ""


class LocationController:
    """Kümmert sich um Standorte (auflisten, hinzufügen, löschen)."""

    def __init__(self, location_dao):
        self.location_dao = location_dao

    def list_locations(self, user_id=None):
        """Gibt alle Locations zurück (nur die des Users, falls user_id gesetzt)."""
        return self.location_dao.list_all(user_id=user_id)

    def add_location(self, name, latitude, longitude, company, branch,
                     threshold_inputs, user_id=None):
        """Legt eine neue Location mit ihren Grenzwerten an.

        threshold_inputs ist eine Liste von Dicts mit "preset" und "value":
            [{"preset": {...}, "value": 5.0}, ...]
        """
        new_location = Location(
            name=name,
            latitude=latitude,
            longitude=longitude,
            user_id=user_id,
            branch=branch,
            company=company,
        )
        # Grenzwerte aus den UI-Eingaben übernehmen
        for t_input in threshold_inputs:
            preset = t_input["preset"]
            threshold = WeatherThreshold(
                parameter=preset["parameter"],
                operator=preset["operator"],
                value=t_input["value"],
                label=preset["label"],
                severity=preset["severity"],
            )
            new_location.thresholds.append(threshold)

        return self.location_dao.add(new_location)

    def delete_location(self, location_id):
        """Löscht eine Location (Grenzwerte und Alerts werden automatisch mitgelöscht)."""
        self.location_dao.delete(location_id)


class AlertController:
    """Kümmert sich um die Wetter-Analyse und das Auflisten von Alerts."""

    def __init__(self, location_dao, alert_dao, weather_client):
        self.location_dao = location_dao
        self.alert_dao = alert_dao
        self.weather_client = weather_client
        self.analyzer = RiskAnalyzer(weather_client)

    def run_analysis(self, location_id):
        """Wetter für eine Location holen, Grenzwerte prüfen, Alerts speichern."""
        location = self.location_dao.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Location {location_id} nicht gefunden.")

        new_alerts = self.analyzer.analyze(location)
        self.alert_dao.replace_for_location(location_id, new_alerts)
        return new_alerts

    def list_alerts(self, limit=200, user_id=None):
        """Gibt die letzten Alerts zurück."""
        return self.alert_dao.list_all(limit=limit, user_id=user_id)

    def get_current_weather(self, latitude, longitude):
        """Holt die aktuelle Wetter-Prognose für eine Position (Roh-Daten)."""
        return self.weather_client.get_forecast(latitude, longitude)


class HistoryController:
    """Berechnet Statistiken für die Alert-History-Seite (KPIs, Charts)."""

    def __init__(self, alert_dao):
        self.alert_dao = alert_dao

    def get_kpis(self, user_id=None):
        """Berechnet die vier KPI-Zahlen oben auf der History-Seite."""
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        today = datetime.now().date()

        total = len(all_alerts)
        danger = 0
        warning = 0
        heute = 0
        for a in all_alerts:
            if a.severity == "critical":
                danger += 1
            if a.severity == "warning":
                warning += 1
            if a.created_at.date() == today:
                heute += 1

        return {
            "total":   total,
            "danger":  danger,
            "warning": warning,
            "heute":   heute,
        }

    def get_alerts_per_day(self, user_id=None):
        """Zählt Alerts pro Tag der letzten 7 Tage.

        Gibt eine Liste mit Tupeln zurück: [("Mo", 3, False), ("Di", 5, False), ..., ("So", 2, True)]
        Der letzte Wert ist True, wenn dieser Tag heute ist.
        """
        cutoff = datetime.now() - timedelta(days=7)
        all_alerts = self.alert_dao.list_all(user_id=user_id)

        # Nur Alerts der letzten 7 Tage
        recent = []
        for a in all_alerts:
            if a.created_at >= cutoff:
                recent.append(a)

        # Pro Datum zählen
        counts = defaultdict(int)
        for a in recent:
            counts[a.created_at.date()] += 1

        # Liste der letzten 7 Tage aufbauen (heute zuletzt)
        today = datetime.now().date()
        result = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_name = DAY_NAMES[day.weekday()]
            count = counts.get(day, 0)
            is_today = (day == today)
            result.append((day_name, count, is_today))
        return result

    def get_alerts_by_type(self, user_id=None):
        """Zählt Alerts pro Kategorie (Wind, Frost, Rain, Snow).

        Gibt eine sortierte Liste zurück: [("Wind", 8, "#4a9eff"), ...]
        Sortiert absteigend nach Anzahl.
        """
        all_alerts = self.alert_dao.list_all(user_id=user_id)

        # Pro Kategorie zählen
        counts = defaultdict(int)
        for a in all_alerts:
            type_name = PARAM_TO_TYPE.get(a.parameter, "Other")
            counts[type_name] += 1

        # Nur Kategorien mit mindestens einem Alert, mit Farbe versehen
        result = []
        for type_name in TYPE_COLORS:
            if counts[type_name] > 0:
                color = TYPE_COLORS[type_name]
                result.append((type_name, counts[type_name], color))

        # Absteigend nach Anzahl sortieren
        result.sort(key=lambda item: -item[1])
        return result

    def get_recent_alerts(self, filter_type="All", user_id=None):
        """Gibt die letzten 50 Alerts zurück, optional gefiltert nach Kategorie."""
        alerts = self.alert_dao.list_all(limit=50, user_id=user_id)
        if filter_type == "All":
            return alerts

        # Nach Kategorie filtern
        filtered = []
        for a in alerts:
            if PARAM_TO_TYPE.get(a.parameter) == filter_type:
                filtered.append(a)
        return filtered

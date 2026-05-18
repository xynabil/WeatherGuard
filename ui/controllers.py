"""UI Controllers.

Die Controller stehen zwischen der UI (Pages) und der Datenbank/Services.
Wenn ein Button geklickt wird, ruft die UI eine Controller-Methode auf,
und der Controller erledigt die eigentliche Arbeit.

So muss die UI keine DB-Queries kennen und der Code bleibt aufgeteilt:
- Pages = Aussehen / Was sieht man
- Controller = Logik / Was passiert beim Klick
- DAO = Datenbank / Wo werden die Daten gespeichert
"""

from collections import defaultdict
from datetime import datetime, timedelta

from domain.models import User, Location, WeatherThreshold
from services.risk_analyzer import RiskAnalyzer


# ---------------------------------------------------------------------------
# Konstanten (werden auch in den Pages verwendet)
# ---------------------------------------------------------------------------

# Branchen-Vorschläge: pro Branche haben wir Standard-Grenzwerte
BRANCH_PRESETS = {
    "Bau": [
        {"parameter": "TTT_C",  "operator": "<", "value": 5.0,  "label": "Frost (Betonarbeiten)", "severity": "critical"},
        {"parameter": "FX_KMH", "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)",  "severity": "critical"},
        {"parameter": "RRR_MM", "operator": ">", "value": 10.0, "label": "Starkregen",            "severity": "warning"},
    ],
    "Event": [
        {"parameter": "FX_KMH", "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)", "severity": "critical"},
        {"parameter": "RRR_MM", "operator": ">", "value": 5.0,  "label": "Regen (Outdoor)",      "severity": "warning"},
        {"parameter": "TTT_C",  "operator": "<", "value": 0.0,  "label": "Frost (Glätte)",       "severity": "warning"},
    ],
    "Lieferdienst": [
        {"parameter": "FRESHSNOW_CM", "operator": ">", "value": 5.0,  "label": "Schneefall",  "severity": "warning"},
        {"parameter": "FX_KMH",       "operator": ">", "value": 70.0, "label": "Orkan",       "severity": "critical"},
        {"parameter": "TTT_C",        "operator": "<", "value": -5.0, "label": "Extremkälte", "severity": "critical"},
    ],
}

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


# ---------------------------------------------------------------------------
# AuthController - Login, Registrierung, Passwort ändern
# ---------------------------------------------------------------------------

class AuthController:
    """Kümmert sich um Login und Benutzer-Konten."""

    def __init__(self, user_dao):
        self.user_dao = user_dao

    def verify_login(self, username, password):
        """Prüft Login-Daten. Gibt den User zurück oder None bei falschem Passwort."""
        user = self.user_dao.get_by_username(username)
        if user is not None and user.check_password(password):
            return user
        return None

    def register(self, username, password, confirm_password, company):
        """Registriert einen neuen User.

        Gibt einen Fehlertext zurück (leerer String = alles ok).
        """
        username = username.strip()
        company = company.strip()

        # Einfache Validierung
        if not username or not password:
            return "Bitte Benutzername und Passwort eingeben."
        if len(password) < 6:
            return "Passwort muss mindestens 6 Zeichen haben."
        if password != confirm_password:
            return "Passwörter stimmen nicht überein."
        if self.user_dao.get_by_username(username) is not None:
            return "Benutzername ist bereits vergeben."

        # User in DB anlegen
        new_user = User(username=username, password=password, company=company)
        self.user_dao.add(new_user)
        return ""  # leerer String = erfolgreich

    def change_password(self, username, current_password, new_password):
        """Ändert das Passwort eines Users. Gibt Fehlertext oder "" zurück."""
        if not current_password or not new_password:
            return "Bitte alle Felder ausfüllen."
        if len(new_password) < 6:
            return "Passwort muss mindestens 6 Zeichen haben."

        # Aktuelles Passwort prüfen
        user = self.user_dao.get_by_username(username)
        if user is None or not user.check_password(current_password):
            return "Aktuelles Passwort ist falsch."

        self.user_dao.update_password(username, new_password)
        return ""


# ---------------------------------------------------------------------------
# LocationController - Standorte verwalten
# ---------------------------------------------------------------------------

class LocationController:
    """Kümmert sich um Standorte (anlegen, auflisten, löschen)."""

    def __init__(self, location_dao):
        self.location_dao = location_dao

    def list_locations(self, user_id=None):
        """Gibt alle Standorte eines Users zurück."""
        return self.location_dao.list_all(user_id=user_id)

    def add_location(self, name, latitude, longitude, company, branch, threshold_inputs, user_id):
        """Legt einen neuen Standort mit seinen Grenzwerten an.

        threshold_inputs ist eine Liste von Dicts wie:
            [{"preset": {...}, "value": 5.0}, ...]
        """
        # 1. Standort-Objekt erstellen
        new_location = Location(
            name=name,
            latitude=latitude,
            longitude=longitude,
            company=company,
            branch=branch,
            user_id=user_id,
        )

        # 2. Grenzwerte hinzufügen
        for threshold_input in threshold_inputs:
            preset = threshold_input["preset"]
            new_location.thresholds.append(WeatherThreshold(
                parameter=preset["parameter"],
                operator=preset["operator"],
                value=threshold_input["value"],  # vom User angepasster Wert
                label=preset["label"],
                severity=preset["severity"],
            ))

        # 3. Speichern
        return self.location_dao.add(new_location)

    def delete_location(self, location_id):
        """Löscht einen Standort (samt Grenzwerten und Alerts)."""
        self.location_dao.delete(location_id)


# ---------------------------------------------------------------------------
# AlertController - Wetter-Analyse laufen lassen & Alerts auflisten
# ---------------------------------------------------------------------------

class AlertController:
    """Kümmert sich um die Wetter-Analyse und das Lesen von Alerts."""

    def __init__(self, location_dao, alert_dao, weather_client):
        self.location_dao = location_dao
        self.alert_dao = alert_dao
        self.weather_client = weather_client
        # RiskAnalyzer hier intern erzeugen - der Controller nutzt ihn nur
        self.risk_analyzer = RiskAnalyzer(weather_client)

    def run_analysis(self, location_id):
        """Führt die Wetter-Analyse für einen Standort durch.

        - Holt aktuelle Wetterdaten
        - Prüft alle Grenzwerte
        - Speichert die neuen Alerts in der DB
        - Gibt die neuen Alerts zurück
        """
        location = self.location_dao.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Standort mit ID {location_id} nicht gefunden.")

        # Analyse durchführen
        new_alerts = self.risk_analyzer.analyze(location)

        # Alte Alerts ersetzen
        self.alert_dao.replace_for_location(location_id, new_alerts)

        return new_alerts

    def list_alerts(self, limit=200, user_id=None):
        """Gibt die Alerts eines Users zurück (neueste zuerst)."""
        return self.alert_dao.list_all(limit=limit, user_id=user_id)

    def get_current_weather(self, latitude, longitude):
        """Holt die aktuelle Wetter-Prognose (für die UI-Anzeige)."""
        return self.weather_client.get_forecast(latitude, longitude)


# ---------------------------------------------------------------------------
# HistoryController - Statistiken für die Alert-History-Seite
# ---------------------------------------------------------------------------

class HistoryController:
    """Berechnet Statistiken (KPIs, Charts) für die Alert-History-Seite."""

    def __init__(self, alert_dao):
        self.alert_dao = alert_dao

    def get_kpis(self, user_id=None):
        """Gibt die 4 KPI-Zahlen oben auf der Seite zurück.

        Returns: Dict mit Schlüsseln 'total', 'danger', 'warning', 'heute'.
        """
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        today = datetime.now().date()

        # Zähler initialisieren
        total = len(all_alerts)
        danger = 0
        warning = 0
        heute = 0

        # Alerts durchgehen und zählen
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

    def get_alerts_per_day(self, user_id=None):
        """Daten für das Balken-Diagramm: Alerts pro Tag (letzte 7 Tage).

        Returns: Liste von Tupeln (Tagesname, Anzahl, ist_heute).
        """
        # Alle Alerts der letzten 7 Tage holen
        cutoff = datetime.now() - timedelta(days=7)
        all_alerts = self.alert_dao.list_all(user_id=user_id)
        recent_alerts = [a for a in all_alerts if a.created_at >= cutoff]

        # Alerts pro Datum zählen
        counts_by_date = defaultdict(int)
        for alert in recent_alerts:
            counts_by_date[alert.created_at.date()] += 1

        # Liste für die letzten 7 Tage bauen (ältester zuerst)
        today = datetime.now().date()
        result = []
        for days_ago in range(6, -1, -1):
            day = today - timedelta(days=days_ago)
            day_name = DAY_NAMES[day.weekday()]
            count = counts_by_date.get(day, 0)
            is_today = (day == today)
            result.append((day_name, count, is_today))

        return result

    def get_alerts_by_type(self, user_id=None):
        """Daten für das Kategorie-Diagramm.

        Returns: Liste von Tupeln (Typ-Name, Anzahl, Farbe), sortiert nach Anzahl.
        """
        all_alerts = self.alert_dao.list_all(user_id=user_id)

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

        return alerts

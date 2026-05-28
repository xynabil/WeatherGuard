"""AlertController - Wetter-Analyse laufen lassen & Alerts auflisten."""

from datetime import datetime

from services.risk_analyzer import RiskAnalyzer


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
        location = self.location_dao.get_by_id(location_id) #Holt den Standort mit der angegebenen ID aus der Datenbank.
        if location is None:
            raise ValueError(f"Standort mit ID {location_id} nicht gefunden.")

        # Analyse durchführen
        new_alerts = self.risk_analyzer.analyze(location)

        # Nur die heutigen Alerts ersetzen, historische bleiben erhalten
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.alert_dao.replace_for_location(location_id, today_start, new_alerts)

        return new_alerts

    def list_alerts(self, limit=200, user_id=None):
        """Gibt die Alerts eines Users zurück (neueste zuerst)."""
        return self.alert_dao.list_all(limit=limit, user_id=user_id)

    def list_current_alerts(self, user_id=None):
        """Gibt nur die heutigen Alerts zurück (für das Live-Dashboard)."""
        return self.alert_dao.list_current(user_id=user_id)

    def get_current_weather(self, latitude, longitude):
        """Holt die aktuelle Wetter-Prognose (für die UI-Anzeige)."""
        return self.weather_client.get_forecast(latitude, longitude)

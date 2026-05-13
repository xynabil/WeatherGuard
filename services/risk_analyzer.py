"""RiskAnalyzer - prüft Wetterdaten gegen Grenzwerte.

Wir gehen die Prognose Stunde für Stunde durch und schauen,
ob ein Grenzwert überschritten wird. Pro Grenzwert erzeugen wir
maximal EINEN Alert (auch wenn er mehrmals überschritten wird),
damit wir nicht 100+ Warnungen pro Standort haben.

Wir merken uns:
- Den ersten Zeitpunkt, an dem der Grenzwert überschritten wird
- Den schlimmsten Wert (am weitesten vom Grenzwert entfernt)
"""

from datetime import datetime

from domain.models import Alert


class RiskAnalyzer:
    """Analysiert eine Wetter-Prognose und erstellt Warnungen."""

    # Anzeigename pro Wetter-Parameter (für die UI)
    PARAMETER_LABELS = {
        "TTT_C":         "Temperatur (°C)",
        "FF_KMH":        "Wind (km/h)",
        "FX_KMH":        "Windböen (km/h)",
        "RRR_MM":        "Niederschlag (mm)",
        "FRESHSNOW_CM":  "Neuschnee (cm)",
        "RELHUM_PERCENT": "Luftfeuchtigkeit (%)",
    }

    def __init__(self, weather_client):
        self.weather_client = weather_client

    def analyze(self, location):
        """Analysiert die Prognose eines Standorts und gibt Alerts zurück."""
        # 1. Wetter-Prognose holen
        forecast = self.weather_client.get_forecast(location.latitude, location.longitude)

        # 2. Verletzungen sammeln (pro Grenzwert max. eine)
        # violations[threshold_id] = {"first_time": ..., "worst_value": ..., "threshold": ...}
        violations = {}

        # Jede Stunde der Prognose durchgehen
        for day in forecast.get("days", []):
            for hour_data in day.get("hours", []):
                self._check_hour(hour_data, location.thresholds, violations)

        # 3. Aus den Verletzungen Alerts machen
        alerts = []
        for info in violations.values():
            threshold = info["threshold"]
            alert = Alert(
                location_id=location.id,
                threshold_label=threshold.label,
                severity=threshold.severity,
                parameter=threshold.parameter,
                actual_value=info["worst_value"],
                threshold_value=threshold.value,
                forecast_time=info["first_time"],
            )
            alerts.append(alert)

        return alerts

    def _check_hour(self, hour_data, thresholds, violations):
        """Prüft eine einzelne Stunde gegen alle Grenzwerte eines Standorts.

        Wenn ein Grenzwert überschritten wird, speichern wir das in 'violations'.
        """
        # Zeitpunkt dieser Stunde parsen
        try:
            forecast_time = datetime.fromisoformat(hour_data.get("date_time", ""))
        except (ValueError, TypeError):
            forecast_time = datetime.now()

        # Jeden Grenzwert prüfen
        for threshold in thresholds:
            actual_value = hour_data.get(threshold.parameter)
            if actual_value is None:
                continue  # Wert nicht vorhanden → überspringen

            if not threshold.is_exceeded(actual_value):
                continue  # Grenzwert nicht überschritten → ok

            # Grenzwert wurde überschritten!
            if threshold.id not in violations:
                # Erste Überschreitung dieses Grenzwerts
                violations[threshold.id] = {
                    "first_time": forecast_time,
                    "worst_value": actual_value,
                    "threshold": threshold,
                }
            else:
                # Weitere Überschreitung: ist der neue Wert "schlimmer"?
                existing = violations[threshold.id]
                if threshold.operator in (">", ">="):
                    # Bei "grösser als": je höher, desto schlimmer
                    if actual_value > existing["worst_value"]:
                        existing["worst_value"] = actual_value
                else:
                    # Bei "kleiner als": je tiefer, desto schlimmer
                    if actual_value < existing["worst_value"]:
                        existing["worst_value"] = actual_value

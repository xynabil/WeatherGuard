from datetime import datetime

from domain.models import Location, Alert
from services.weather_client import WeatherClient


class RiskAnalyzer:
    """Prüft Wetterdaten gegen Grenzwerte und erzeugt Alerts.

    Pro Grenzwert wird maximal ein Alert erzeugt — nämlich für den
    ersten Zeitpunkt, an dem der Grenzwert überschritten wird.
    So entstehen keine 100+ Duplikate über die 3-Tages-Prognose.
    """

    # Mapping: API-Feld → menschenlesbarer Name
    PARAMETER_LABELS = {
        "TTT_C":          "Temperatur (°C)",
        "FF_KMH":         "Wind (km/h)",
        "FX_KMH":         "Windböen (km/h)",
        "RRR_MM":         "Niederschlag (mm)",
        "PROBPCP_PERCENT":"Regenwahrscheinlichkeit (%)",
        "FRESHSNOW_CM":   "Neuschnee (cm)",
        "RELHUM_PERCENT": "Luftfeuchtigkeit (%)",
    }

    def __init__(self, weather_client: WeatherClient):
        self.weather_client = weather_client

    def analyze(self, location: Location) -> list[Alert]:
        """Analysiert die Prognose und gibt pro Grenzwert maximal einen Alert zurück.

        Der Alert enthält den ersten Zeitpunkt, an dem der Grenzwert
        überschritten wird, sowie den schlechtesten gemessenen Wert.
        """
        forecast = self.weather_client.get_forecast(location.latitude, location.longitude)

        # threshold.id → {"first_time": datetime, "worst_value": float}
        violations: dict[int, dict] = {}

        for day in forecast.get("days", []):
            for hour_data in day.get("hours", []):
                try:
                    forecast_time = datetime.fromisoformat(hour_data.get("date_time", ""))
                except (ValueError, TypeError):
                    forecast_time = datetime.now()

                for threshold in location.thresholds:
                    actual_value = hour_data.get(threshold.parameter)
                    if actual_value is None:
                        continue

                    if threshold.is_exceeded(actual_value):
                        if threshold.id not in violations:
                            # Erste Überschreitung: speichern
                            violations[threshold.id] = {
                                "first_time":  forecast_time,
                                "worst_value": actual_value,
                                "threshold":   threshold,
                            }
                        else:
                            # Schlimmeren Wert merken (weiter von Grenzwert entfernt)
                            existing = violations[threshold.id]
                            if threshold.operator in (">", ">="):
                                if actual_value > existing["worst_value"]:
                                    existing["worst_value"] = actual_value
                            else:  # "<", "<="
                                if actual_value < existing["worst_value"]:
                                    existing["worst_value"] = actual_value

        # Einen Alert pro verletztem Grenzwert erzeugen
        alerts = []
        for info in violations.values():
            t = info["threshold"]
            alerts.append(Alert(
                location_id=location.id,
                threshold_label=t.label,
                severity=t.severity,
                parameter=t.parameter,
                actual_value=info["worst_value"],
                threshold_value=t.value,
                forecast_time=info["first_time"],
            ))

        return alerts

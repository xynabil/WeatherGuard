from datetime import datetime

from models.location import Location
from models.threshold import WeatherThreshold
from models.alert import Alert
from services.weather_client import WeatherClient


class RiskAnalyzer:
    """Prüft Wetterdaten gegen Grenzwerte und erzeugt Alerts."""

    # Mapping: API-Feld → menschenlesbarer Name
    PARAMETER_LABELS = {
        "TTT_C": "Temperatur (°C)",
        "FF_KMH": "Wind (km/h)",
        "FX_KMH": "Windböen (km/h)",
        "RRR_MM": "Niederschlag (mm)",
        "PROBPCP_PERCENT": "Regenwahrscheinlichkeit (%)",
        "FRESHSNOW_CM": "Neuschnee (cm)",
        "RELHUM_PERCENT": "Luftfeuchtigkeit (%)",
    }

    def __init__(self, weather_client: WeatherClient):
        self.weather_client = weather_client

    def analyze(self, location: Location) -> list[Alert]:
        """Analysiert die Prognose für einen Standort und gibt Alerts zurück."""
        forecast = self.weather_client.get_forecast(location.latitude, location.longitude)
        alerts: list[Alert] = []

        for day in forecast.get("days", []):
            for hour_data in day.get("hours", []):
                hour_alerts = self._check_thresholds(location, hour_data)
                alerts.extend(hour_alerts)

        return alerts

    def _check_thresholds(self, location: Location, hour_data: dict) -> list[Alert]:
        """Prüft alle Thresholds eines Standorts gegen eine Stunde."""
        alerts = []
        forecast_time_str = hour_data.get("date_time", "")

        try:
            forecast_time = datetime.fromisoformat(forecast_time_str)
        except (ValueError, TypeError):
            forecast_time = datetime.now()

        for threshold in location.thresholds:
            actual_value = hour_data.get(threshold.parameter)
            if actual_value is None:
                continue

            if threshold.is_exceeded(actual_value):
                alert = Alert(
                    location_id=location.id,
                    threshold_label=threshold.label,
                    severity=threshold.severity,
                    parameter=threshold.parameter,
                    actual_value=actual_value,
                    threshold_value=threshold.value,
                    forecast_time=forecast_time,
                )
                alerts.append(alert)

        return alerts

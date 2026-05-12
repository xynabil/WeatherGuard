"""RiskAnalyzer - vergleicht die Wetter-Prognose mit den Grenzwerten.

Geht jede Stunde der 3-Tages-Prognose durch und prüft pro Location:
"Wird hier irgendwann ein Grenzwert überschritten?"
Falls ja, wird ein Alert erzeugt - aber nur EINER pro Grenzwert
(sonst hätten wir 100+ Alerts über 3 Tage Prognose, das wäre unbrauchbar).
"""

from datetime import datetime

from domain.models import Alert


# Menschenlesbare Namen für die Parameter (werden in der UI angezeigt)
PARAMETER_LABELS = {
    "TTT_C":          "Temperatur (°C)",
    "FF_KMH":         "Wind (km/h)",
    "FX_KMH":         "Windböen (km/h)",
    "RRR_MM":         "Niederschlag (mm)",
    "FRESHSNOW_CM":   "Neuschnee (cm)",
    "RELHUM_PERCENT": "Luftfeuchtigkeit (%)",
}


class RiskAnalyzer:
    """Prüft Wetterdaten gegen Grenzwerte und erzeugt daraus Alerts."""

    def __init__(self, weather_client):
        self.weather_client = weather_client

    def analyze(self, location):
        """Analysiert die Prognose für eine Location.

        Gibt eine Liste von Alert-Objekten zurück. Pro Grenzwert höchstens einer:
        - mit dem ersten Zeitpunkt, an dem der Grenzwert überschritten wird
        - mit dem schlimmsten Wert über die ganze Prognose hinweg
        """
        # 1. Wetterdaten holen
        forecast = self.weather_client.get_forecast(
            location.latitude, location.longitude,
        )

        # 2. Für jeden Grenzwert merken wir uns:
        #    "wann zuerst überschritten?" und "wie schlimm wird's maximal?"
        #    Aufbau: {threshold_id: {"first_time": ..., "worst_value": ..., "threshold": ...}}
        violations = {}

        # Durch alle Tage und Stunden gehen
        for day in forecast.get("days", []):
            for hour_data in day.get("hours", []):
                # Zeitpunkt aus den Daten lesen
                time_str = hour_data.get("date_time", "")
                try:
                    forecast_time = datetime.fromisoformat(time_str)
                except (ValueError, TypeError):
                    forecast_time = datetime.now()

                # Jeden Grenzwert dieser Location prüfen
                for threshold in location.thresholds:
                    actual_value = hour_data.get(threshold.parameter)
                    if actual_value is None:
                        continue   # Diesen Parameter haben wir nicht

                    # Überschreitung?
                    if threshold.is_exceeded(actual_value):
                        if threshold.id not in violations:
                            # Erste Überschreitung dieses Grenzwerts merken
                            violations[threshold.id] = {
                                "first_time":  forecast_time,
                                "worst_value": actual_value,
                                "threshold":   threshold,
                            }
                        else:
                            # Schon mal überschritten - falls jetzt noch schlimmer, neuen Wert merken
                            current_worst = violations[threshold.id]["worst_value"]
                            if threshold.operator in (">", ">="):
                                # Bei ">"-Grenzwerten ist "schlimmer" = höher (mehr Wind, mehr Regen)
                                if actual_value > current_worst:
                                    violations[threshold.id]["worst_value"] = actual_value
                            else:
                                # Bei "<"-Grenzwerten ist "schlimmer" = niedriger (z.B. tiefere Temperatur)
                                if actual_value < current_worst:
                                    violations[threshold.id]["worst_value"] = actual_value

        # 3. Für jeden überschrittenen Grenzwert genau einen Alert bauen
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

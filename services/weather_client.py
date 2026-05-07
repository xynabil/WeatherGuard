"""WeatherClient — holt Wetterdaten via Open-Meteo.

Open-Meteo ist kostenlos und benötigt keinen API-Key.
Die Antwort wird intern so umgewandelt, dass RiskAnalyzer
dieselben Feldnamen (TTT_C, FX_KMH, …) erhält wie vorher.

API-Dokumentation: https://open-meteo.com/en/docs
"""
import requests
from datetime import datetime


class WeatherClient:
    """Client für die Open-Meteo Wetter-API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # Felder, die physikalisch nicht negativ sein können
    NON_NEGATIVE = {"FF_KMH", "FX_KMH", "RRR_MM", "FRESHSNOW_CM", "RELHUM_PERCENT"}

    # Mapping: interner Feldname → Open-Meteo-Parametername
    FIELD_MAP = {
        "TTT_C":          "temperature_2m",
        "FF_KMH":         "windspeed_10m",
        "FX_KMH":         "windgusts_10m",
        "RRR_MM":         "precipitation",
        "FRESHSNOW_CM":   "snowfall",
        "RELHUM_PERCENT": "relativehumidity_2m",
    }

    def get_forecast(self, latitude: float, longitude: float) -> dict:
        """Holt die stündliche 3-Tages-Prognose für eine Position.

        Gibt ein Dict zurück mit:
            {"days": [{"date": "...", "hours": [{"TTT_C": ..., "FX_KMH": ..., ...}]}]}

        Dieses Format ist identisch mit dem, das RiskAnalyzer erwartet.
        """
        ometo_fields = list(self.FIELD_MAP.values())

        response = requests.get(
            self.BASE_URL,
            params={
                "latitude":       latitude,
                "longitude":      longitude,
                "hourly":         ",".join(ometo_fields),
                "forecast_days":  3,
                "timezone":       "Europe/Zurich",
                "wind_speed_unit": "kmh",   # km/h direkt, kein Umrechnen nötig
            },
            timeout=10,
        )
        response.raise_for_status()
        return self._convert(response.json())

    def _convert(self, raw: dict) -> dict:
        """Wandelt Open-Meteo-Antwort ins interne Format um.

        Open-Meteo liefert parallele Arrays (eine Liste pro Feld).
        Wir formen diese in Tage → Stunden um.
        """
        hourly = raw.get("hourly", {})
        times  = hourly.get("time", [])

        # Umgekehrtes Mapping: Open-Meteo-Name → interner Name
        reverse_map = {v: k for k, v in self.FIELD_MAP.items()}

        # Stunden-Dicts bauen
        days: dict = {}
        for i, ts_str in enumerate(times):
            dt   = datetime.fromisoformat(ts_str)
            date = dt.date()
            if date not in days:
                days[date] = []

            hour_data = {"date_time": ts_str}
            for ometo_key, internal_key in reverse_map.items():
                values = hourly.get(ometo_key, [])
                val = values[i] if i < len(values) else None
                if val is not None and internal_key in self.NON_NEGATIVE:
                    val = max(0.0, val)
                hour_data[internal_key] = val

            days[date].append(hour_data)

        return {
            "days": [
                {"date": str(date), "hours": hours}
                for date, hours in sorted(days.items())
            ]
        }

    def __repr__(self) -> str:
        return "<WeatherClient(api=Open-Meteo)>"

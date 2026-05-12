"""WeatherClient - holt Wetterdaten von der Open-Meteo API.

Open-Meteo ist kostenlos und braucht keinen API-Key.
Wir holen eine 3-Tages-Prognose mit stündlichen Werten und
wandeln das Format intern um, damit der RiskAnalyzer es leicht
verarbeiten kann.

API-Dokumentation: https://open-meteo.com/en/docs
"""

from datetime import datetime

import requests


class WeatherClient:
    """Holt Wetter-Prognosen von Open-Meteo."""

    # URL der API
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # Diese Werte können physikalisch nicht negativ sein.
    # Falls die API mal einen kleinen negativen Wert liefert (z.B. -0.01 mm Regen),
    # setzen wir den auf 0.
    NON_NEGATIVE_FIELDS = ["FF_KMH", "FX_KMH", "RRR_MM", "FRESHSNOW_CM", "RELHUM_PERCENT"]

    # Übersetzung: unser interner Name → Open-Meteo Name
    FIELD_MAP = {
        "TTT_C":          "temperature_2m",
        "FF_KMH":         "windspeed_10m",
        "FX_KMH":         "windgusts_10m",
        "RRR_MM":         "precipitation",
        "FRESHSNOW_CM":   "snowfall",
        "RELHUM_PERCENT": "relativehumidity_2m",
    }

    def get_forecast(self, latitude, longitude):
        """Holt die 3-Tages-Prognose für eine Position.

        Gibt ein Dictionary zurück in dieser Form:
            {
                "days": [
                    {"date": "2026-05-12", "hours": [{"TTT_C": 18.5, "FX_KMH": 25, ...}, ...]},
                    {"date": "2026-05-13", "hours": [...]},
                    ...
                ]
            }
        """
        # Welche Felder wollen wir von der API holen?
        open_meteo_fields = list(self.FIELD_MAP.values())

        # API-Aufruf
        response = requests.get(
            self.BASE_URL,
            params={
                "latitude":        latitude,
                "longitude":       longitude,
                "hourly":          ",".join(open_meteo_fields),
                "forecast_days":   3,
                "timezone":        "Europe/Zurich",
                "wind_speed_unit": "kmh",
            },
            timeout=10,
        )
        response.raise_for_status()  # Fehler werfen, falls etwas schiefging

        # Antwort von API-Format in unser internes Format umwandeln
        return self._convert_to_internal_format(response.json())

    def _convert_to_internal_format(self, api_response):
        """Wandelt die Open-Meteo-Antwort in unser internes Format um.

        Open-Meteo liefert parallele Listen (eine pro Wetter-Feld).
        Wir bauen daraus eine Liste von Tagen, jeder Tag mit Liste von Stunden.
        """
        hourly = api_response.get("hourly", {})
        times = hourly.get("time", [])

        # Umgekehrte Übersetzung: Open-Meteo Name → unser Name
        reverse_map = {}
        for our_name, ometo_name in self.FIELD_MAP.items():
            reverse_map[ometo_name] = our_name

        # Stunden nach Tagen gruppieren
        days_dict = {}  # date → Liste von Stunden-Dicts

        for index, timestamp_string in enumerate(times):
            # Zeitstempel parsen
            dt = datetime.fromisoformat(timestamp_string)
            date = dt.date()

            # Neue Tages-Liste anlegen, falls noch nicht da
            if date not in days_dict:
                days_dict[date] = []

            # Stunden-Dict bauen
            hour_data = {"date_time": timestamp_string}
            for ometo_name, our_name in reverse_map.items():
                values_list = hourly.get(ometo_name, [])
                value = values_list[index] if index < len(values_list) else None

                # Negative Werte abfangen, wo's nicht sinnvoll ist
                if value is not None and our_name in self.NON_NEGATIVE_FIELDS:
                    value = max(0.0, value)

                hour_data[our_name] = value

            days_dict[date].append(hour_data)

        # Aus dem Dict eine sortierte Liste machen
        days_list = []
        for date in sorted(days_dict.keys()):
            days_list.append({"date": str(date), "hours": days_dict[date]})

        return {"days": days_list}

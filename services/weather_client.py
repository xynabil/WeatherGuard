"""WeatherClient - holt Wetterdaten von Open-Meteo.

Open-Meteo ist eine kostenlose Wetter-API ohne API-Key.
Doku: https://open-meteo.com/en/docs

Die Klasse macht zwei Dinge:
1. Eine HTTP-Anfrage an Open-Meteo schicken (mit Längen-/Breitengrad)
2. Die Antwort in unser internes Format umwandeln, damit der RiskAnalyzer
   damit arbeiten kann.
"""

from datetime import datetime

import requests


# URL der Open-Meteo-API
BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Wie heissen unsere Parameter bei Open-Meteo?
# Wir nennen die Temperatur z.B. "TTT_C", die API nennt sie "temperature_2m".
FIELD_MAP = {
    "TTT_C":          "temperature_2m",       # Temperatur in °C
    "FF_KMH":         "windspeed_10m",         # Wind in km/h
    "FX_KMH":         "windgusts_10m",         # Windböen in km/h
    "RRR_MM":         "precipitation",         # Niederschlag in mm
    "FRESHSNOW_CM":   "snowfall",              # Neuschnee in cm
    "RELHUM_PERCENT": "relativehumidity_2m",   # Luftfeuchtigkeit in %
}

# Diese Werte dürfen physikalisch nicht negativ sein.
# Falls die API mal -0.1 mm Regen liefert, runden wir auf 0.
NON_NEGATIVE = {"FF_KMH", "FX_KMH", "RRR_MM", "FRESHSNOW_CM", "RELHUM_PERCENT"}


class WeatherClient:
    """Client für die Open-Meteo Wetter-API."""

    def get_forecast(self, latitude, longitude):
        """Holt die 3-Tages-Stunden-Prognose für eine Position.

        Gibt ein Dict zurück mit folgendem Aufbau:
            {"days": [
                {"date": "2024-...",
                 "hours": [
                    {"TTT_C": 5.2, "FX_KMH": 30.0, ...},
                    ...
                 ]},
                ...
            ]}
        """
        # 1. Welche Felder wollen wir von der API?
        # Open-Meteo erwartet sie kommagetrennt: "temperature_2m,windspeed_10m,..."
        open_meteo_fields = list(FIELD_MAP.values())

        # 2. HTTP-Anfrage an die API schicken
        response = requests.get(
            BASE_URL,
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
        response.raise_for_status()    # Fehler werfen, falls die API nicht antwortet
        raw_data = response.json()

        # 3. Antwort in unser Format umwandeln und zurückgeben
        return self.convert(raw_data)

    def convert(self, raw_data):
        """Wandelt die Open-Meteo-Antwort in unser internes Format um.

        Open-Meteo liefert parallele Listen (eine Liste pro Feld):
            time:          ["2024-01-01T00:00", "2024-01-01T01:00", ...]
            temperature_2m:[2.1, 1.8, ...]
            windspeed_10m: [15.0, 18.0, ...]

        Wir bauen daraus eine Liste von Tagen, jeder Tag mit einer Liste von Stunden.
        """
        hourly = raw_data.get("hourly", {})
        times = hourly.get("time", [])

        # Umgekehrte Zuordnung: Open-Meteo-Name → unser Name
        reverse_map = {}
        for our_name, open_meteo_name in FIELD_MAP.items():
            reverse_map[open_meteo_name] = our_name

        # Stunden nach Tagen gruppieren
        days_dict = {}
        for i, timestamp_str in enumerate(times):
            timestamp = datetime.fromisoformat(timestamp_str)
            date = timestamp.date()

            # Neuen Tag anlegen, wenn nötig
            if date not in days_dict:
                days_dict[date] = []

            # Daten für diese Stunde zusammenstellen
            hour_data = {"date_time": timestamp_str}
            for open_meteo_name, our_name in reverse_map.items():
                values = hourly.get(open_meteo_name, [])
                if i < len(values):
                    value = values[i]
                else:
                    value = None
                # Negative Werte abfangen (z.B. -0.1 mm Regen → 0.0)
                if value is not None and our_name in NON_NEGATIVE:
                    value = max(0.0, value)
                hour_data[our_name] = value

            days_dict[date].append(hour_data)

        # In eine sortierte Liste umwandeln (Datum aufsteigend)
        result_days = []
        for date in sorted(days_dict.keys()):
            result_days.append({
                "date":  str(date),
                "hours": days_dict[date],
            })
        return {"days": result_days}

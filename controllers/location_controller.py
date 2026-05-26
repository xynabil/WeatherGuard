"""LocationController - Standorte verwalten (anlegen, auflisten, löschen)."""

from domain.models import Location, WeatherThreshold


# Branchen-Vorschläge: pro Branche haben wir Standard-Grenzwerte.
# Wird auch von der UI verwendet, um Threshold-Optionen anzuzeigen.
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

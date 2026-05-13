"""Demo-Daten für die Datenbank.

Beim ersten Start der App soll die Datenbank nicht leer sein.
Diese Klasse fügt einen Demo-User, drei Standorte und ein paar
historische Alerts ein, damit die App von Anfang an "lebt".
"""

from datetime import datetime, timedelta

from sqlmodel import select

from domain.models import User, Location, WeatherThreshold, Alert


# Demo-Standorte mit ihren Grenzwerten (als normale Python-Listen/Dicts).
# So müssen wir die Daten nicht im Code "verstecken".
DEMO_LOCATIONS = [
    {
        "name": "Baustelle Zürich HB",
        "latitude": 47.3784, "longitude": 8.5400,
        "branch": "Bau", "company": "Müller Bau AG",
        "thresholds": [
            {"parameter": "TTT_C",  "operator": "<", "value": 5.0,  "label": "Frost (Betonarbeiten)", "severity": "critical"},
            {"parameter": "FX_KMH", "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)",  "severity": "critical"},
            {"parameter": "RRR_MM", "operator": ">", "value": 10.0, "label": "Starkregen",            "severity": "warning"},
        ],
    },
    {
        "name": "Open-Air Bühne Olten",
        "latitude": 47.3524, "longitude": 7.9027,
        "branch": "Event", "company": "EventPro GmbH",
        "thresholds": [
            {"parameter": "FX_KMH", "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)", "severity": "critical"},
            {"parameter": "RRR_MM", "operator": ">", "value": 5.0,  "label": "Regen (Outdoor)",      "severity": "warning"},
            {"parameter": "TTT_C",  "operator": "<", "value": 0.0,  "label": "Frost (Glätte)",       "severity": "warning"},
        ],
    },
    {
        "name": "Depot Basel Süd",
        "latitude": 47.5468, "longitude": 7.5883,
        "branch": "Lieferdienst", "company": "SwiftLogistic AG",
        "thresholds": [
            {"parameter": "FRESHSNOW_CM", "operator": ">", "value": 5.0,  "label": "Schneefall",  "severity": "warning"},
            {"parameter": "FX_KMH",       "operator": ">", "value": 70.0, "label": "Orkan",       "severity": "critical"},
            {"parameter": "TTT_C",        "operator": "<", "value": -5.0, "label": "Extremkälte", "severity": "critical"},
        ],
    },
]


# Demo-Alerts: (Standort-Index, Label, Severity, Parameter, Ist-Wert, Grenzwert, Tage_zurück, Stunde)
DEMO_ALERTS = [
    # Zürich HB (Index 0)
    (0, "Sturm (Kranarbeiten)",   "critical", "FX_KMH",       72.0,  60.0, 0, 8),
    (0, "Starkregen",              "warning",  "RRR_MM",       18.0,  10.0, 1, 14),
    (0, "Frost (Betonarbeiten)",   "critical", "TTT_C",         2.3,   5.0, 3, 6),
    (0, "Starkregen",              "warning",  "RRR_MM",       14.5,  10.0, 5, 11),
    # Olten (Index 1)
    (1, "Frost (Glätte)",          "warning",  "TTT_C",         1.5,   2.0, 1, 6),
    (1, "Regen (Outdoor)",         "warning",  "RRR_MM",        8.2,   5.0, 2, 16),
    (1, "Sturm (Zelte/Bühnen)",    "critical", "FX_KMH",       55.0,  40.0, 4, 13),
    # Basel (Index 2)
    (2, "Schneefall",              "warning",  "FRESHSNOW_CM",  8.0,   5.0, 2, 7),
    (2, "Extremkälte",             "critical", "TTT_C",        -7.1,  -5.0, 3, 4),
    (2, "Schneefall",              "warning",  "FRESHSNOW_CM",  6.5,   5.0, 6, 9),
]


class WeatherSeeder:
    """Füllt die Datenbank mit Demo-Daten."""

    def seed(self, session):
        """Hauptmethode: legt User, Standorte und Alerts an."""
        # 1. Demo-User
        admin = self._create_demo_user(session)

        # 2. Demo-Standorte (mit Grenzwerten)
        locations = self._create_demo_locations(session, admin.id)

        # 3. Demo-Alerts
        self._create_demo_alerts(session, locations)

    def _create_demo_user(self, session):
        """Legt den 'admin'-User an, falls noch keiner existiert."""
        existing = session.exec(select(User)).first()
        if existing is not None:
            return existing

        admin = User(username="admin", password="admin123", company="Müller Bau AG")
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin

    def _create_demo_locations(self, session, user_id):
        """Legt die Demo-Standorte mit ihren Grenzwerten an."""
        # Falls schon Standorte existieren, einfach diese zurückgeben
        existing = list(session.exec(select(Location)).all())
        if existing:
            return existing

        created_locations = []
        for location_data in DEMO_LOCATIONS:
            # Standort erstellen
            location = Location(
                name=location_data["name"],
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                branch=location_data["branch"],
                company=location_data["company"],
                user_id=user_id,
            )
            # Grenzwerte hinzufügen
            for t in location_data["thresholds"]:
                location.thresholds.append(WeatherThreshold(
                    parameter=t["parameter"],
                    operator=t["operator"],
                    value=t["value"],
                    label=t["label"],
                    severity=t["severity"],
                ))
            session.add(location)
            created_locations.append(location)

        session.commit()
        return created_locations

    def _create_demo_alerts(self, session, locations):
        """Legt ein paar historische Alerts an, damit das Dashboard nicht leer ist."""
        existing = session.exec(select(Alert)).first()
        if existing is not None:
            return

        now = datetime.now()
        for loc_index, label, severity, param, actual, threshold, days_ago, hour in DEMO_ALERTS:
            location = locations[loc_index]
            # Zeitpunkt zusammenbauen: heute - days_ago, dann auf 'hour' setzen
            forecast_time = now - timedelta(days=days_ago, hours=now.hour - hour)

            alert = Alert(
                location_id=location.id,
                threshold_label=label,
                severity=severity,
                parameter=param,
                actual_value=actual,
                threshold_value=threshold,
                forecast_time=forecast_time,
                created_at=forecast_time,
            )
            session.add(alert)

        session.commit()

"""Demo-Daten für den allerersten Programmstart.

Wenn die Datenbank beim Start leer ist, füllt WeatherSeeder sie mit:
- einem Admin-User (admin / admin123)
- drei Demo-Standorten mit Grenzwerten (Baustelle, Event, Lieferdienst)
- 10 historischen Alerts (damit die History-Seite direkt Daten zeigt)
"""

from datetime import datetime, timedelta

from sqlmodel import select

from domain.models import User, Location, WeatherThreshold, Alert


# Die drei Demo-Standorte mit ihren Grenzwerten
DEMO_LOCATIONS = [
    {
        "name": "Baustelle Zürich HB",
        "latitude": 47.3784, "longitude": 8.5400,
        "branch": "Bau", "company": "Müller Bau AG",
        "thresholds": [
            {"parameter": "TTT_C",  "operator": "<", "value": 5.0,  "label": "Frost (Betonarbeiten)", "severity": "critical"},
            {"parameter": "FX_KMH", "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)",  "severity": "critical"},
            {"parameter": "RRR_MM", "operator": ">", "value": 10.0, "label": "Starkregen",             "severity": "warning"},
        ],
    },
    {
        "name": "Open-Air Bühne Olten",
        "latitude": 47.3524, "longitude": 7.9027,
        "branch": "Event", "company": "EventPro GmbH",
        "thresholds": [
            {"parameter": "FX_KMH", "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)", "severity": "critical"},
            {"parameter": "RRR_MM", "operator": ">", "value": 5.0,  "label": "Regen (Outdoor)",       "severity": "warning"},
            {"parameter": "TTT_C",  "operator": "<", "value": 0.0,  "label": "Frost (Glätte)",        "severity": "warning"},
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


# Historische Demo-Alerts: (location_index, label, severity, parameter, actual, threshold, days_ago, hour)
DEMO_ALERTS = [
    (0, "Sturm (Kranarbeiten)",  "critical", "FX_KMH",        72.0,  60.0, 0,  8),
    (0, "Starkregen",            "warning",  "RRR_MM",        18.0,  10.0, 1, 14),
    (0, "Frost (Betonarbeiten)", "critical", "TTT_C",          2.3,   5.0, 3,  6),
    (0, "Starkregen",            "warning",  "RRR_MM",        14.5,  10.0, 5, 11),
    (1, "Frost (Glätte)",        "warning",  "TTT_C",          1.5,   2.0, 1,  6),
    (1, "Regen (Outdoor)",       "warning",  "RRR_MM",         8.2,   5.0, 2, 16),
    (1, "Sturm (Zelte/Bühnen)",  "critical", "FX_KMH",        55.0,  40.0, 4, 13),
    (2, "Schneefall",            "warning",  "FRESHSNOW_CM",   8.0,   5.0, 2,  7),
    (2, "Extremkälte",           "critical", "TTT_C",         -7.1,  -5.0, 3,  4),
    (2, "Schneefall",            "warning",  "FRESHSNOW_CM",   6.5,   5.0, 6,  9),
]


class WeatherSeeder:
    """Füllt eine leere Datenbank mit Demo-Daten."""

    def seed(self, session):
        """Hauptmethode - ruft die drei Seed-Schritte nacheinander auf."""
        admin = self.seed_user(session)
        locations = self.seed_locations(session, admin)
        self.seed_alerts(session, locations)

    def seed_user(self, session):
        """Legt den Admin-User an, falls noch keiner existiert."""
        existing = session.exec(select(User)).first()
        if existing is not None:
            return existing

        admin = User(
            username="admin",
            password="admin123",
            company="Müller Bau AG",
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin

    def seed_locations(self, session, admin):
        """Legt die drei Demo-Standorte mit ihren Grenzwerten an."""
        # Falls schon welche existieren, einfach zurückgeben
        existing = list(session.exec(select(Location)).all())
        if existing:
            return existing

        locations = []
        for data in DEMO_LOCATIONS:
            # Eine neue Location erstellen
            loc = Location(
                name=data["name"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                branch=data["branch"],
                company=data["company"],
                user_id=admin.id,
            )
            # Grenzwerte zu dieser Location hinzufügen
            for t_data in data["thresholds"]:
                threshold = WeatherThreshold(
                    parameter=t_data["parameter"],
                    operator=t_data["operator"],
                    value=t_data["value"],
                    label=t_data["label"],
                    severity=t_data["severity"],
                )
                loc.thresholds.append(threshold)
            session.add(loc)
            locations.append(loc)

        session.commit()
        return locations

    def seed_alerts(self, session, locations):
        """Erzeugt 10 historische Alerts für die letzten Tage."""
        existing = session.exec(select(Alert)).first()
        if existing is not None:
            return

        now = datetime.now()
        for loc_index, label, severity, param, actual, threshold, days_ago, hour in DEMO_ALERTS:
            location = locations[loc_index]
            # Zeitpunkt berechnen: "vor X Tagen, um Y Uhr"
            time_point = now - timedelta(days=days_ago, hours=now.hour - hour)
            alert = Alert(
                location_id=location.id,
                threshold_label=label,
                severity=severity,
                parameter=param,
                actual_value=actual,
                threshold_value=threshold,
                forecast_time=time_point,
                created_at=time_point,
            )
            session.add(alert)
        session.commit()

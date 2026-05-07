"""Demo data seeder.

WeatherSeeder fills the database with one user, three locations, and
10 historical alerts so the app looks useful right after cloning.
Design pattern: same as MenuSeeder in the pizza reference project.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from domain.models import User, Location, WeatherThreshold, Alert


class WeatherSeeder:
    """Seeds demo users, locations, thresholds, and alerts."""

    def seed(self, session: Session) -> None:
        """Insert demo data. Call only when tables are empty."""
        self._seed_user(session)
        locations = self._seed_locations(session)
        self._seed_alerts(session, locations)

    # ------------------------------------------------------------------

    def _seed_user(self, session: Session) -> None:
        if session.exec(select(User)).first():
            return
        session.add(User(username="admin", password="admin123", company="Müller Bau AG"))
        session.commit()

    def _seed_locations(self, session: Session) -> list[Location]:
        if session.exec(select(Location)).first():
            return list(session.exec(select(Location)).all())

        admin = session.exec(select(User).where(User.username == "admin")).first()
        admin_id = admin.id if admin else None

        data = [
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

        locations = []
        for d in data:
            loc = Location(
                name=d["name"], latitude=d["latitude"], longitude=d["longitude"],
                branch=d["branch"], company=d["company"], user_id=admin_id,
            )
            for t in d["thresholds"]:
                loc.thresholds.append(WeatherThreshold(**t))
            session.add(loc)
            locations.append(loc)
        session.commit()
        return locations

    def _seed_alerts(self, session: Session, locations: list[Location]) -> None:
        if session.exec(select(Alert)).first():
            return

        now = datetime.now()
        raw = [
            # Zürich HB
            (locations[0], "Sturm (Kranarbeiten)", "critical", "FX_KMH",        72.0,  60.0, 0, 8),
            (locations[0], "Starkregen",           "warning",  "RRR_MM",         18.0,  10.0, 1, 14),
            (locations[0], "Frost (Betonarbeiten)","critical", "TTT_C",           2.3,   5.0, 3, 6),
            (locations[0], "Starkregen",           "warning",  "RRR_MM",         14.5,  10.0, 5, 11),
            # Olten
            (locations[1], "Frost (Glätte)",       "warning",  "TTT_C",           1.5,   2.0, 1, 6),
            (locations[1], "Regen (Outdoor)",      "warning",  "RRR_MM",          8.2,   5.0, 2, 16),
            (locations[1], "Sturm (Zelte/Bühnen)", "critical", "FX_KMH",         55.0,  40.0, 4, 13),
            # Basel
            (locations[2], "Schneefall",           "warning",  "FRESHSNOW_CM",    8.0,   5.0, 2, 7),
            (locations[2], "Extremkälte",          "critical", "TTT_C",          -7.1,  -5.0, 3, 4),
            (locations[2], "Schneefall",           "warning",  "FRESHSNOW_CM",    6.5,   5.0, 6, 9),
        ]

        for loc, label, severity, param, actual, threshold, days_ago, hour in raw:
            t = now - timedelta(days=days_ago, hours=now.hour - hour)
            session.add(Alert(
                location_id=loc.id,
                threshold_label=label,
                severity=severity,
                parameter=param,
                actual_value=actual,
                threshold_value=threshold,
                forecast_time=t,
                created_at=t,
            ))
        session.commit()

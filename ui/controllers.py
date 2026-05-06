"""UI controllers.

Controllers sit between the UI (pages) and the DAO/service layer.
They translate user actions into service/DAO calls and prepare data for the view.
Design pattern: same as AdminController / ShoppingController in the pizza reference project.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from domain.models import User, Location, WeatherThreshold, Alert
from data_access.dao import UserDAO, LocationDAO, AlertDAO
from services.weather_client import WeatherClient
from services.risk_analyzer import RiskAnalyzer


# ---------------------------------------------------------------------------
# Branch presets (industry-specific threshold suggestions)
# ---------------------------------------------------------------------------

BRANCH_PRESETS: dict = {
    "Bau": [
        {"parameter": "TTT_C",        "operator": "<", "value": 5.0,  "label": "Frost (Betonarbeiten)", "severity": "critical"},
        {"parameter": "FX_KMH",       "operator": ">", "value": 60.0, "label": "Sturm (Kranarbeiten)",  "severity": "critical"},
        {"parameter": "RRR_MM",       "operator": ">", "value": 10.0, "label": "Starkregen",             "severity": "warning"},
    ],
    "Event": [
        {"parameter": "FX_KMH",       "operator": ">", "value": 40.0, "label": "Sturm (Zelte/Bühnen)",  "severity": "critical"},
        {"parameter": "RRR_MM",       "operator": ">", "value": 5.0,  "label": "Regen (Outdoor)",        "severity": "warning"},
        {"parameter": "TTT_C",        "operator": "<", "value": 0.0,  "label": "Frost (Glätte)",         "severity": "warning"},
    ],
    "Lieferdienst": [
        {"parameter": "FRESHSNOW_CM", "operator": ">", "value": 5.0,  "label": "Schneefall",             "severity": "warning"},
        {"parameter": "FX_KMH",       "operator": ">", "value": 70.0, "label": "Orkan",                  "severity": "critical"},
        {"parameter": "TTT_C",        "operator": "<", "value": -5.0, "label": "Extremkälte",            "severity": "critical"},
    ],
}

# Mapping: API field name → display category
PARAM_TO_TYPE: dict = {
    "TTT_C":           "Frost",
    "FF_KMH":          "Wind",
    "FX_KMH":          "Wind",
    "RRR_MM":          "Rain",
    "FRESHSNOW_CM":    "Snow",
    "PROBPCP_PERCENT": "Rain",
    "RELHUM_PERCENT":  "Other",
}

TYPE_COLORS: dict = {
    "Wind":  "#4a9eff",
    "Frost": "#4ec9a8",
    "Rain":  "#b197fc",
    "Snow":  "#a8d8ea",
    "Other": "#888888",
}

DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


# ---------------------------------------------------------------------------

class AuthController:
    """Handles login and password changes."""

    def __init__(self, user_dao: UserDAO) -> None:
        self._user_dao = user_dao

    def verify_login(self, username: str, password: str) -> Optional[User]:
        """Return the User if credentials are correct, else None."""
        user = self._user_dao.get_by_username(username)
        if user and user.check_password(password):
            return user
        return None

    def register(self, username: str, password: str, confirm_pw: str, company: str) -> Tuple[bool, str]:
        """Register a new user. Returns (success, error_message)."""
        if not username.strip() or not password:
            return False, "Bitte Benutzername und Passwort eingeben."
        if len(password) < 6:
            return False, "Passwort muss mindestens 6 Zeichen haben."
        if password != confirm_pw:
            return False, "Passwörter stimmen nicht überein."
        if self._user_dao.get_by_username(username.strip()):
            return False, "Benutzername ist bereits vergeben."
        self._user_dao.add(User(username=username.strip(), password=password, company=company.strip()))
        return True, ""

    def change_password(self, username: str, current_pw: str, new_pw: str) -> Tuple[bool, str]:
        """Try to change password. Returns (success, error_message)."""
        if not current_pw or not new_pw:
            return False, "Bitte alle Felder ausfüllen."
        if len(new_pw) < 6:
            return False, "Passwort muss mindestens 6 Zeichen haben."
        user = self._user_dao.get_by_username(username)
        if not user or not user.check_password(current_pw):
            return False, "Aktuelles Passwort ist falsch."
        self._user_dao.update_password(username, new_pw)
        return True, ""


class LocationController:
    """Handles location listing, adding, and deleting."""

    def __init__(self, location_dao: LocationDAO) -> None:
        self._location_dao = location_dao

    def list_locations(self, user_id: int = None) -> List[Location]:
        return self._location_dao.list_all(user_id=user_id)

    def add_location(
        self,
        name: str,
        latitude: float,
        longitude: float,
        company: str,
        branch: str,
        threshold_inputs: list,
        user_id: int = None,
    ) -> Location:
        """Create and persist a new location with its thresholds."""
        loc = Location(
            name=name, latitude=latitude, longitude=longitude,
            user_id=user_id, branch=branch, company=company,
        )
        for t in threshold_inputs:
            loc.thresholds.append(WeatherThreshold(
                parameter=t["preset"]["parameter"],
                operator=t["preset"]["operator"],
                value=t["value"],
                label=t["preset"]["label"],
                severity=t["preset"]["severity"],
            ))
        return self._location_dao.add(loc)

    def delete_location(self, location_id: int) -> None:
        self._location_dao.delete(location_id)


class AlertController:
    """Handles running analysis and reading alerts."""

    def __init__(
        self,
        location_dao: LocationDAO,
        alert_dao: AlertDAO,
        weather_client: WeatherClient,
    ) -> None:
        self._location_dao = location_dao
        self._alert_dao    = alert_dao
        self._analyzer     = RiskAnalyzer(weather_client)
        self._weather_client = weather_client

    def run_analysis(self, location_id: int) -> List[Alert]:
        """Run weather analysis for one location, persist results, return new alerts."""
        loc = self._location_dao.get_by_id(location_id)
        if loc is None:
            raise ValueError(f"Location {location_id} not found.")
        new_alerts = self._analyzer.analyze(loc)
        self._alert_dao.replace_for_location(location_id, new_alerts)
        return new_alerts

    def list_alerts(self, limit: int = 200, user_id: int = None) -> List[Alert]:
        return self._alert_dao.list_all(limit=limit, user_id=user_id)

    def get_current_weather(self, latitude: float, longitude: float) -> dict:
        """Return the raw forecast dict for a location."""
        return self._weather_client.get_forecast(latitude, longitude)


class HistoryController:
    """Prepares aggregated data for the Alert History page."""

    def __init__(self, alert_dao: AlertDAO) -> None:
        self._alert_dao = alert_dao

    def get_kpis(self, user_id: int = None) -> dict:
        alerts = self._alert_dao.list_all(user_id=user_id)
        today  = datetime.now().date()
        return {
            "total":   len(alerts),
            "danger":  sum(1 for a in alerts if a.severity == "critical"),
            "warning": sum(1 for a in alerts if a.severity == "warning"),
            "heute":   sum(1 for a in alerts if a.created_at.date() == today),
        }

    def get_alerts_per_day(self, user_id: int = None) -> list:
        """Return (day_name, count, is_today) for the last 7 days."""
        cutoff = datetime.now() - timedelta(days=7)
        all_alerts = self._alert_dao.list_all(user_id=user_id)
        recent = [a for a in all_alerts if a.created_at >= cutoff]

        today  = datetime.now().date()
        counts: dict = defaultdict(int)
        for a in recent:
            counts[a.created_at.date()] += 1

        result = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            result.append((DAY_NAMES[day.weekday()], counts.get(day, 0), day == today))
        return result

    def get_alerts_by_type(self, user_id: int = None) -> list:
        """Return (type_name, count, color) sorted by count descending."""
        all_alerts = self._alert_dao.list_all(user_id=user_id)
        counts: dict = defaultdict(int)
        for a in all_alerts:
            counts[PARAM_TO_TYPE.get(a.parameter, "Other")] += 1
        return sorted(
            [(t, counts[t], TYPE_COLORS[t]) for t in TYPE_COLORS if counts[t] > 0],
            key=lambda x: -x[1],
        )

    def get_recent_alerts(self, filter_type: str = "All", user_id: int = None) -> List[Alert]:
        """Return the last 50 alerts, optionally filtered by type."""
        alerts = self._alert_dao.list_all(limit=50, user_id=user_id)
        if filter_type == "All":
            return alerts
        return [a for a in alerts if PARAM_TO_TYPE.get(a.parameter) == filter_type]

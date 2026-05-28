"""Datenbank-Modelle (Tabellen).

Wir definieren hier vier Tabellen mit SQLModel:
- User:             Login-Konten
- Location:         Überwachte Standorte (Baustelle, Event, Depot, ...)
- WeatherThreshold: Grenzwerte pro Standort (z.B. "Wind > 60 km/h = Sturm")
- Alert:            Warnungen, die in der DB gespeichert werden

SQLModel ist eine Bibliothek, die Python-Klassen automatisch in DB-Tabellen umwandelt.
Jede Klasse hier entspricht einer Tabelle.
"""

import operator
from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship


_COMPARE_OPS = {
    "<":  operator.lt,
    ">":  operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


class User(SQLModel, table=True):
    """Ein Login-Konto (Benutzer der App)."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50)
    password: str = Field(max_length=100)  # Klartext - reicht für ein Schulprojekt
    company: str = Field(max_length=100, default="")

    def check_password(self, password):
        """Prüft ob das eingegebene Passwort stimmt."""
        return self.password == password


class Location(SQLModel, table=True):
    """Ein überwachter Standort (z.B. eine Baustelle)."""

    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Wem gehört der Standort?
    name: str = Field(max_length=100)
    latitude: float
    longitude: float
    branch: str = Field(max_length=50)    # "Bau", "Event", "Lieferdienst"
    company: str = Field(max_length=100)

    # Beziehung zu Grenzwerten: ein Standort hat mehrere Grenzwerte
    thresholds: List["WeatherThreshold"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    # Beziehung zu Alerts: ein Standort hat mehrere Alerts
    alerts: List["Alert"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class WeatherThreshold(SQLModel, table=True):
    """Ein Grenzwert für einen Standort.

    Beispiele:
        - parameter="TTT_C",  operator="<", value=5.0   → Frost-Warnung
        - parameter="FX_KMH", operator=">", value=60.0  → Sturm-Warnung
    """

    __tablename__ = "thresholds"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    parameter: str = Field(max_length=30)     # z.B. "TTT_C", "FX_KMH", "RRR_MM"
    operator: str = Field(max_length=5)       # "<", ">", "<=", ">="
    value: float                              # der Grenzwert selbst
    label: str = Field(max_length=100)        # Anzeige-Name, z.B. "Sturm"
    severity: str = Field(default="warning", max_length=20)  # "warning" oder "critical"

    location: Optional["Location"] = Relationship(back_populates="thresholds")

    def is_exceeded(self, actual_value):
        """Prüft, ob der gemessene Wert den Grenzwert überschreitet.

        Beispiel: Grenzwert "TTT_C < 5", actual_value = 2.0 → True (Frost!)
        """
        compare = _COMPARE_OPS.get(self.operator)
        return compare(actual_value, self.value) if compare else False


class Alert(SQLModel, table=True):
    """Eine ausgelöste Wetter-Warnung."""

    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    threshold_label: str = Field(max_length=100)     # z.B. "Sturm (Kranarbeiten)"
    severity: str = Field(max_length=20)             # "warning" oder "critical"
    parameter: str = Field(max_length=30)            # welcher Wetter-Wert
    actual_value: float                              # tatsächlich gemessener Wert
    threshold_value: float                           # der überschrittene Grenzwert
    forecast_time: datetime                          # für welchen Zeitpunkt gilt die Warnung
    created_at: datetime = Field(default_factory=datetime.now)

    location: Optional["Location"] = Relationship(back_populates="alerts")

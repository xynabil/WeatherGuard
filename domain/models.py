"""Datenbank-Modelle.

Jede Klasse hier entspricht genau einer Tabelle in der SQLite-Datenbank.
SQLModel kümmert sich um die Übersetzung Python-Objekt ↔ SQL-Zeile.

Die vier Tabellen:
- User              → Benutzerkonten (Login)
- Location          → überwachte Standorte (Baustellen, Events, Depots)
- WeatherThreshold  → Grenzwerte pro Location ("Wind > 60 km/h")
- Alert             → ausgelöste Wetter-Warnungen
"""

from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """Ein Benutzerkonto.

    Hinweis: Das Passwort wird als Klartext gespeichert. Das ist nur
    für dieses Schulprojekt OK - in einer echten App würde man es hashen.
    """
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    username: str
    password: str
    company: str = ""

    def check_password(self, password):
        """Prüft, ob das eingegebene Passwort stimmt."""
        return self.password == password


class Location(SQLModel, table=True):
    """Ein überwachter Standort (Baustelle, Event-Location, Depot ...)."""
    __tablename__ = "locations"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")   # gehört zu welchem User?
    name: str
    latitude: float
    longitude: float
    branch: str       # "Bau", "Event" oder "Lieferdienst"
    company: str

    # Beziehung 1:n - eine Location hat mehrere Grenzwerte
    thresholds: list["WeatherThreshold"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    # Beziehung 1:n - eine Location hat mehrere Alerts
    alerts: list["Alert"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class WeatherThreshold(SQLModel, table=True):
    """Ein Grenzwert für eine Location.

    Beispiele:
        parameter="TTT_C",  operator="<", value=5.0   → warnt bei Frost
        parameter="FX_KMH", operator=">", value=60.0  → warnt bei Sturm
    """
    __tablename__ = "thresholds"

    id: int = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    parameter: str            # z.B. "TTT_C" (Temperatur), "FX_KMH" (Windböen)
    operator: str             # "<", ">", "<=" oder ">="
    value: float              # der eigentliche Grenzwert (z.B. 60.0)
    label: str                # menschenlesbarer Name (z.B. "Sturm (Kran)")
    severity: str = "warning" # "info", "warning" oder "critical"

    # Rückwärts-Beziehung: jeder Grenzwert kennt seine Location
    location: "Location" = Relationship(back_populates="thresholds")

    def is_exceeded(self, actual_value):
        """Prüft, ob der gemessene Wert den Grenzwert überschreitet."""
        if self.operator == "<":
            return actual_value < self.value
        if self.operator == ">":
            return actual_value > self.value
        if self.operator == "<=":
            return actual_value <= self.value
        if self.operator == ">=":
            return actual_value >= self.value
        return False


class Alert(SQLModel, table=True):
    """Eine ausgelöste Wetter-Warnung, gehört zu einer Location."""
    __tablename__ = "alerts"

    id: int = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    threshold_label: str       # z.B. "Sturm (Kranarbeiten)"
    severity: str              # "warning" oder "critical"
    parameter: str             # welcher Parameter ("FX_KMH" usw.)
    actual_value: float        # vorhergesagter Wert (z.B. 72.0 km/h)
    threshold_value: float     # der überschrittene Grenzwert (z.B. 60.0)
    forecast_time: datetime    # wann tritt der schlimme Wert auf?
    created_at: datetime = Field(default_factory=datetime.now)

    # Rückwärts-Beziehung: jeder Alert kennt seine Location
    location: "Location" = Relationship(back_populates="alerts")

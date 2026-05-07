"""Domain and ORM models.

We use SQLModel (SQLAlchemy + Pydantic) to map domain objects to a SQLite database.

Tables:
- User: login accounts
- Location: monitored sites with lat/lon
- WeatherThreshold: per-location alert conditions
- Alert: triggered warnings stored in the DB
"""

from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """A login account.

    Note: passwords are stored in plain text — intentional simplicity for a school project.
    In a production app you would use bcrypt or Argon2.
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50)
    password: str = Field(max_length=100)
    company: str = Field(max_length=100, default="")

    def check_password(self, password: str) -> bool:
        """Encapsulation: password comparison is hidden inside the model."""
        return self.password == password

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', company='{self.company}')>"


class Location(SQLModel, table=True):
    """A monitored site (construction site, event venue, depot, …)."""

    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")   # owner — only this user sees the location
    name: str = Field(max_length=100)
    latitude: float
    longitude: float
    branch: str = Field(max_length=50)    # "Bau", "Event", "Lieferdienst"
    company: str = Field(max_length=100)

    thresholds: List["WeatherThreshold"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    alerts: List["Alert"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def __repr__(self) -> str:
        return f"<Location(name='{self.name}', branch='{self.branch}')>"


class WeatherThreshold(SQLModel, table=True):
    """Defines an alert condition for a Location.

    Examples:
        - parameter="TTT_C",  operator="<", value=5.0  → frost warning
        - parameter="FX_KMH", operator=">", value=60.0 → storm warning
    """

    __tablename__ = "thresholds"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    parameter: str = Field(max_length=30)     # "TTT_C", "FX_KMH", "RRR_MM", …
    operator: str = Field(max_length=5)       # "<", ">", "<=", ">="
    value: float
    label: str = Field(max_length=100)        # "Frost (Beton)", "Sturm", …
    severity: str = Field(default="warning", max_length=20)  # "info", "warning", "critical"

    location: Optional["Location"] = Relationship(back_populates="thresholds")

    def is_exceeded(self, actual_value: float) -> bool:
        """Encapsulation: threshold comparison logic lives here, not in the caller."""
        ops = {
            "<":  lambda a, b: a < b,
            ">":  lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        compare = ops.get(self.operator)
        if compare is None:
            raise ValueError(f"Unknown operator: {self.operator}")
        return compare(actual_value, self.value)

    def __repr__(self) -> str:
        return f"<WeatherThreshold('{self.label}': {self.parameter} {self.operator} {self.value})>"


class Alert(SQLModel, table=True):
    """A triggered weather warning linked to a Location."""

    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    threshold_label: str = Field(max_length=100)
    severity: str = Field(max_length=20)
    parameter: str = Field(max_length=30)
    actual_value: float
    threshold_value: float
    forecast_time: datetime
    created_at: datetime = Field(default_factory=datetime.now)

    location: Optional["Location"] = Relationship(back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert('{self.threshold_label}', severity='{self.severity}')>"

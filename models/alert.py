from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.location import Location


class Alert(SQLModel, table=True):
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
        return f"<Alert('{self.threshold_label}' at {self.location_id}, severity='{self.severity}')>"

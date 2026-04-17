from typing import List, Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.threshold import WeatherThreshold
    from models.alert import Alert


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    latitude: float
    longitude: float
    branch: str = Field(max_length=50)       # z.B. "Bau", "Event", "Lieferdienst"
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
        return f"<Location(name='{self.name}', branch='{self.branch}', company='{self.company}')>"

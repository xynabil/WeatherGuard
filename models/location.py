from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)  # z.B. "Bau", "Event", "Lieferdienst"
    company: Mapped[str] = mapped_column(String(100), nullable=False)

    thresholds = relationship("WeatherThreshold", back_populates="location", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Location(name='{self.name}', branch='{self.branch}', company='{self.company}')>"

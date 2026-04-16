from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class WeatherThreshold(Base):
    """Definiert einen Grenzwert für einen Standort.

    Beispiele:
        - parameter="TTT_C", operator="<", value=5.0  → Frostwarnung
        - parameter="FX_KMH", operator=">", value=40.0  → Sturmwarnung
        - parameter="RRR_MM", operator=">", value=10.0  → Starkregen
    """
    __tablename__ = "thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(30), nullable=False)   # z.B. "TTT_C", "FX_KMH", "RRR_MM"
    operator: Mapped[str] = mapped_column(String(5), nullable=False)     # "<", ">", "<=", ">="
    value: Mapped[float] = mapped_column(Float, nullable=False)          # Grenzwert
    label: Mapped[str] = mapped_column(String(100), nullable=False)      # z.B. "Frost (Beton)", "Sturm"
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")  # "info", "warning", "critical"

    location = relationship("Location", back_populates="thresholds")

    def is_exceeded(self, actual_value: float) -> bool:
        ops = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        compare = ops.get(self.operator)
        if compare is None:
            raise ValueError(f"Unbekannter Operator: {self.operator}")
        return compare(actual_value, self.value)

    def __repr__(self) -> str:
        return f"<Threshold('{self.label}': {self.parameter} {self.operator} {self.value})>"

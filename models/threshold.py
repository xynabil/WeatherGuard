from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.location import Location


class WeatherThreshold(SQLModel, table=True):
    """Definiert einen Grenzwert für einen Standort.

    Beispiele:
        - parameter="TTT_C", operator="<", value=5.0  → Frostwarnung
        - parameter="FX_KMH", operator=">", value=40.0 → Sturmwarnung
        - parameter="RRR_MM", operator=">", value=10.0 → Starkregen
    """
    __tablename__ = "thresholds"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id")
    parameter: str = Field(max_length=30)          # z.B. "TTT_C", "FX_KMH", "RRR_MM"
    operator: str = Field(max_length=5)            # "<", ">", "<=", ">="
    value: float                                   # Grenzwert
    label: str = Field(max_length=100)             # z.B. "Frost (Beton)", "Sturm"
    severity: str = Field(default="warning", max_length=20)  # "info", "warning", "critical"

    location: Optional["Location"] = Relationship(back_populates="thresholds")

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

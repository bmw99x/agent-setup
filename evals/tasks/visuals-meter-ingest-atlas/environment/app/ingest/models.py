from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Reading:
    meter_id: str
    site: str
    taken_at: datetime
    kwh: float
    temperature_c: float | None = None


@dataclass(frozen=True)
class Rejected:
    line: str
    reason: str

from dataclasses import dataclass
from datetime import date


@dataclass
class Application:
    company: str
    position: str
    status: str
    applied_date: date
    deadline: date | None = None
    notes: str = ""
    id: int | None = None

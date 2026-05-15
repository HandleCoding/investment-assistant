from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FundNavBar:
    nav_date: date
    unit_nav: float | None
    accumulated_nav: float | None
    daily_return: float | None = None

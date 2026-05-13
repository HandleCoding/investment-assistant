from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PriceBar:
    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    pct_change: float | None = None

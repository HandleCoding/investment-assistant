from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class TradeOrder:
    symbol: str
    market: str
    action: str
    quantity: float
    price: float
    trade_date: date
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PositionTracker:
    symbol: str
    market: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    trade_date: date
    days_held: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MonthlyReturnTracker:
    month: str
    starting_value: float
    current_value: float
    monthly_pnl: float
    monthly_return: float
    target_return: float
    target_met: bool
    positions: list[PositionTracker]
    trades_this_month: list[TradeOrder]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class PortfolioPositionInput:
    symbol: str
    market: str
    asset_type: str
    name: str | None
    quantity: float
    cost_price: float
    last_price: float | None = None
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    opened_at: date | None = None
    note: str | None = None


@dataclass(frozen=True)
class PortfolioPositionSnapshot:
    id: int
    symbol: str
    name: str | None
    market: str
    asset_type: str
    quantity: float
    cost_price: float
    last_price: float
    market_value: float
    cost_value: float
    pnl: float
    pnl_pct: float
    weight: float
    rule_status: str
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PortfolioSnapshot:
    total_market_value: float
    total_cost_value: float
    cash: float
    total_asset_value: float
    total_pnl: float
    total_pnl_pct: float
    positions: list[PortfolioPositionSnapshot]
    allocation: dict[str, float]
    alerts: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

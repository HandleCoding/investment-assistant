from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class BacktestRequest:
    symbol: str
    market: str = "A_SHARE"
    start_date: date | None = None
    end_date: date | None = None
    initial_cash: float = 100_000
    fast_window: int = 20
    slow_window: int = 60


@dataclass(frozen=True)
class BacktestTrade:
    trade_date: date
    action: str
    price: float
    quantity: float
    cash: float


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    market: str
    start_date: date
    end_date: date
    initial_cash: float
    final_value: float
    total_return: float
    max_drawdown: float
    trade_count: int
    win_rate: float
    trades: list[BacktestTrade]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

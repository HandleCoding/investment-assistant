from datetime import date

from pydantic import BaseModel, Field


class PortfolioPositionRequest(BaseModel):
    symbol: str
    market: str = "A_SHARE"
    asset_type: str = "STOCK"
    name: str | None = None
    quantity: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    last_price: float | None = Field(default=None, gt=0)
    stop_loss_price: float | None = Field(default=None, gt=0)
    take_profit_price: float | None = Field(default=None, gt=0)
    opened_at: date | None = None
    note: str | None = None


class CandidateGenerateRequest(BaseModel):
    markets: list[str] = Field(default_factory=lambda: ["A_SHARE", "HK"])
    symbols: list[str] = Field(default_factory=lambda: ["000001", "603288", "510300", "HK0700"])
    min_score: float = 40
    max_drawdown_floor: float = -0.35
    min_return_20d: float | None = None


class CandidateStatusRequest(BaseModel):
    status: str


class BacktestRunRequest(BaseModel):
    symbol: str
    market: str = "A_SHARE"
    start_date: date | None = None
    end_date: date | None = None
    initial_cash: float = Field(default=100_000, gt=0)
    fast_window: int = Field(default=20, gt=1)
    slow_window: int = Field(default=60, gt=2)


class SignalBacktestRunRequest(BaseModel):
    symbol: str
    market: str = "A_SHARE"
    strategy_name: str = "trend_momentum_quality"
    rebalance_days: int = Field(default=20, gt=0)
    holding_days: int = Field(default=20, gt=0)
    initial_cash: float = Field(default=100_000, gt=0)


class StrategyScanRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["000001", "603288", "510300"])
    market: str = "A_SHARE"
    strategy_name: str | None = None
    limit: int = Field(default=20, gt=0, le=100)


class OpportunityRankRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["000001", "603288", "510300"])
    market: str = "A_SHARE"
    max_positions: int = Field(default=5, gt=0, le=20)

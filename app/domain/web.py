from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MetricCard:
    title: str
    value: str
    change: str
    tone: str = "neutral"


@dataclass(frozen=True)
class AlertItem:
    title: str
    description: str
    tone: str = "warning"


@dataclass(frozen=True)
class CandidateItem:
    symbol: str
    name: str
    market: str
    score: int
    conclusion: str
    return_20d: str
    max_drawdown: str
    reason: str
    risk: str


@dataclass(frozen=True)
class PositionItem:
    symbol: str
    name: str
    market: str
    quantity: str
    cost_price: str
    last_price: str
    pnl: str
    weight: str
    rule_status: str


@dataclass(frozen=True)
class DashboardViewModel:
    market_cards: list[MetricCard]
    portfolio_cards: list[MetricCard]
    alerts: list[AlertItem]
    candidates: list[CandidateItem]

    def to_context(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CandidatePoolViewModel:
    candidates: list[CandidateItem]
    filters: list[str]

    def to_context(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PortfolioViewModel:
    summary_cards: list[MetricCard]
    positions: list[PositionItem]
    alerts: list[AlertItem]
    allocation: list[MetricCard]

    def to_context(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BacktestViewModel:
    default_symbol: str
    default_market: str
    default_initial_cash: str
    default_fast_window: int
    default_slow_window: int

    def to_context(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyViewModel:
    strategies: list[str]
    default_symbols: str

    def to_context(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DataManagementViewModel:
    summary_cards: list[MetricCard]
    coverage: list[dict[str, object]]

    def to_context(self) -> dict[str, object]:
        return asdict(self)

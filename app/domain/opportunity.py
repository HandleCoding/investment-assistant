from dataclasses import asdict, dataclass

from app.domain.strategy import StrategySignal


@dataclass(frozen=True)
class OpportunityRecommendation:
    symbol: str
    market: str
    score: float
    action: str
    position_size: float
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    expected_upside: float | None
    downside_risk: float | None
    holding_days: int
    thesis: list[str]
    risks: list[str]
    signals: list[StrategySignal]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityRankResult:
    target_monthly_return: float
    recommendations: list[OpportunityRecommendation]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

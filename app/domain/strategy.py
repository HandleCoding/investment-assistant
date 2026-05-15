from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StrategySignal:
    strategy: str
    symbol: str
    market: str
    score: float
    action: str
    confidence: str
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    holding_days: int
    reasons: list[str]
    risks: list[str]
    metrics: dict[str, float | int | str | None]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyRankResult:
    strategy: str
    signals: list[StrategySignal]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

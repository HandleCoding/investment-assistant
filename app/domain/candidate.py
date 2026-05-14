from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class CandidateRule:
    markets: list[str]
    symbols: list[str]
    min_score: float = 55
    max_drawdown_floor: float = -0.25
    min_return_20d: float | None = None


@dataclass(frozen=True)
class CandidateEntrySnapshot:
    id: int
    symbol: str
    name: str | None
    market: str
    score: float
    conclusion: str
    return_20d: float | None
    max_drawdown: float | None
    reason: str
    risk: str
    status: str
    generated_at: date

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CandidatePoolSnapshot:
    rule: CandidateRule
    entries: list[CandidateEntrySnapshot]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    max_score: float = 100
    raw_total: float | None = None
    raw_max_score: float | None = None
    fundamental: float = 0
    valuation: float = 0
    technical: float = 0
    momentum: float = 0
    risk: float = 0


@dataclass(frozen=True)
class AnalysisSummary:
    symbol: str
    score: ScoreBreakdown
    conclusion: str
    reasons: list[str]
    risks: list[str]
    metrics: dict[str, float | int | str | None]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

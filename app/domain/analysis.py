from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
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

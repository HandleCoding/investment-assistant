from app.domain.analysis import AnalysisSummary
from app.services.scoring_service import ScoringService


class AnalysisService:
    def __init__(self, scoring_service: ScoringService | None = None) -> None:
        self.scoring_service = scoring_service or ScoringService()

    def analyze(self, symbol: str) -> AnalysisSummary:
        return self.scoring_service.placeholder_summary(symbol)

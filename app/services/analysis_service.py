from sqlalchemy.orm import Session

from app.domain.analysis import AnalysisSummary
from app.services.price_service import PriceService
from app.services.scoring_service import ScoringService


class AnalysisService:
    def __init__(
        self,
        session: Session,
        price_service: PriceService | None = None,
        scoring_service: ScoringService | None = None,
    ) -> None:
        self.price_service = price_service or PriceService(session)
        self.scoring_service = scoring_service or ScoringService()

    def analyze_a_share(self, symbol: str) -> AnalysisSummary:
        prices = self.price_service.get_a_share_history(symbol=symbol)
        return self.scoring_service.score_a_share(symbol, prices)

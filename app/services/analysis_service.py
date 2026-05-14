from sqlalchemy.orm import Session

from app.domain.analysis import AnalysisSummary
from app.services.price_service import PriceService, normalize_hk_symbol
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

    def analyze_hk_stock(self, symbol: str) -> AnalysisSummary:
        normalized_symbol = normalize_hk_symbol(symbol)
        prices = self.price_service.get_hk_stock_history(symbol=normalized_symbol)
        return self.scoring_service.score_a_share(normalized_symbol, prices)

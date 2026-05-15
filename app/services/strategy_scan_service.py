from sqlalchemy.orm import Session

from app.database.models import Market
from app.domain.strategy import StrategyRankResult, StrategySignal
from app.services.price_service import PriceService
from app.strategies.modules import StrategyModule, default_strategy_modules


class StrategyScanService:
    def __init__(
        self,
        session: Session,
        price_service: PriceService | None = None,
        strategies: list[StrategyModule] | None = None,
    ):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.strategies = strategies or default_strategy_modules()

    def scan(
        self,
        symbols: list[str],
        market: str = Market.A_SHARE.value,
        strategy_name: str | None = None,
        limit: int = 20,
    ) -> StrategyRankResult:
        strategies = [
            strategy
            for strategy in self.strategies
            if strategy_name is None or strategy.name == strategy_name
        ]
        signals: list[StrategySignal] = []
        for symbol in symbols:
            prices = self._load_prices(symbol, market)
            for strategy in strategies:
                try:
                    signals.append(strategy.evaluate(symbol, market, prices))
                except ValueError:
                    continue
        signals.sort(key=lambda item: item.score, reverse=True)
        return StrategyRankResult(
            strategy=strategy_name or "multi_strategy",
            signals=signals[:limit],
        )

    def _load_prices(self, symbol: str, market: str):
        if market == Market.HK.value:
            return self.price_service.get_hk_stock_history(symbol)
        if market == Market.FUND.value:
            return self.price_service.get_fund_nav_history(symbol)
        return self.price_service.get_a_share_history(symbol)

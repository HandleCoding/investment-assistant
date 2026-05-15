from sqlalchemy.orm import Session

from app.database.models import AssetType, Market
from app.domain.candidate import CandidateEntrySnapshot, CandidatePoolSnapshot, CandidateRule
from app.domain.errors import DataSourceError, NoMarketDataError
from app.repositories.assets import AssetRepository
from app.repositories.candidates import CandidateRepository, today
from app.services.analysis_service import AnalysisService
from app.services.price_service import normalize_hk_symbol
from app.services.strategy_scan_service import StrategyScanService


class CandidatePoolService:
    def __init__(self, session: Session, analysis_service: AnalysisService | None = None):
        self.session = session
        self.assets = AssetRepository(session)
        self.candidates = CandidateRepository(session)
        self.analysis_service = analysis_service or AnalysisService(session)
        self.strategy_scan_service = StrategyScanService(session)

    def generate(self, rule: CandidateRule | None = None) -> CandidatePoolSnapshot:
        rule = rule or CandidateRule(
            markets=[Market.A_SHARE.value, Market.HK.value],
            symbols=["000001", "603288", "510300", "HK0700"],
            min_score=40,
            max_drawdown_floor=-0.35,
        )
        generated_at = today()
        entries = []
        for market in rule.markets or [Market.A_SHARE.value]:
            market_symbols = [
                symbol
                for symbol in rule.symbols
                if self._market_for_symbol(symbol, rule.markets) == market
            ]
            if not market_symbols:
                continue
            try:
                result = self.strategy_scan_service.scan(
                    market_symbols,
                    market=market,
                    limit=len(market_symbols) * 4,
                )
            except (DataSourceError, NoMarketDataError):
                continue
            for signal in result.signals:
                if not self._passes_rule(signal.metrics, signal.score, rule):
                    continue
                symbol = (
                    normalize_hk_symbol(signal.symbol)
                    if market == Market.HK.value
                    else signal.symbol
                )
                asset = self.assets.get_or_create(
                    symbol,
                    market,
                    AssetType.STOCK.value,
                    name=symbol,
                )
                entry = self.candidates.upsert_from_signal(asset.id, generated_at, signal)
                entries.append(self._to_snapshot(entry))

        self.session.commit()
        if not entries:
            entries = self.list_latest().entries
        return CandidatePoolSnapshot(rule=rule, entries=entries)

    def list_latest(self, limit: int = 50) -> CandidatePoolSnapshot:
        rule = CandidateRule(markets=[], symbols=[])
        entries = [self._to_snapshot(entry) for entry in self.candidates.list_latest(limit)]
        return CandidatePoolSnapshot(rule=rule, entries=entries)

    def update_status(self, entry_id: int, status: str) -> CandidateEntrySnapshot:
        entry = self.candidates.update_status(entry_id, status)
        self.session.commit()
        return self._to_snapshot(entry)

    def _analyze(self, symbol: str, markets: list[str]):
        market = self._market_for_symbol(symbol, markets)
        if market == Market.HK.value:
            return self.analysis_service.analyze_hk_stock(symbol)
        return self.analysis_service.analyze_a_share(symbol)

    def _market_for_symbol(self, symbol: str, markets: list[str]) -> str:
        if symbol.upper().startswith("HK") and Market.HK.value in markets:
            return Market.HK.value
        return Market.A_SHARE.value

    def _passes_rule(self, metrics: dict[str, object], score: float, rule: CandidateRule) -> bool:
        max_drawdown = float(metrics.get("max_drawdown") or 0)
        return_20d = metrics.get("return_20d")
        if score < rule.min_score:
            return False
        if max_drawdown < rule.max_drawdown_floor:
            return False
        if rule.min_return_20d is not None and float(return_20d or 0) < rule.min_return_20d:
            return False
        return True

    def _to_snapshot(self, entry) -> CandidateEntrySnapshot:
        return CandidateEntrySnapshot(
            id=entry.id,
            symbol=entry.asset.symbol,
            name=entry.asset.name,
            market=entry.asset.market,
            score=round(entry.score, 2),
            conclusion=entry.conclusion,
            return_20d=entry.return_20d,
            max_drawdown=entry.max_drawdown,
            reason=entry.reason or "暂无明确入池理由",
            risk=entry.risk or "暂无明显风险",
            status=entry.status,
            generated_at=entry.generated_at,
        )

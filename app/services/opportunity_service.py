from sqlalchemy.orm import Session

from app.database.models import Market
from app.domain.opportunity import OpportunityRankResult, OpportunityRecommendation
from app.domain.strategy import StrategySignal
from app.services.price_service import PriceService
from app.services.strategy_scan_service import StrategyScanService


class OpportunityService:
    def __init__(
        self,
        session: Session,
        price_service: PriceService | None = None,
        target_monthly_return: float = 0.10,
    ):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.scanner = StrategyScanService(session, self.price_service)
        self.target_monthly_return = target_monthly_return

    def rank(
        self,
        symbols: list[str],
        market: str = Market.A_SHARE.value,
        max_positions: int = 5,
    ) -> OpportunityRankResult:
        result = self.scanner.scan(symbols, market=market, limit=len(symbols) * 4)
        grouped = self._group_by_symbol(result.signals)
        recommendations = []
        for symbol, signals in grouped.items():
            rec = self._build_recommendation(symbol, market, signals, max_positions)
            recommendations.append(rec)
        recommendations.sort(key=lambda item: item.score, reverse=True)
        recommendations = recommendations[:max_positions]
        return OpportunityRankResult(
            target_monthly_return=self.target_monthly_return,
            recommendations=recommendations,
            warnings=self._warnings(recommendations),
        )

    def _group_by_symbol(self, signals: list[StrategySignal]) -> dict[str, list[StrategySignal]]:
        grouped: dict[str, list[StrategySignal]] = {}
        for signal in signals:
            grouped.setdefault(signal.symbol, []).append(signal)
        return grouped

    def _build_recommendation(
        self,
        symbol: str,
        market: str,
        signals: list[StrategySignal],
        max_positions: int,
    ) -> OpportunityRecommendation:
        score = self._combined_score(signals)
        entry = signals[0].entry
        stop_loss = min(signal.stop_loss or 0 for signal in signals) or entry
        take_profit = max(signal.take_profit or 0 for signal in signals) or entry
        expected_upside = (take_profit - entry) / entry if entry else None
        downside_risk = (entry - stop_loss) / entry if entry else None
        position_size = self._position_size(score, max_positions, downside_risk)
        all_reasons = [f"[{s.strategy}] {r}" for s in signals for r in s.reasons]
        all_risks = list({r for s in signals for r in s.risks})
        action = "强关注" if score >= 75 else "可观察" if score >= 55 else "暂不考虑"
        holding = max(signal.holding_days for signal in signals) if signals else 20
        return OpportunityRecommendation(
            symbol=symbol,
            market=market,
            score=score,
            action=action,
            position_size=position_size,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            expected_upside=expected_upside,
            downside_risk=downside_risk,
            holding_days=holding,
            thesis=all_reasons[:5],
            risks=all_risks[:5],
            signals=signals,
        )

    def _combined_score(self, signals: list[StrategySignal]) -> float:
        if not signals:
            return 0
        weight_sum = sum(signal.score for signal in signals)
        return round(weight_sum / len(signals), 2)

    def _position_size(
        self,
        score: float,
        max_positions: int,
        downside_risk: float | None,
    ) -> float:
        base = 1.0 / max_positions
        if score >= 75:
            base *= 1.3
        elif score < 55:
            base *= 0.5
        if downside_risk is not None and downside_risk > 0.10:
            base *= 0.8
        return round(min(base, 0.30), 4)

    def _warnings(self, recs: list[OpportunityRecommendation]) -> list[str]:
        warnings = []
        if not recs:
            warnings.append("当前候选池无符合条件的机会。")
            return warnings
        best = recs[0]
        if best.expected_upside is not None and best.expected_upside < self.target_monthly_return:
            warnings.append(
                f"最高候选预期上行 {best.expected_upside * 100:.1f}% 低于月度目标 "
                f"{self.target_monthly_return * 100:.0f}%，需考虑更高弹性品种或杠杆。"
            )
        if any(rec.downside_risk and rec.downside_risk > 0.12 for rec in recs):
            warnings.append("部分候选下行风险超过 12%，建议配合严格止损。")
        high_corr_markets = {rec.market for rec in recs}
        if len(high_corr_markets) == 1 and len(recs) > 1:
            warnings.append("候选资产高度集中在同一市场，分散不足。")
        return warnings

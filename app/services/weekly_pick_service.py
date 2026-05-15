from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.backtest import SignalBacktestRequest
from app.domain.errors import DataSourceError, NoMarketDataError
from app.domain.opportunity import OpportunityRankResult, OpportunityRecommendation
from app.domain.weekly_pick import WeeklyPick
from app.services.backtest_service import BacktestService
from app.services.opportunity_service import OpportunityService
from app.services.price_service import PriceService

HIGH_ELASTICITY_A_SHARE = [
    "002475",
    "300750",
    "600519",
    "000858",
    "002594",
    "300059",
    "601012",
    "000001",
    "603288",
    "510300",
]

POPULAR_FUNDS = [
    "110011",
    "161725",
    "519736",
    "005827",
]


def _action_for_score(score: float) -> str:
    if score >= 70:
        return "强关注"
    if score >= 50:
        return "可观察"
    if score < 35:
        return "暂不考虑"
    return "观察"


class WeeklyPickService:
    def __init__(
        self,
        session: Session,
        price_service: PriceService | None = None,
        target_monthly_return: float = 0.10,
    ):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.opportunity = OpportunityService(
            session,
            self.price_service,
            target_monthly_return=target_monthly_return,
        )
        self.backtest = BacktestService(session, self.price_service)

    def generate(self) -> WeeklyPick:
        stock_result = self._safe_rank_stocks()

        fund_recommendations = []
        for symbol in POPULAR_FUNDS:
            try:
                fund_result = self.opportunity.rank(
                    [symbol],
                    market="FUND",
                    max_positions=1,
                )
                fund_recommendations.extend(fund_result.recommendations)
            except Exception:
                continue

        all_recs = stock_result.recommendations + fund_recommendations
        all_recs.sort(key=lambda item: item.score, reverse=True)
        top_picks = all_recs[:5]

        backtest_summary, boosted_picks = self._backtest_and_boost(top_picks)
        all_warnings = list(stock_result.warnings)
        if not any("基金" in w for w in all_warnings) and not fund_recommendations:
            all_warnings.append("基金净值数据暂时无法获取，仅基于股票候选推荐。")
        self._add_target_warnings(boosted_picks, all_warnings)

        return WeeklyPick(
            pick_date=datetime.now(UTC).date(),
            target_monthly_return=self.opportunity.target_monthly_return,
            picks=boosted_picks,
            warnings=all_warnings,
            backtest_summary=backtest_summary,
        )

    def _safe_rank_stocks(self) -> OpportunityRankResult:
        available = []
        for symbol in HIGH_ELASTICITY_A_SHARE:
            try:
                self.price_service.get_a_share_history(symbol, lookback_days=150)
                available.append(symbol)
            except (DataSourceError, NoMarketDataError, Exception):
                continue
        if not available:
            return OpportunityRankResult(
                target_monthly_return=self.opportunity.target_monthly_return,
                recommendations=[],
                warnings=["所有候选股票数据源暂时不可用，请稍后重试。"],
            )
        return self.opportunity.rank(available, market="A_SHARE", max_positions=5)

    def _backtest_and_boost(self, picks: list) -> tuple[str, list[OpportunityRecommendation]]:
        results = []
        boosted = []
        for rec in picks[:5]:
            best_strategy = "trend_momentum_quality"
            if rec.signals:
                best_strategy = max(rec.signals, key=lambda s: s.score).strategy
            try:
                result = self.backtest.run_signal_holding_period(
                    SignalBacktestRequest(
                        symbol=rec.symbol,
                        market=rec.market,
                        strategy_name=best_strategy,
                        rebalance_days=20,
                        holding_days=20,
                        initial_cash=100_000,
                    )
                )
                boost = 0
                if result.total_return >= 0.10:
                    boost += 25
                elif result.total_return >= 0.05:
                    boost += 15
                elif result.total_return > 0:
                    boost += 5
                if result.win_rate >= 0.55:
                    boost += 10
                if boost > 0:
                    rec = OpportunityRecommendation(
                        symbol=rec.symbol,
                        market=rec.market,
                        score=round(min(100, rec.score + boost), 2),
                        action=_action_for_score(round(min(100, rec.score + boost), 2)),
                        position_size=rec.position_size,
                        entry=rec.entry,
                        stop_loss=rec.stop_loss,
                        take_profit=rec.take_profit,
                        expected_upside=rec.expected_upside,
                        downside_risk=rec.downside_risk,
                        holding_days=rec.holding_days,
                        thesis=rec.thesis
                        + [
                            f"回测验证: 总收益 {result.total_return * 100:.1f}%, "
                            f"胜率 {result.win_rate * 100:.0f}%"
                        ],
                        risks=rec.risks,
                        signals=rec.signals,
                    )
                results.append(
                    f"{rec.symbol}: 总收益 {result.total_return * 100:.1f}%, "
                    f"胜率 {result.win_rate * 100:.0f}%, "
                    f"最大回撤 {result.max_drawdown * 100:.1f}%, "
                    f"交易 {result.trade_count} 次"
                )
            except Exception:
                results.append(f"{rec.symbol}: 回测数据不足")
            boosted.append(rec)
        return " | ".join(results) if results else "无可用回测结果", boosted

    def _add_target_warnings(self, picks: list, warnings: list[str]) -> None:
        achieved = any(
            "总收益" in t and any(f"{v}%" in t for v in range(10, 100))
            for p in picks
            for t in p.thesis
        )
        if achieved:
            warnings.append("回测显示部分基金策略信号可达月度 10% 目标，但历史表现不代表未来。")
        else:
            warnings.append(
                "当前候选回测收益未达月度 10%，建议等待更明确的趋势信号或扩大候选池。"
            )

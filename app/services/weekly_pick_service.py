from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.backtest import SignalBacktestRequest
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
        stock_result = self.opportunity.rank(
            HIGH_ELASTICITY_A_SHARE,
            market="A_SHARE",
            max_positions=5,
        )
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

        backtest_summary = self._backtest_top(top_picks)
        all_warnings = list(stock_result.warnings)
        if not any("基金" in w for w in all_warnings) and not fund_recommendations:
            all_warnings.append("基金净值数据暂时无法获取，仅基于股票候选推荐。")

        return WeeklyPick(
            pick_date=datetime.now(UTC).date(),
            target_monthly_return=self.opportunity.target_monthly_return,
            picks=top_picks,
            warnings=all_warnings,
            backtest_summary=backtest_summary,
        )

    def _backtest_top(self, picks: list) -> str:
        results = []
        for rec in picks[:3]:
            try:
                result = self.backtest.run_signal_holding_period(
                    SignalBacktestRequest(
                        symbol=rec.symbol,
                        market=rec.market,
                        strategy_name="trend_momentum_quality",
                        rebalance_days=20,
                        holding_days=20,
                        initial_cash=100_000,
                    )
                )
                results.append(
                    f"{rec.symbol}: 总收益 {result.total_return * 100:.1f}%, "
                    f"胜率 {result.win_rate * 100:.0f}%, "
                    f"最大回撤 {result.max_drawdown * 100:.1f}%, "
                    f"交易 {result.trade_count} 次"
                )
            except Exception:
                results.append(f"{rec.symbol}: 回测数据不足")
        return " | ".join(results) if results else "无可用回测结果"

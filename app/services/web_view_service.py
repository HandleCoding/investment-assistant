from sqlalchemy.orm import Session

from app.domain.candidate import CandidateEntrySnapshot
from app.domain.portfolio import PortfolioPositionSnapshot, PortfolioSnapshot
from app.domain.web import (
    AlertItem,
    BacktestViewModel,
    CandidateItem,
    CandidatePoolViewModel,
    DashboardViewModel,
    DataManagementViewModel,
    MetricCard,
    PortfolioViewModel,
    PositionItem,
    StrategyViewModel,
)
from app.services.candidate_service import CandidatePoolService
from app.services.data_management_service import DataManagementService
from app.services.portfolio_service import PortfolioService
from app.services.weekly_pick_service import WeeklyPickService
from app.strategies.modules import default_strategy_modules


class DashboardViewService:
    def __init__(self, session: Session):
        self.candidates = CandidatePoolService(session)
        self.portfolio = PortfolioService(session)

    def build(self) -> DashboardViewModel:
        portfolio = self.portfolio.snapshot()
        candidates = self.candidates.list_latest(limit=8).entries
        pick_summary = ""
        pick_warnings: list[str] = []
        try:
            pick = WeeklyPickService(self.candidates.session).generate()
            pick_summary = pick.backtest_summary
            pick_warnings = pick.warnings
        except Exception:
            pick_summary = "本周推荐生成需要行情数据支持"
        return DashboardViewModel(
            market_cards=[
                MetricCard("上证指数", "待接入", "行情源扩展", "neutral"),
                MetricCard("沪深300", "待接入", "行情源扩展", "neutral"),
                MetricCard("恒生指数", "待接入", "行情源扩展", "neutral"),
                MetricCard("候选资产", str(len(candidates)), "真实候选池", "positive"),
            ],
            portfolio_cards=_portfolio_summary_cards(portfolio),
            alerts=[AlertItem("组合纪律", item) for item in portfolio.alerts],
            candidates=[_candidate_item(item) for item in candidates],
            weekly_pick_summary=pick_summary,
            weekly_pick_warnings=pick_warnings,
        )


class CandidatePoolViewService:
    def __init__(self, session: Session):
        self.service = CandidatePoolService(session)

    def build(self) -> CandidatePoolViewModel:
        pool = self.service.list_latest()
        return CandidatePoolViewModel(
            filters=["A 股", "港股", "评分 40+", "回撤 > -35%", "真实分析生成"],
            candidates=[_candidate_item(item) for item in pool.entries],
        )


class PortfolioViewService:
    def __init__(self, session: Session):
        self.service = PortfolioService(session)

    def build(self) -> PortfolioViewModel:
        snapshot = self.service.snapshot()
        return PortfolioViewModel(
            summary_cards=_portfolio_summary_cards(snapshot),
            allocation=[
                MetricCard(key, _format_pct(value), "当前配置", "neutral")
                for key, value in snapshot.allocation.items()
            ] or [MetricCard("暂无持仓", "0%", "请先通过 API 录入", "neutral")],
            positions=[_position_item(item) for item in snapshot.positions],
            alerts=[AlertItem("风险提醒", item) for item in snapshot.alerts],
        )


class BacktestViewService:
    def build(self) -> BacktestViewModel:
        return BacktestViewModel(
            default_symbol="000001",
            default_market="A_SHARE",
            default_initial_cash="100000",
            default_fast_window=20,
            default_slow_window=60,
        )


class StrategyViewService:
    def build(self) -> StrategyViewModel:
        return StrategyViewModel(
            strategies=[strategy.name for strategy in default_strategy_modules()],
            default_symbols="000001,603288,510300,002475,300750,600519",
        )


class DataManagementViewService:
    def __init__(self, session: Session):
        self.service = DataManagementService(session)

    def build(self) -> DataManagementViewModel:
        snapshot = self.service.snapshot()
        return DataManagementViewModel(
            summary_cards=[
                MetricCard("资产数量", str(snapshot.asset_count), "assets", "neutral"),
                MetricCard("行情缓存", str(snapshot.price_bar_count), "price bars", "positive"),
                MetricCard("候选记录", str(snapshot.candidate_count), "candidates", "neutral"),
                MetricCard("回测次数", str(snapshot.backtest_count), "runs", "neutral"),
            ],
            coverage=[item.to_dict() for item in snapshot.coverage],
        )


def _portfolio_summary_cards(snapshot: PortfolioSnapshot) -> list[MetricCard]:
    tone = "positive" if snapshot.total_pnl >= 0 else "negative"
    return [
        MetricCard(
            "总资产",
            _format_money(snapshot.total_asset_value),
            _format_pct(snapshot.total_pnl_pct),
            tone,
        ),
        MetricCard("持仓市值", _format_money(snapshot.total_market_value), "OPEN", "neutral"),
        MetricCard(
            "浮动盈亏",
            _format_money(snapshot.total_pnl),
            _format_pct(snapshot.total_pnl_pct),
            tone,
        ),
        MetricCard("现金", _format_money(snapshot.cash), "可配置", "neutral"),
    ]


def _candidate_item(item: CandidateEntrySnapshot) -> CandidateItem:
    return CandidateItem(
        symbol=item.symbol,
        name=item.name or item.symbol,
        market=item.market,
        score=int(round(item.score)),
        conclusion=item.conclusion,
        return_20d=_format_pct(item.return_20d),
        max_drawdown=_format_pct(item.max_drawdown),
        reason=item.reason,
        risk=item.risk,
    )


def _position_item(item: PortfolioPositionSnapshot) -> PositionItem:
    return PositionItem(
        symbol=item.symbol,
        name=item.name or item.symbol,
        market=item.market,
        quantity=f"{item.quantity:,.0f}",
        cost_price=f"{item.cost_price:.2f}",
        last_price=f"{item.last_price:.2f}",
        pnl=_format_money(item.pnl),
        weight=_format_pct(item.weight),
        rule_status=item.rule_status,
    )


def _format_money(value: float) -> str:
    return f"{value:,.2f}"


def _format_pct(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{value * 100:+.2f}%"

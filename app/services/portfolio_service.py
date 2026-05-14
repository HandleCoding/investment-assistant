from sqlalchemy.orm import Session

from app.domain.portfolio import (
    PortfolioPositionInput,
    PortfolioPositionSnapshot,
    PortfolioSnapshot,
)
from app.repositories.assets import AssetRepository, normalize_asset_type, normalize_market
from app.repositories.portfolio import PortfolioRepository


class PortfolioService:
    def __init__(self, session: Session):
        self.session = session
        self.assets = AssetRepository(session)
        self.positions = PortfolioRepository(session)

    def upsert_position(self, data: PortfolioPositionInput) -> PortfolioPositionSnapshot:
        market = normalize_market(data.market)
        asset_type = normalize_asset_type(data.asset_type)
        asset = self.assets.get_or_create(data.symbol, market, asset_type, data.name)
        position = self.positions.upsert_position(asset.id, data)
        self.session.commit()
        return self._position_snapshot(position, total_value=self._position_value(position))

    def snapshot(self, cash: float = 0) -> PortfolioSnapshot:
        positions = self.positions.list_open_positions()
        total_market_value = sum(self._position_value(position) for position in positions)
        total_cost_value = sum(position.quantity * position.cost_price for position in positions)
        total_asset_value = total_market_value + cash
        snapshots = [
            self._position_snapshot(position, total_asset_value or total_market_value or 1)
            for position in positions
        ]
        allocation = self._allocation(snapshots, total_market_value)
        total_pnl = total_market_value - total_cost_value
        total_pnl_pct = total_pnl / total_cost_value if total_cost_value else 0
        return PortfolioSnapshot(
            total_market_value=round(total_market_value, 2),
            total_cost_value=round(total_cost_value, 2),
            cash=round(cash, 2),
            total_asset_value=round(total_asset_value, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 4),
            positions=snapshots,
            allocation=allocation,
            alerts=self._alerts(snapshots),
        )

    def close_position(self, position_id: int) -> PortfolioSnapshot:
        self.positions.close_position(position_id)
        self.session.commit()
        return self.snapshot()

    def _position_snapshot(self, position, total_value: float) -> PortfolioPositionSnapshot:
        last_price = position.last_price or position.cost_price
        market_value = position.quantity * last_price
        cost_value = position.quantity * position.cost_price
        pnl = market_value - cost_value
        pnl_pct = pnl / cost_value if cost_value else 0
        weight = market_value / total_value if total_value else 0
        return PortfolioPositionSnapshot(
            id=position.id,
            symbol=position.asset.symbol,
            name=position.asset.name,
            market=position.asset.market,
            asset_type=position.asset.asset_type,
            quantity=position.quantity,
            cost_price=position.cost_price,
            last_price=last_price,
            market_value=round(market_value, 2),
            cost_value=round(cost_value, 2),
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 4),
            weight=round(weight, 4),
            rule_status=self._rule_status(position, last_price),
            stop_loss_price=position.stop_loss_price,
            take_profit_price=position.take_profit_price,
            note=position.note,
        )

    def _position_value(self, position) -> float:
        return position.quantity * (position.last_price or position.cost_price)

    def _allocation(
        self,
        snapshots: list[PortfolioPositionSnapshot],
        total_market_value: float,
    ) -> dict[str, float]:
        if not total_market_value:
            return {}
        result: dict[str, float] = {}
        for item in snapshots:
            result[item.asset_type] = result.get(item.asset_type, 0) + item.market_value
        return {key: round(value / total_market_value, 4) for key, value in result.items()}

    def _alerts(self, snapshots: list[PortfolioPositionSnapshot]) -> list[str]:
        alerts = []
        if any(item.weight > 0.35 for item in snapshots):
            alerts.append("单一持仓仓位超过 35%，建议复核集中度风险。")
        if any(item.rule_status == "触发止损" for item in snapshots):
            alerts.append("有持仓触发止损线，请优先复盘买入理由。")
        if not alerts:
            alerts.append("当前组合未触发主要纪律提醒。")
        return alerts

    def _rule_status(self, position, last_price: float) -> str:
        if position.stop_loss_price is not None and last_price <= position.stop_loss_price:
            return "触发止损"
        if position.take_profit_price is not None and last_price >= position.take_profit_price:
            return "达到止盈"
        return "正常"

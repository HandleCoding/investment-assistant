from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.database.models import Market, PortfolioPosition
from app.domain.errors import DataSourceError, NoMarketDataError
from app.domain.trade import MonthlyReturnTracker, PositionTracker, TradeOrder
from app.repositories.assets import AssetRepository
from app.repositories.trades import TradeRepository
from app.services.price_service import PriceService


class TradeService:
    def __init__(self, session: Session, price_service: PriceService | None = None):
        self.session = session
        self.price_service = price_service or PriceService(session)
        self.assets = AssetRepository(session)
        self.trades = TradeRepository(session)

    def execute_buy(self, order: TradeOrder) -> PositionTracker:
        market = _market_key(order.market)
        asset = self.assets.get_or_create(order.symbol, market, "STOCK", order.symbol)
        self.trades.record(
            asset_id=asset.id,
            action="BUY",
            quantity=order.quantity,
            price=order.price,
            trade_date=order.trade_date,
            reason=order.reason,
        )
        position = self._upsert_position(asset.id, order.quantity, order.price, order.trade_date)
        self.session.commit()
        return self._track_position(position)

    def execute_sell(self, order: TradeOrder) -> PositionTracker:
        market = _market_key(order.market)
        asset = self.assets.get_or_create(order.symbol, market, "STOCK", order.symbol)
        self.trades.record(
            asset_id=asset.id,
            action="SELL",
            quantity=order.quantity,
            price=order.price,
            trade_date=order.trade_date,
            reason=order.reason,
        )
        position = self.session.get(PortfolioPosition, asset.id)
        if position and position.status == "OPEN":
            position.quantity -= order.quantity
            if position.quantity <= 0:
                position.status = "CLOSED"
            position.updated_at = datetime.now(UTC)
        self.session.commit()
        return self._track_position(position) if position and position.status == "OPEN" else None

    def refresh_prices(self) -> list[PositionTracker]:
        positions = (
            self.session.query(PortfolioPosition)
            .filter(PortfolioPosition.status == "OPEN")
            .all()
        )
        trackers = []
        for position in positions:
            try:
                latest = self._fetch_latest_price(position)
                if latest:
                    position.last_price = latest
                    position.updated_at = datetime.now(UTC)
            except (DataSourceError, NoMarketDataError, Exception):
                pass
            trackers.append(self._track_position(position))
        self.session.commit()
        return trackers

    def monthly_return(self, cash: float = 0, target: float = 0.10) -> MonthlyReturnTracker:
        now = datetime.now(UTC)
        year, month = now.year, now.month
        positions = self.refresh_prices()
        current_value = sum(p.market_value for p in positions) + cash
        month_trades = self.trades.list_by_month(year, month)
        starting = current_value - sum(p.unrealized_pnl for p in positions)
        monthly_pnl = current_value - starting if starting else 0
        monthly_return = monthly_pnl / starting if starting else 0
        return MonthlyReturnTracker(
            month=f"{year}-{month:02d}",
            starting_value=round(starting, 2),
            current_value=round(current_value, 2),
            monthly_pnl=round(monthly_pnl, 2),
            monthly_return=round(monthly_return, 4),
            target_return=target,
            target_met=monthly_return >= target,
            positions=positions,
            trades_this_month=[
                TradeOrder(
                    symbol=t.asset.symbol,
                    market=t.asset.market,
                    action=t.action,
                    quantity=t.quantity,
                    price=t.price,
                    trade_date=t.trade_date,
                    reason=t.reason,
                )
                for t in month_trades
            ],
        )

    def _upsert_position(self, asset_id: int, quantity: float, price: float, opened_at: date):
        from sqlalchemy import select
        position = self.session.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.asset_id == asset_id,
                PortfolioPosition.status == "OPEN",
            )
        )
        if position is None:
            position = PortfolioPosition(asset_id=asset_id, status="OPEN")
            self.session.add(position)
            position.quantity = quantity
            position.cost_price = price
            position.last_price = price
            position.opened_at = opened_at
        else:
            total_cost = position.cost_price * position.quantity + price * quantity
            position.quantity += quantity
            position.cost_price = total_cost / position.quantity if position.quantity else price
            position.last_price = price
        position.updated_at = datetime.now(UTC)
        self.session.flush()
        return position

    def _track_position(self, position) -> PositionTracker:
        last_price = position.last_price or position.cost_price
        market_value = position.quantity * last_price
        cost_value = position.quantity * position.cost_price
        unrealized_pnl = market_value - cost_value
        unrealized_pnl_pct = unrealized_pnl / cost_value if cost_value else 0
        today = datetime.now(UTC).date()
        days_held = (today - position.opened_at).days if position.opened_at else 0
        return PositionTracker(
            symbol=position.asset.symbol,
            market=position.asset.market,
            quantity=position.quantity,
            avg_cost=round(position.cost_price, 4),
            current_price=last_price,
            market_value=round(market_value, 2),
            cost_value=round(cost_value, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            unrealized_pnl_pct=round(unrealized_pnl_pct, 4),
            trade_date=today,
            days_held=days_held,
        )

    def _fetch_latest_price(self, position) -> float | None:
        symbol = position.asset.symbol
        market = position.asset.market
        try:
            if market == Market.HK.value:
                df = self.price_service.get_hk_stock_history(symbol, lookback_days=5)
            elif market == Market.FUND.value:
                df = self.price_service.get_fund_nav_history(symbol, lookback_days=30)
            else:
                df = self.price_service.get_a_share_history(symbol, lookback_days=5)
            if not df.empty:
                return float(df.iloc[-1]["close"])
        except Exception:
            pass
        return None


def _market_key(market: str) -> str:
    return market.upper().replace("-", "_")

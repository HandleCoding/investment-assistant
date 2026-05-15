from datetime import date

from app.domain.trade import TradeOrder
from app.services.trade_service import TradeService


def test_trade_service_executes_buy(db_session) -> None:
    service = TradeService(db_session)
    tracker = service.execute_buy(TradeOrder(
        symbol="110011",
        market="FUND",
        action="BUY",
        quantity=1000,
        price=4.608,
        trade_date=date(2026, 5, 15),
        reason="回测验证 10.6% 收益",
    ))

    assert tracker.symbol == "110011"
    assert tracker.quantity == 1000
    assert tracker.avg_cost == 4.608
    assert tracker.unrealized_pnl == 0


def test_trade_service_tracks_monthly_return(db_session) -> None:
    service = TradeService(db_session)
    service.execute_buy(TradeOrder(
        symbol="110011",
        market="FUND",
        action="BUY",
        quantity=1000,
        price=4.608,
        trade_date=date(2026, 5, 15),
    ))
    result = service.monthly_return(cash=5000, target=0.10)

    assert result.month == "2026-05"
    assert len(result.positions) >= 1
    assert result.target_return == 0.10

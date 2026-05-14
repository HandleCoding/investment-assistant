from app.domain.portfolio import PortfolioPositionInput
from app.services.portfolio_service import PortfolioService


def test_portfolio_service_calculates_snapshot(db_session) -> None:
    service = PortfolioService(db_session)

    service.upsert_position(
        PortfolioPositionInput(
            symbol="000001",
            market="A_SHARE",
            asset_type="STOCK",
            name="平安银行",
            quantity=1000,
            cost_price=10,
            last_price=12,
            stop_loss_price=9,
        )
    )
    snapshot = service.snapshot(cash=1000)

    assert snapshot.total_market_value == 12000
    assert snapshot.total_cost_value == 10000
    assert snapshot.total_asset_value == 13000
    assert snapshot.total_pnl == 2000
    assert snapshot.positions[0].rule_status == "正常"
    assert snapshot.allocation == {"STOCK": 1.0}


def test_portfolio_service_flags_stop_loss(db_session) -> None:
    service = PortfolioService(db_session)

    service.upsert_position(
        PortfolioPositionInput(
            symbol="000001",
            market="A_SHARE",
            asset_type="STOCK",
            name="平安银行",
            quantity=1000,
            cost_price=10,
            last_price=8.8,
            stop_loss_price=9,
        )
    )
    snapshot = service.snapshot()

    assert snapshot.positions[0].rule_status == "触发止损"
    assert "有持仓触发止损线，请优先复盘买入理由。" in snapshot.alerts

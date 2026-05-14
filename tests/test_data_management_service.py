from datetime import date

from app.database.models import Asset, PriceDaily
from app.services.data_management_service import DataManagementService


def test_data_management_service_reports_counts_and_coverage(db_session) -> None:
    asset = Asset(symbol="000001", name="平安银行", market="A_SHARE", asset_type="STOCK")
    db_session.add(asset)
    db_session.flush()
    db_session.add(
        PriceDaily(
            asset_id=asset.id,
            trade_date=date(2026, 1, 2),
            open=10,
            high=11,
            low=9,
            close=10.5,
            volume=1000,
            amount=10000,
            turnover_rate=1,
            pct_change=0.01,
            adjust_type="qfq",
        )
    )
    db_session.commit()

    snapshot = DataManagementService(db_session).snapshot()

    assert snapshot.asset_count == 1
    assert snapshot.price_bar_count == 1
    assert snapshot.coverage[0].symbol == "000001"
    assert snapshot.coverage[0].price_count == 1

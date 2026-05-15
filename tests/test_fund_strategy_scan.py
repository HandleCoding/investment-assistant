from datetime import date, timedelta

import pandas as pd

from app.database.models import Market
from app.services.price_service import PriceService
from app.services.strategy_scan_service import StrategyScanService


class FakeFundDataClient:
    def fetch_open_fund_history(self, symbol: str):
        start = date.today() - timedelta(days=139)
        return pd.DataFrame(
            [
                {
                    "净值日期": start + timedelta(days=index),
                    "单位净值": 1 + index * 0.002,
                    "累计净值": 1 + index * 0.002,
                    "日增长率": 0.2,
                }
                for index in range(140)
            ]
        )


def test_strategy_scan_service_supports_funds(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeFundDataClient())
    service = StrategyScanService(db_session, price_service=price_service)

    result = service.scan(
        ["000001"],
        market=Market.FUND.value,
        strategy_name="trend_momentum_quality",
    )

    assert result.signals[0].market == "FUND"
    assert result.signals[0].score >= 40

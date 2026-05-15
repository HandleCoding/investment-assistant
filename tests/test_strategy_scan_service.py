from datetime import date, timedelta

import pandas as pd

from app.services.price_service import PriceService
from app.services.strategy_scan_service import StrategyScanService


class FakeStrategyDataClient:
    def fetch_a_share_history(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return pd.DataFrame(
            [
                {
                    "日期": start_date + timedelta(days=index),
                    "开盘": 10 + index * 0.1,
                    "最高": 10 + index * 0.1,
                    "最低": 10 + index * 0.1,
                    "收盘": 10 + index * 0.1,
                    "成交量": 1000 + index,
                    "成交额": 10000 + index,
                    "换手率": 1,
                    "涨跌幅": 1,
                }
                for index in range(140)
            ]
        )

    def fetch_a_share_history_tx(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return self.fetch_a_share_history(symbol, start_date, end_date, adjust)


def test_strategy_scan_service_ranks_signals(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeStrategyDataClient())
    service = StrategyScanService(db_session, price_service=price_service)

    result = service.scan(["000001"], strategy_name="trend_momentum_quality")

    assert result.strategy == "trend_momentum_quality"
    assert result.signals[0].symbol == "000001"
    assert result.signals[0].score >= 60

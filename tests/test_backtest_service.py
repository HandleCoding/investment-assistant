from datetime import date, timedelta

import pandas as pd

from app.domain.backtest import BacktestRequest
from app.services.backtest_service import BacktestService
from app.services.price_service import PriceService


class FakeBacktestDataClient:
    def fetch_a_share_history(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return pd.DataFrame(
            [
                {
                    "日期": start_date + timedelta(days=index),
                    "开盘": 10 + index * 0.05,
                    "最高": 10 + index * 0.05,
                    "最低": 10 + index * 0.05,
                    "收盘": 10 + index * 0.05,
                    "成交量": 1000,
                    "成交额": 10000,
                    "换手率": 1,
                    "涨跌幅": 1,
                }
                for index in range(140)
            ]
        )

    def fetch_a_share_history_tx(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return self.fetch_a_share_history(symbol, start_date, end_date, adjust)


def test_backtest_service_runs_ma_cross(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeBacktestDataClient())
    service = BacktestService(db_session, price_service=price_service)

    result = service.run_moving_average_cross(
        BacktestRequest(symbol="000001", fast_window=5, slow_window=20, initial_cash=10000)
    )

    assert result.symbol == "000001"
    assert result.final_value > 10000
    assert result.trade_count >= 1

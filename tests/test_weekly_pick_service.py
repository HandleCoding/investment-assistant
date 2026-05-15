from datetime import date, timedelta

import pandas as pd

from app.services.price_service import PriceService
from app.services.weekly_pick_service import WeeklyPickService


class FakeWeeklyDataClient:
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
                    "成交额": 10000,
                    "换手率": 1,
                    "涨跌幅": 1,
                }
                for index in range(140)
            ]
        )

    def fetch_a_share_history_tx(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return self.fetch_a_share_history(symbol, start_date, end_date, adjust)


def test_weekly_pick_service_generates_picks(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeWeeklyDataClient())
    service = WeeklyPickService(db_session, price_service=price_service)

    pick = service.generate()

    assert pick.pick_date is not None
    assert len(pick.picks) >= 1
    assert pick.picks[0].symbol in {
        "000001", "002475", "300750", "600519",
        "000858", "002594", "300059", "601012",
        "603288", "510300",
    }
    assert pick.target_monthly_return == 0.10

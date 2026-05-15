from datetime import date, timedelta

import pandas as pd

from app.services.opportunity_service import OpportunityService
from app.services.price_service import PriceService


class FakeOpportunityDataClient:
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


def test_opportunity_service_ranks_candidates(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeOpportunityDataClient())
    service = OpportunityService(db_session, price_service=price_service)

    result = service.rank(["000001"], max_positions=3)

    assert len(result.recommendations) >= 1
    rec = result.recommendations[0]
    assert rec.symbol == "000001"
    assert rec.score >= 0
    assert rec.position_size > 0
    assert rec.entry is not None
    assert rec.stop_loss is not None
    assert rec.take_profit is not None


def test_opportunity_service_warns_when_upside_below_target(db_session) -> None:
    price_service = PriceService(db_session, data_client=FakeOpportunityDataClient())
    service = OpportunityService(
        db_session,
        price_service=price_service,
        target_monthly_return=0.50,
    )

    result = service.rank(["000001"])

    assert any("低于月度目标" in w for w in result.warnings)

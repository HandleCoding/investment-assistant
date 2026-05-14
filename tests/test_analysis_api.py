from datetime import date, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from app.api.analysis import get_analysis_service
from app.database.session import get_session
from app.main import app
from app.services.analysis_service import AnalysisService
from app.services.price_service import PriceService


class FakeDataClient:
    def fetch_a_share_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "日期": start_date + timedelta(days=index),
                    "开盘": 10 + index * 0.1,
                    "最高": 10 + index * 0.1,
                    "最低": 10 + index * 0.1,
                    "收盘": 10 + index * 0.1,
                    "成交量": 1000,
                    "成交额": 10000,
                    "换手率": 1,
                    "涨跌幅": 1,
                }
                for index in range(130)
            ]
        )


def test_analyze_a_share_api(db_session) -> None:
    def override_session():
        yield db_session

    def override_analysis_service():
        price_service = PriceService(db_session, data_client=FakeDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis/a-share/000001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "000001"
    assert body["metrics"]["price_count"] == 130

from datetime import date, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from app.api.analysis import get_analysis_service
from app.main import app
from app.services.analysis_service import AnalysisService
from app.services.price_service import PriceService


class FakeDataClient:
    def fetch_a_share_history(self, symbol: str, start_date: date, end_date: date, adjust: str):
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

    def fetch_a_share_history_tx(self, symbol: str, start_date: date, end_date: date, adjust: str):
        return self.fetch_a_share_history(symbol, start_date, end_date, adjust)


def test_dashboard_page_loads() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_candidate_pool_page_loads() -> None:
    response = TestClient(app).get("/candidates")

    assert response.status_code == 200
    assert "今日候选观察池" in response.text


def test_portfolio_page_loads() -> None:
    response = TestClient(app).get("/portfolio")

    assert response.status_code == 200
    assert "持仓管理" in response.text


def test_backtests_page_loads() -> None:
    response = TestClient(app).get("/backtests")

    assert response.status_code == 200
    assert "策略回测" in response.text


def test_data_management_page_loads() -> None:
    response = TestClient(app).get("/data")

    assert response.status_code == 200
    assert "数据管理" in response.text


def test_analysis_page_loads_with_fake_data(db_session) -> None:
    def override_analysis_service():
        price_service = PriceService(db_session, data_client=FakeDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis?market=a-share&symbol=000001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "资产分析" in response.text
    assert "000001" in response.text

from datetime import date, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from app.api.analysis import get_analysis_service
from app.database.session import get_session
from app.domain.errors import DataSourceError
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

    def fetch_a_share_history_tx(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        return self.fetch_a_share_history(symbol, start_date, end_date, adjust)

    def fetch_hk_stock_daily_sina(self, symbol: str, adjust: str) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "date": date.today() - timedelta(days=129 - index),
                    "open": 300 + index,
                    "high": 300 + index,
                    "low": 300 + index,
                    "close": 300 + index,
                    "volume": 1000,
                    "amount": 10000,
                }
                for index in range(130)
            ]
        )


class FallbackDataClient:
    def fetch_a_share_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        raise DataSourceError("primary failed")

    def fetch_a_share_history_tx(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "date": start_date + timedelta(days=index),
                    "open": 10 + index * 0.1,
                    "high": 10 + index * 0.1,
                    "low": 10 + index * 0.1,
                    "close": 10 + index * 0.1,
                    "amount": 1000,
                }
                for index in range(130)
            ]
        )


class BrokenDataClient:
    def fetch_a_share_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        raise DataSourceError("primary failed")

    def fetch_a_share_history_tx(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str,
    ) -> pd.DataFrame:
        raise DataSourceError("fallback failed")


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


def test_analyze_a_share_report_api(db_session) -> None:
    def override_analysis_service():
        price_service = PriceService(db_session, data_client=FakeDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis/a-share/000001/report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "A 股股票分析报告" in response.text


def test_analyze_a_share_api_uses_fallback_source(db_session) -> None:
    def override_analysis_service():
        price_service = PriceService(db_session, data_client=FallbackDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis/a-share/000592")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["metrics"]["price_count"] == 130


def test_analyze_a_share_api_returns_503_when_data_source_fails(db_session) -> None:
    def override_analysis_service():
        price_service = PriceService(db_session, data_client=BrokenDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis/a-share/603288")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "行情数据源暂时不可用" in response.json()["detail"]


def test_analyze_hk_stock_api_accepts_hk_prefix(db_session) -> None:
    def override_analysis_service():
        price_service = PriceService(db_session, data_client=FakeDataClient())
        return AnalysisService(db_session, price_service=price_service)

    app.dependency_overrides[get_analysis_service] = override_analysis_service

    try:
        response = TestClient(app).get("/analysis/hk/HK0700")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "00700"
    assert body["metrics"]["price_count"] == 130

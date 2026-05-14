from fastapi.testclient import TestClient

from app.database.session import get_session
from app.main import app


def test_portfolio_api_upserts_and_reads_position(db_session) -> None:
    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    try:
        create_response = TestClient(app).post(
            "/api/portfolio/positions",
            json={
                "symbol": "000001",
                "market": "A_SHARE",
                "asset_type": "STOCK",
                "name": "平安银行",
                "quantity": 100,
                "cost_price": 10,
                "last_price": 11,
            },
        )
        read_response = TestClient(app).get("/api/portfolio")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert read_response.status_code == 200
    assert read_response.json()["positions"][0]["symbol"] == "000001"


def test_assets_api_lists_persisted_assets(db_session) -> None:
    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    try:
        TestClient(app).post(
            "/api/portfolio/positions",
            json={
                "symbol": "000001",
                "market": "A_SHARE",
                "asset_type": "STOCK",
                "quantity": 100,
                "cost_price": 10,
            },
        )
        response = TestClient(app).get("/api/assets")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["symbol"] == "000001"

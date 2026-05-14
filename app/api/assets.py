from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.repositories.assets import AssetRepository

router = APIRouter()


@router.get("")
def list_assets(
    session: Annotated[Session, Depends(get_session)],
    market: str | None = None,
) -> list[dict[str, object]]:
    assets = AssetRepository(session).list_assets(market)
    return [
        {
            "id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "market": asset.market,
            "asset_type": asset.asset_type,
            "industry": asset.industry,
            "status": asset.status,
        }
        for asset in assets
    ]


@router.get("/{symbol}")
def get_asset(
    symbol: str,
    session: Annotated[Session, Depends(get_session)],
    market: str = "A_SHARE",
) -> dict[str, object]:
    asset = AssetRepository(session).get_by_symbol(symbol, market)
    if asset is None:
        return {"symbol": symbol, "market": market, "status": "NOT_FOUND"}
    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "name": asset.name,
        "market": asset.market,
        "asset_type": asset.asset_type,
        "industry": asset.industry,
        "status": asset.status,
    }

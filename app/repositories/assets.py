from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Asset, AssetType, Market


class AssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_symbol(self, symbol: str, market: str) -> Asset | None:
        return self.session.scalar(
            select(Asset).where(Asset.symbol == symbol, Asset.market == market)
        )

    def get_or_create(
        self,
        symbol: str,
        market: str,
        asset_type: str,
        name: str | None = None,
    ) -> Asset:
        asset = self.get_by_symbol(symbol, market)
        if asset is not None:
            if name and asset.name != name:
                asset.name = name
                asset.updated_at = datetime.now(UTC)
                self.session.flush()
            return asset

        asset = Asset(
            symbol=symbol,
            name=name,
            market=market,
            asset_type=asset_type,
            industry=None,
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def list_assets(self, market: str | None = None) -> list[Asset]:
        statement = select(Asset).order_by(Asset.market, Asset.symbol)
        if market:
            statement = statement.where(Asset.market == market)
        return list(self.session.scalars(statement).all())


def normalize_market(value: str) -> str:
    normalized = value.upper().replace("-", "_")
    if normalized in {item.value for item in Market}:
        return normalized
    raise ValueError(f"Unsupported market: {value}")


def normalize_asset_type(value: str) -> str:
    normalized = value.upper().replace("-", "_")
    if normalized in {item.value for item in AssetType}:
        return normalized
    raise ValueError(f"Unsupported asset type: {value}")


def coerce_date(value: date | None) -> date:
    return value or datetime.now(UTC).date()

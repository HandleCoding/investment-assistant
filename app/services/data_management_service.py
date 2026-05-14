from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Asset, BacktestRun, CandidateEntry, PortfolioPosition, PriceDaily
from app.domain.data_management import AssetDataCoverage, DataHealthSnapshot


class DataManagementService:
    def __init__(self, session: Session):
        self.session = session

    def snapshot(self) -> DataHealthSnapshot:
        return DataHealthSnapshot(
            asset_count=self._count(Asset),
            price_bar_count=self._count(PriceDaily),
            candidate_count=self._count(CandidateEntry),
            position_count=self._count(PortfolioPosition),
            backtest_count=self._count(BacktestRun),
            coverage=self._coverage(),
        )

    def _count(self, model: type) -> int:
        return int(self.session.scalar(select(func.count()).select_from(model)) or 0)

    def _coverage(self) -> list[AssetDataCoverage]:
        statement = (
            select(
                Asset.symbol,
                Asset.market,
                Asset.asset_type,
                func.count(PriceDaily.id),
                func.min(PriceDaily.trade_date),
                func.max(PriceDaily.trade_date),
            )
            .outerjoin(PriceDaily, PriceDaily.asset_id == Asset.id)
            .group_by(Asset.id)
            .order_by(Asset.market, Asset.symbol)
        )
        return [
            AssetDataCoverage(
                symbol=row[0],
                market=row[1],
                asset_type=row[2],
                price_count=int(row[3] or 0),
                first_trade_date=row[4],
                last_trade_date=row[5],
            )
            for row in self.session.execute(statement).all()
        ]

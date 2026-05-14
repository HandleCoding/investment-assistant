from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import PortfolioPosition
from app.domain.portfolio import PortfolioPositionInput


class PortfolioRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_position(self, asset_id: int, data: PortfolioPositionInput) -> PortfolioPosition:
        position = self.session.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.asset_id == asset_id,
                PortfolioPosition.status == "OPEN",
            )
        )
        if position is None:
            position = PortfolioPosition(asset_id=asset_id, status="OPEN")
            self.session.add(position)

        position.quantity = data.quantity
        position.cost_price = data.cost_price
        position.last_price = data.last_price
        position.stop_loss_price = data.stop_loss_price
        position.take_profit_price = data.take_profit_price
        position.opened_at = data.opened_at
        position.note = data.note
        position.updated_at = datetime.now(UTC)
        self.session.flush()
        return position

    def list_open_positions(self) -> list[PortfolioPosition]:
        statement = select(PortfolioPosition).where(PortfolioPosition.status == "OPEN")
        return list(self.session.scalars(statement).all())

    def close_position(self, position_id: int) -> PortfolioPosition:
        position = self.session.get(PortfolioPosition, position_id)
        if position is None:
            raise ValueError(f"Position not found: {position_id}")
        position.status = "CLOSED"
        position.updated_at = datetime.now(UTC)
        self.session.flush()
        return position

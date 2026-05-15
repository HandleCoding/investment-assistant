from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import TradeRecord


class TradeRepository:
    def __init__(self, session: Session):
        self.session = session

    def record(
        self,
        asset_id: int,
        action: str,
        quantity: float,
        price: float,
        trade_date: date,
        reason: str | None = None,
    ) -> TradeRecord:
        trade = TradeRecord(
            asset_id=asset_id,
            action=action,
            quantity=quantity,
            price=price,
            trade_date=trade_date,
            reason=reason,
        )
        self.session.add(trade)
        self.session.flush()
        return trade

    def list_by_month(self, year: int, month: int) -> list[TradeRecord]:
        statement = (
            select(TradeRecord)
            .where(
                TradeRecord.trade_date >= date(year, month, 1),
                TradeRecord.trade_date
                < (date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)),
            )
            .order_by(TradeRecord.trade_date)
        )
        return list(self.session.scalars(statement).all())

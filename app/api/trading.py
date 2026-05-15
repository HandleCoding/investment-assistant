from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import TradeOrderRequest
from app.database.session import get_session
from app.domain.trade import TradeOrder
from app.services.trade_service import TradeService

router = APIRouter()


def get_trade_service(
    session: Annotated[Session, Depends(get_session)],
) -> TradeService:
    return TradeService(session)


@router.post("/buy")
def execute_buy(
    request: TradeOrderRequest,
    service: Annotated[TradeService, Depends(get_trade_service)],
) -> dict[str, object]:
    tracker = service.execute_buy(TradeOrder(**request.model_dump()))
    return tracker.to_dict()


@router.post("/sell")
def execute_sell(
    request: TradeOrderRequest,
    service: Annotated[TradeService, Depends(get_trade_service)],
) -> dict[str, object]:
    tracker = service.execute_sell(TradeOrder(**request.model_dump()))
    if tracker is None:
        return {"status": "CLOSED"}
    return tracker.to_dict()


@router.get("/monthly-return")
def monthly_return(
    service: Annotated[TradeService, Depends(get_trade_service)],
    cash: float = 0,
    target: float = 0.10,
) -> dict[str, object]:
    return service.monthly_return(cash=cash, target=target).to_dict()

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import PortfolioPositionRequest
from app.database.session import get_session
from app.domain.portfolio import PortfolioPositionInput
from app.services.portfolio_service import PortfolioService

router = APIRouter()


def get_portfolio_service(
    session: Annotated[Session, Depends(get_session)],
) -> PortfolioService:
    return PortfolioService(session)


@router.get("")
def get_portfolio(
    service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> dict[str, object]:
    return service.snapshot().to_dict()


@router.post("/positions")
def upsert_position(
    request: PortfolioPositionRequest,
    service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> dict[str, object]:
    position = service.upsert_position(PortfolioPositionInput(**request.model_dump()))
    return position.to_dict()


@router.delete("/positions/{position_id}")
def close_position(
    position_id: int,
    service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> dict[str, object]:
    return service.close_position(position_id).to_dict()

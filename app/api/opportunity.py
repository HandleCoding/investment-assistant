from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import OpportunityRankRequest
from app.database.session import get_session
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.opportunity_service import OpportunityService

router = APIRouter()


def get_opportunity_service(
    session: Annotated[Session, Depends(get_session)],
) -> OpportunityService:
    return OpportunityService(session)


@router.post("/rank")
def rank_opportunities(
    request: OpportunityRankRequest,
    service: Annotated[OpportunityService, Depends(get_opportunity_service)],
) -> dict[str, object]:
    try:
        return service.rank(
            symbols=request.symbols,
            market=request.market,
            max_positions=request.max_positions,
        ).to_dict()
    except NoMarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataSourceError as exc:
        raise HTTPException(status_code=503, detail=f"行情数据源暂时不可用：{exc}") from exc

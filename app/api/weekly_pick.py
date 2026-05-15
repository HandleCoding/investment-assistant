from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.weekly_pick_service import WeeklyPickService

router = APIRouter()


def get_weekly_pick_service(
    session: Annotated[Session, Depends(get_session)],
) -> WeeklyPickService:
    return WeeklyPickService(session)


@router.get("")
def get_weekly_picks(
    service: Annotated[WeeklyPickService, Depends(get_weekly_pick_service)],
) -> dict[str, object]:
    try:
        return service.generate().to_dict()
    except NoMarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataSourceError as exc:
        raise HTTPException(status_code=503, detail=f"行情数据源暂时不可用：{exc}") from exc

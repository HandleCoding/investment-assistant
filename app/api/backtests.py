from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import BacktestRunRequest
from app.database.session import get_session
from app.domain.backtest import BacktestRequest
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.backtest_service import BacktestService

router = APIRouter()


def get_backtest_service(
    session: Annotated[Session, Depends(get_session)],
) -> BacktestService:
    return BacktestService(session)


@router.post("/ma-cross")
def run_moving_average_cross(
    request: BacktestRunRequest,
    service: Annotated[BacktestService, Depends(get_backtest_service)],
) -> dict[str, object]:
    try:
        return service.run_moving_average_cross(BacktestRequest(**request.model_dump())).to_dict()
    except NoMarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataSourceError as exc:
        raise HTTPException(status_code=503, detail=f"行情数据源暂时不可用：{exc}") from exc

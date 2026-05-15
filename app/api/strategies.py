from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import StrategyScanRequest
from app.database.session import get_session
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.strategy_scan_service import StrategyScanService

router = APIRouter()


def get_strategy_scan_service(
    session: Annotated[Session, Depends(get_session)],
) -> StrategyScanService:
    return StrategyScanService(session)


@router.post("/scan")
def scan_strategies(
    request: StrategyScanRequest,
    service: Annotated[StrategyScanService, Depends(get_strategy_scan_service)],
) -> dict[str, object]:
    try:
        return service.scan(
            symbols=request.symbols,
            market=request.market,
            strategy_name=request.strategy_name,
            limit=request.limit,
        ).to_dict()
    except NoMarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataSourceError as exc:
        raise HTTPException(status_code=503, detail=f"行情数据源暂时不可用：{exc}") from exc

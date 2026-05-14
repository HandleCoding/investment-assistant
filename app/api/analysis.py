from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportService

router = APIRouter()


def get_analysis_service(
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisService:
    return AnalysisService(session)


def _analyze_or_raise(service: AnalysisService, symbol: str):
    try:
        return service.analyze_a_share(symbol)
    except NoMarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataSourceError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"行情数据源暂时不可用：{exc}",
        ) from exc


@router.get("/a-share/{symbol}")
def analyze_a_share(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> dict[str, object]:
    return _analyze_or_raise(service, symbol).to_dict()


@router.get("/a-share/{symbol}/report")
def analyze_a_share_report(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> Response:
    summary = _analyze_or_raise(service, symbol)
    report = ReportService().render_a_share_markdown(summary)
    return Response(content=report, media_type="text/markdown; charset=utf-8")

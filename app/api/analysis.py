from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.domain.analysis import AnalysisSummary
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportService

router = APIRouter()


def get_analysis_service(
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisService:
    return AnalysisService(session)


def _analyze_or_raise(
    analyze: Callable[[str], AnalysisSummary],
    symbol: str,
) -> AnalysisSummary:
    try:
        return analyze(symbol)
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
    return _analyze_or_raise(service.analyze_a_share, symbol).to_dict()


@router.get("/a-share/{symbol}/report")
def analyze_a_share_report(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> Response:
    summary = _analyze_or_raise(service.analyze_a_share, symbol)
    report = ReportService().render_stock_markdown(summary, "A 股")
    return Response(content=report, media_type="text/markdown; charset=utf-8")


@router.get("/hk/{symbol}")
def analyze_hk_stock(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> dict[str, object]:
    return _analyze_or_raise(service.analyze_hk_stock, symbol).to_dict()


@router.get("/hk/{symbol}/report")
def analyze_hk_stock_report(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> Response:
    summary = _analyze_or_raise(service.analyze_hk_stock, symbol)
    report = ReportService().render_stock_markdown(summary, "港股")
    return Response(content=report, media_type="text/markdown; charset=utf-8")

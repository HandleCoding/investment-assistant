from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportService

router = APIRouter()


def get_analysis_service(
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisService:
    return AnalysisService(session)


@router.get("/a-share/{symbol}")
def analyze_a_share(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> dict[str, object]:
    return service.analyze_a_share(symbol).to_dict()


@router.get("/a-share/{symbol}/report")
def analyze_a_share_report(
    symbol: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> Response:
    summary = service.analyze_a_share(symbol)
    report = ReportService().render_a_share_markdown(summary)
    return Response(content=report, media_type="text/markdown; charset=utf-8")

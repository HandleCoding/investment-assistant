from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.services.analysis_service import AnalysisService

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

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.analysis import get_analysis_service
from app.core.paths import TEMPLATES_DIR
from app.database.session import get_session
from app.domain.errors import DataSourceError, NoMarketDataError
from app.services.analysis_service import AnalysisService
from app.services.web_view_service import (
    BacktestViewService,
    CandidatePoolViewService,
    DashboardViewService,
    DataManagementViewService,
    PortfolioViewService,
    StrategyViewService,
)

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    context = DashboardViewService(session).build().to_context()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"active_page": "dashboard", **context},
    )


@router.get("/analysis", response_class=HTMLResponse)
def analysis_page(
    request: Request,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
    symbol: Annotated[str, Query()] = "000001",
    market: Annotated[str, Query(pattern="^(a-share|hk)$")] = "a-share",
) -> HTMLResponse:
    summary = None
    error = None
    try:
        if market == "hk":
            summary = service.analyze_hk_stock(symbol)
        else:
            summary = service.analyze_a_share(symbol)
    except (DataSourceError, NoMarketDataError) as exc:
        error = str(exc)

    return templates.TemplateResponse(
        request,
        "analysis.html",
        {
            "active_page": "analysis",
            "symbol": symbol,
            "market": market,
            "summary": summary,
            "error": error,
        },
    )


@router.get("/candidates", response_class=HTMLResponse)
def candidate_pool(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    context = CandidatePoolViewService(session).build().to_context()
    return templates.TemplateResponse(
        request,
        "candidates.html",
        {"active_page": "candidates", **context},
    )


@router.get("/portfolio", response_class=HTMLResponse)
def portfolio(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    context = PortfolioViewService(session).build().to_context()
    return templates.TemplateResponse(
        request,
        "portfolio.html",
        {"active_page": "portfolio", **context},
    )


@router.get("/backtests", response_class=HTMLResponse)
def backtests(request: Request) -> HTMLResponse:
    context = BacktestViewService().build().to_context()
    return templates.TemplateResponse(
        request,
        "backtests.html",
        {"active_page": "backtests", **context},
    )


@router.get("/strategies", response_class=HTMLResponse)
def strategies(request: Request) -> HTMLResponse:
    context = StrategyViewService().build().to_context()
    return templates.TemplateResponse(
        request,
        "strategies.html",
        {"active_page": "strategies", **context},
    )


@router.get("/data", response_class=HTMLResponse)
def data_management(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    context = DataManagementViewService(session).build().to_context()
    return templates.TemplateResponse(
        request,
        "data.html",
        {"active_page": "data", **context},
    )

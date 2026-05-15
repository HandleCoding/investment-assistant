from fastapi import APIRouter

from app.api import (
    analysis,
    assets,
    backtests,
    candidates,
    data_management,
    opportunity,
    portfolio,
    strategies,
    trading,
    weekly_pick,
)

router = APIRouter()
router.include_router(assets.router, prefix="/api/assets", tags=["assets"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
router.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
router.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
router.include_router(backtests.router, prefix="/api/backtests", tags=["backtests"])
router.include_router(data_management.router, prefix="/api/data", tags=["data"])
router.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
router.include_router(opportunity.router, prefix="/api/opportunities", tags=["opportunities"])
router.include_router(weekly_pick.router, prefix="/api/weekly-picks", tags=["weekly-picks"])
router.include_router(trading.router, prefix="/api/trading", tags=["trading"])

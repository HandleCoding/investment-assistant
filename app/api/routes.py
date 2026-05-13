from fastapi import APIRouter

from app.api import analysis, assets

router = APIRouter()
router.include_router(assets.router, prefix="/assets", tags=["assets"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

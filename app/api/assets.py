from fastapi import APIRouter

router = APIRouter()


@router.get("/{symbol}")
def get_asset(symbol: str) -> dict[str, str]:
    return {"symbol": symbol, "status": "not_implemented"}

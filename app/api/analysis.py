from fastapi import APIRouter

router = APIRouter()


@router.get("/{symbol}")
def analyze_asset(symbol: str) -> dict[str, str]:
    return {"symbol": symbol, "status": "not_implemented"}

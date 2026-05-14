from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class AssetDataCoverage:
    symbol: str
    market: str
    asset_type: str
    price_count: int
    first_trade_date: date | None
    last_trade_date: date | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DataHealthSnapshot:
    asset_count: int
    price_bar_count: int
    candidate_count: int
    position_count: int
    backtest_count: int
    coverage: list[AssetDataCoverage]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

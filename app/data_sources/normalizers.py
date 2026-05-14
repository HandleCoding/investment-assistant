import pandas as pd

from app.domain.market_data import PriceBar

A_SHARE_PRICE_COLUMNS = {
    "日期": "trade_date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover_rate",
    "涨跌幅": "pct_change",
}


def normalize_a_share_prices(raw_prices: pd.DataFrame) -> list[PriceBar]:
    if raw_prices.empty:
        return []

    frame = raw_prices.rename(columns=A_SHARE_PRICE_COLUMNS)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date

    bars: list[PriceBar] = []
    for row in frame.to_dict(orient="records"):
        bars.append(
            PriceBar(
                trade_date=row["trade_date"],
                open=_optional_float(row.get("open")),
                high=_optional_float(row.get("high")),
                low=_optional_float(row.get("low")),
                close=_optional_float(row.get("close")),
                volume=_optional_float(row.get("volume")),
                amount=_optional_float(row.get("amount")),
                turnover_rate=_optional_float(row.get("turnover_rate")),
                pct_change=_optional_float(row.get("pct_change")),
            )
        )
    return bars


def price_bars_to_frame(price_bars: list[PriceBar]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": bar.trade_date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "amount": bar.amount,
                "turnover_rate": bar.turnover_rate,
                "pct_change": bar.pct_change,
            }
            for bar in price_bars
        ]
    ).sort_values("trade_date")


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)

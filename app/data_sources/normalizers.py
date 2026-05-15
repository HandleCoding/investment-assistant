import pandas as pd

from app.domain.fund_data import FundNavBar
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

A_SHARE_TX_PRICE_COLUMNS = {
    "date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "amount": "volume",
}

HK_DAILY_PRICE_COLUMNS = {
    "date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "amount": "amount",
}

FUND_NAV_COLUMNS = {
    "净值日期": "nav_date",
    "日期": "nav_date",
    "单位净值": "unit_nav",
    "累计净值": "accumulated_nav",
    "日增长率": "daily_return",
}


def normalize_a_share_prices(raw_prices: pd.DataFrame) -> list[PriceBar]:
    return _normalize_price_frame(raw_prices, A_SHARE_PRICE_COLUMNS)


def normalize_a_share_tx_prices(raw_prices: pd.DataFrame) -> list[PriceBar]:
    return _normalize_price_frame(raw_prices, A_SHARE_TX_PRICE_COLUMNS)


def normalize_hk_daily_prices(raw_prices: pd.DataFrame) -> list[PriceBar]:
    return _normalize_price_frame(raw_prices, HK_DAILY_PRICE_COLUMNS)


def normalize_fund_nav(raw_nav: pd.DataFrame) -> list[FundNavBar]:
    if raw_nav.empty:
        return []
    frame = raw_nav.rename(columns=FUND_NAV_COLUMNS)
    frame["nav_date"] = pd.to_datetime(frame["nav_date"]).dt.date
    bars: list[FundNavBar] = []
    for row in frame.to_dict(orient="records"):
        bars.append(
            FundNavBar(
                nav_date=row["nav_date"],
                unit_nav=_optional_float(row.get("unit_nav")),
                accumulated_nav=_optional_float(row.get("accumulated_nav")),
                daily_return=_optional_percent(row.get("daily_return")),
            )
        )
    return bars


def fund_nav_to_price_frame(nav_bars: list[FundNavBar]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": bar.nav_date,
                "open": bar.unit_nav,
                "high": bar.unit_nav,
                "low": bar.unit_nav,
                "close": bar.unit_nav,
                "volume": 0,
                "amount": 0,
                "pct_change": bar.daily_return,
            }
            for bar in nav_bars
        ]
    ).sort_values("trade_date")


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


def _normalize_price_frame(raw_prices: pd.DataFrame, columns: dict[str, str]) -> list[PriceBar]:
    if raw_prices.empty:
        return []

    frame = raw_prices.rename(columns=columns)
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


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(str(value).replace("%", ""))


def _optional_percent(value: object) -> float | None:
    raw_value = _optional_float(value)
    if raw_value is None:
        return None
    return raw_value / 100 if abs(raw_value) > 1 else raw_value

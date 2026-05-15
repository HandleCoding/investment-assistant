from datetime import date

import akshare as ak
import pandas as pd
from requests import RequestException

from app.domain.errors import DataSourceError


class AkShareClient:
    def fetch_a_share_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        try:
            return ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
                timeout=10,
            )
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取东方财富 A 股行情失败：{exc}") from exc

    def fetch_a_share_history_tx(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        try:
            return ak.stock_zh_a_hist_tx(
                symbol=_a_share_symbol_with_market(symbol),
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
                timeout=10,
            )
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取腾讯 A 股行情失败：{exc}") from exc

    def fetch_hk_stock_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        try:
            return ak.stock_hk_hist(
                symbol=_hk_symbol(symbol),
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
            )
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取港股行情失败：{exc}") from exc

    def fetch_hk_stock_daily_sina(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        try:
            return ak.stock_hk_daily(symbol=_hk_symbol(symbol), adjust=adjust)
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取新浪港股行情失败：{exc}") from exc

    def fetch_hk_fund_history(self, code: str) -> pd.DataFrame:
        try:
            return ak.fund_hk_fund_hist_em(code=code, symbol="历史净值明细")
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取港基净值失败：{exc}") from exc

    def fetch_open_fund_history(self, symbol: str) -> pd.DataFrame:
        try:
            return ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取基金净值失败：{exc}") from exc


def _a_share_symbol_with_market(symbol: str) -> str:
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith(("6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _hk_symbol(symbol: str) -> str:
    normalized = symbol.upper().removeprefix("HK")
    return normalized.zfill(5)

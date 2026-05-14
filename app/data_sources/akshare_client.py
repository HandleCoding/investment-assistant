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
            raise DataSourceError(f"AkShare 获取 A 股行情失败：{exc}") from exc

    def fetch_hk_stock_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        try:
            return ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
            )
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取港股行情失败：{exc}") from exc

    def fetch_hk_fund_history(self, code: str) -> pd.DataFrame:
        try:
            return ak.fund_hk_fund_hist_em(code=code, symbol="历史净值明细")
        except RequestException as exc:
            raise DataSourceError(f"AkShare 获取港基净值失败：{exc}") from exc

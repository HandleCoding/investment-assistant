from datetime import date

import akshare as ak
import pandas as pd


class AkShareClient:
    def fetch_a_share_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust=adjust,
        )

    def fetch_hk_stock_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        return ak.stock_hk_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust=adjust,
        )

    def fetch_hk_fund_history(self, code: str) -> pd.DataFrame:
        return ak.fund_hk_fund_hist_em(code=code, symbol="历史净值明细")

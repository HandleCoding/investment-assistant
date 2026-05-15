from datetime import date

import pandas as pd

from app.data_sources.normalizers import (
    normalize_a_share_prices,
    normalize_a_share_tx_prices,
    normalize_fund_nav,
    normalize_hk_daily_prices,
)


def test_normalize_a_share_prices() -> None:
    raw_prices = pd.DataFrame(
        [
            {
                "日期": "2026-01-02",
                "开盘": 10,
                "最高": 11,
                "最低": 9,
                "收盘": 10.5,
                "成交量": 1000,
                "成交额": 10000,
                "换手率": 1.2,
                "涨跌幅": 2.3,
            }
        ]
    )

    result = normalize_a_share_prices(raw_prices)

    assert len(result) == 1
    assert result[0].trade_date == date(2026, 1, 2)
    assert result[0].close == 10.5


def test_normalize_a_share_tx_prices() -> None:
    raw_prices = pd.DataFrame(
        [
            {
                "date": "2026-01-02",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "amount": 1000,
            }
        ]
    )

    result = normalize_a_share_tx_prices(raw_prices)

    assert len(result) == 1
    assert result[0].trade_date == date(2026, 1, 2)
    assert result[0].close == 10.5
    assert result[0].volume == 1000


def test_normalize_hk_daily_prices() -> None:
    raw_prices = pd.DataFrame(
        [
            {
                "date": "2026-01-02",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "volume": 2000,
                "amount": 3000,
            }
        ]
    )

    result = normalize_hk_daily_prices(raw_prices)

    assert len(result) == 1
    assert result[0].trade_date == date(2026, 1, 2)
    assert result[0].close == 10.5
    assert result[0].volume == 2000
    assert result[0].amount == 3000


def test_normalize_fund_nav() -> None:
    raw_nav = pd.DataFrame(
        [
            {
                "净值日期": "2026-01-02",
                "单位净值": "1.2345",
                "累计净值": "1.5000",
                "日增长率": "2.30%",
            }
        ]
    )

    result = normalize_fund_nav(raw_nav)

    assert len(result) == 1
    assert result[0].nav_date == date(2026, 1, 2)
    assert result[0].unit_nav == 1.2345
    assert result[0].daily_return == 0.023

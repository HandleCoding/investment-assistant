from datetime import date, timedelta

import pandas as pd

from app.strategies.modules import BreakoutVolumeStrategy, TrendMomentumStrategy


def _trend_prices(length: int = 140) -> pd.DataFrame:
    start = date(2026, 1, 1)
    return pd.DataFrame(
        [
            {
                "trade_date": start + timedelta(days=index),
                "open": 10 + index * 0.1,
                "high": 10 + index * 0.1,
                "low": 10 + index * 0.1,
                "close": 10 + index * 0.1,
                "volume": 1000 + index * 3,
            }
            for index in range(length)
        ]
    )


def test_trend_momentum_strategy_scores_strong_trend() -> None:
    signal = TrendMomentumStrategy().evaluate("000001", "A_SHARE", _trend_prices())

    assert signal.score >= 60
    assert signal.action in {"可观察", "强关注"}
    assert signal.entry is not None
    assert signal.stop_loss is not None
    assert signal.take_profit is not None


def test_breakout_strategy_detects_confirmed_breakout() -> None:
    prices = _trend_prices()
    prices.loc[139, "close"] = prices["high"].iloc[-61:-1].max() + 2
    prices.loc[139, "high"] = prices.loc[139, "close"]
    prices.loc[139, "volume"] = prices["volume"].tail(20).mean() * 2

    signal = BreakoutVolumeStrategy().evaluate("000001", "A_SHARE", prices)

    assert signal.score >= 70
    assert "突破" in signal.reasons[0]

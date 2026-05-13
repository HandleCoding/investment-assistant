import pandas as pd

from app.indicators.risk import max_drawdown
from app.indicators.technical import moving_average


def test_moving_average() -> None:
    values = pd.Series([1, 2, 3, 4, 5])

    result = moving_average(values, 3)

    assert result.iloc[-1] == 4


def test_max_drawdown() -> None:
    values = pd.Series([100, 120, 90, 110])

    result = max_drawdown(values)

    assert round(result, 4) == -0.25

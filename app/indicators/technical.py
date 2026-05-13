import pandas as pd


def moving_average(values: pd.Series, window: int) -> pd.Series:
    return values.rolling(window=window, min_periods=window).mean()


def rate_of_change(values: pd.Series, periods: int) -> pd.Series:
    return values.pct_change(periods=periods)

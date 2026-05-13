import pandas as pd


def historical_percentile(values: pd.Series, current: float) -> float:
    clean_values = values.dropna()
    if clean_values.empty:
        return 0.0
    return float((clean_values <= current).mean())

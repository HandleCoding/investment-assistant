import pandas as pd


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    drawdown = values / values.cummax() - 1
    return float(drawdown.min())


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    if returns.empty:
        return 0.0
    return float(returns.std() * periods_per_year**0.5)

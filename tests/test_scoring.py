from datetime import date, timedelta

import pandas as pd

from app.services.scoring_service import ScoringService


def test_score_a_share_returns_summary() -> None:
    start_date = date(2025, 1, 1)
    prices = pd.DataFrame(
        [
            {
                "trade_date": start_date + timedelta(days=index),
                "open": 10 + index * 0.1,
                "high": 10 + index * 0.1,
                "low": 10 + index * 0.1,
                "close": 10 + index * 0.1,
                "volume": 1000,
                "amount": 10000,
                "turnover_rate": 1,
                "pct_change": 1,
            }
            for index in range(130)
        ]
    )

    result = ScoringService().score_a_share("000001", prices)

    assert result.symbol == "000001"
    assert result.score.total > 0
    assert result.metrics["price_count"] == 130
    assert result.conclusion in {"Avoid", "High Risk", "Neutral", "Watch", "Strong Watch"}

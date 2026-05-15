from dataclasses import asdict, dataclass
from datetime import date

from app.domain.opportunity import OpportunityRecommendation


@dataclass(frozen=True)
class WeeklyPick:
    pick_date: date
    target_monthly_return: float
    picks: list[OpportunityRecommendation]
    warnings: list[str]
    backtest_summary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

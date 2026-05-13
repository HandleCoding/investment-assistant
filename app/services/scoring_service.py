from app.domain.analysis import AnalysisSummary, ScoreBreakdown


class ScoringService:
    def classify_score(self, score: float) -> str:
        if score >= 85:
            return "Strong Watch"
        if score >= 70:
            return "Watch"
        if score >= 55:
            return "Neutral"
        if score >= 40:
            return "High Risk"
        return "Avoid"

    def placeholder_summary(self, symbol: str) -> AnalysisSummary:
        score = ScoreBreakdown(total=0)
        return AnalysisSummary(
            symbol=symbol,
            score=score,
            conclusion=self.classify_score(score.total),
            reasons=[],
            risks=["Analysis rules are not implemented yet."],
        )

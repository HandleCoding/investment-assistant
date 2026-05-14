from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import CandidateEntry
from app.domain.analysis import AnalysisSummary


class CandidateRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_from_analysis(
        self,
        asset_id: int,
        generated_at: date,
        summary: AnalysisSummary,
    ) -> CandidateEntry:
        entry = self.session.scalar(
            select(CandidateEntry).where(
                CandidateEntry.asset_id == asset_id,
                CandidateEntry.generated_at == generated_at,
            )
        )
        metrics = summary.metrics
        reason = summary.reasons[0] if summary.reasons else "暂无明确入池理由"
        risk = summary.risks[0] if summary.risks else "暂无明显风险"
        if entry is None:
            entry = CandidateEntry(asset_id=asset_id, generated_at=generated_at)
            self.session.add(entry)

        entry.score = summary.score.total
        entry.conclusion = summary.conclusion
        entry.return_20d = _to_float(metrics.get("return_20d"))
        entry.max_drawdown = _to_float(metrics.get("max_drawdown"))
        entry.reason = reason
        entry.risk = risk
        entry.status = "WATCHING"
        self.session.flush()
        return entry

    def list_latest(self, limit: int = 50) -> list[CandidateEntry]:
        statement = (
            select(CandidateEntry)
            .order_by(CandidateEntry.generated_at.desc(), CandidateEntry.score.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def update_status(self, entry_id: int, status: str) -> CandidateEntry:
        entry = self.session.get(CandidateEntry, entry_id)
        if entry is None:
            raise ValueError(f"Candidate entry not found: {entry_id}")
        entry.status = status.upper()
        self.session.flush()
        return entry


def today() -> date:
    return datetime.now(UTC).date()


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)

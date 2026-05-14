from datetime import date

from app.database.models import Asset, CandidateEntry
from app.services.candidate_service import CandidatePoolService


def test_candidate_service_lists_persisted_entries(db_session) -> None:
    asset = Asset(symbol="000001", name="平安银行", market="A_SHARE", asset_type="STOCK")
    db_session.add(asset)
    db_session.flush()
    db_session.add(
        CandidateEntry(
            asset_id=asset.id,
            generated_at=date(2026, 1, 2),
            score=72,
            conclusion="可观察",
            return_20d=0.05,
            max_drawdown=-0.08,
            reason="趋势改善",
            risk="金融板块弹性有限",
            status="WATCHING",
        )
    )
    db_session.commit()

    snapshot = CandidatePoolService(db_session).list_latest()

    assert len(snapshot.entries) == 1
    assert snapshot.entries[0].symbol == "000001"
    assert snapshot.entries[0].score == 72

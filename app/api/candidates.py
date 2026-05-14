from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import CandidateGenerateRequest, CandidateStatusRequest
from app.database.session import get_session
from app.domain.candidate import CandidateRule
from app.services.candidate_service import CandidatePoolService

router = APIRouter()


def get_candidate_service(
    session: Annotated[Session, Depends(get_session)],
) -> CandidatePoolService:
    return CandidatePoolService(session)


@router.get("")
def list_candidates(
    service: Annotated[CandidatePoolService, Depends(get_candidate_service)],
) -> dict[str, object]:
    return service.list_latest().to_dict()


@router.post("/generate")
def generate_candidates(
    request: CandidateGenerateRequest,
    service: Annotated[CandidatePoolService, Depends(get_candidate_service)],
) -> dict[str, object]:
    rule = CandidateRule(**request.model_dump())
    return service.generate(rule).to_dict()


@router.patch("/{entry_id}/status")
def update_candidate_status(
    entry_id: int,
    request: CandidateStatusRequest,
    service: Annotated[CandidatePoolService, Depends(get_candidate_service)],
) -> dict[str, object]:
    return service.update_status(entry_id, request.status).to_dict()

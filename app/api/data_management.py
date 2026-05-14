from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.services.data_management_service import DataManagementService

router = APIRouter()


@router.get("/health")
def data_health(
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, object]:
    return DataManagementService(session).snapshot().to_dict()

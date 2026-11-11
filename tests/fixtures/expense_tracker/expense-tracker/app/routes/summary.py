from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.custom import MonthlySummaryResponse
from app.services import expense_service as service
from app.services.errors import ServiceError

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get(
    "",
    operation_id="monthly_summary",
    response_model=MonthlySummaryResponse,
    responses={400: {"description": "Bad request"}},
)
def monthly_summary(month: str, db: Session = Depends(get_db)):
    try:
        return service.monthly_summary(db, month)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e

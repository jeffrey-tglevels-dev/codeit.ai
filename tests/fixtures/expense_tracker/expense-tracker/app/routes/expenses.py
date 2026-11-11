from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.services import expense_service as service
from app.services.errors import ServiceError

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

NOT_FOUND = {404: {"description": "Not found"}}
BAD_REQUEST = {400: {"description": "Bad request"}}


@router.get("", operation_id="list_expenses", response_model=list[ExpenseRead])
def list_expenses(db: Session = Depends(get_db)):
    return service.list_expenses(db)


@router.get("/{id}", operation_id="get_expense", response_model=ExpenseRead, responses=NOT_FOUND)
def get_expense(id: int, db: Session = Depends(get_db)):
    try:
        return service.get_expense(db, id)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e


@router.post(
    "",
    operation_id="create_expense",
    response_model=ExpenseRead,
    status_code=201,
    responses=BAD_REQUEST,
)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    try:
        return service.create_expense(db, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e


@router.put(
    "/{id}",
    operation_id="update_expense",
    response_model=ExpenseRead,
    responses={**BAD_REQUEST, **NOT_FOUND},
)
def update_expense(id: int, data: ExpenseUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_expense(db, id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e


@router.delete(
    "/{id}",
    operation_id="delete_expense",
    status_code=204,
    response_class=Response,
    responses=NOT_FOUND,
)
def delete_expense(id: int, db: Session = Depends(get_db)):
    try:
        service.delete_expense(db, id)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e
    return Response(status_code=204)

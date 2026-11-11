from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.services import category_service as service
from app.services.errors import ServiceError

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", operation_id="list_categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)


@router.post(
    "",
    operation_id="create_category",
    response_model=CategoryRead,
    status_code=201,
    responses={409: {"description": "Conflict"}},
)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    try:
        return service.create_category(db, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e


@router.delete(
    "/{id}",
    operation_id="delete_category",
    status_code=204,
    response_class=Response,
    responses={404: {"description": "Not found"}, 409: {"description": "Conflict"}},
)
def delete_category(id: int, db: Session = Depends(get_db)):
    try:
        service.delete_category(db, id)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e
    return Response(status_code=204)

from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories import category_repository as repo
from app.schemas.category import CategoryCreate
from app.services.errors import Conflict, NotFound


def list_categories(db: Session) -> list[Category]:
    return repo.list_all(db)


def create_category(db: Session, data: CategoryCreate) -> Category:
    if repo.get_by_name(db, data.name) is not None:
        raise Conflict(f"category {data.name!r} already exists")
    return repo.create(db, data.name)


def delete_category(db: Session, category_id: int) -> None:
    category = repo.get(db, category_id)
    if category is None:
        raise NotFound("category not found")
    if repo.count_expenses(db, category_id) > 0:
        raise Conflict("category still has expenses")
    repo.delete(db, category)

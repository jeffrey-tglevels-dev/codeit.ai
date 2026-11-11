from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.expense import Expense


def list_all(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def get(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def get_by_name(db: Session, name: str) -> Category | None:
    return db.scalars(select(Category).where(Category.name == name)).first()


def create(db: Session, name: str) -> Category:
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def count_expenses(db: Session, category_id: int) -> int:
    stmt = select(func.count()).select_from(Expense).where(Expense.category_id == category_id)
    return db.scalar(stmt) or 0


def delete(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()

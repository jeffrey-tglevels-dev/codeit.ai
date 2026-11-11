import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.expense import Expense


def list_all(db: Session) -> list[Expense]:
    return list(db.scalars(select(Expense).order_by(Expense.date.desc(), Expense.id.desc())))


def get(db: Session, expense_id: int) -> Expense | None:
    return db.get(Expense, expense_id)


def create(db: Session, values: dict[str, Any]) -> Expense:
    expense = Expense(**values)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update(db: Session, expense: Expense, values: dict[str, Any]) -> Expense:
    for key, value in values.items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()


def total_and_count(db: Session, start: datetime.date, end: datetime.date) -> tuple[float, int]:
    stmt = select(func.coalesce(func.sum(Expense.amount), 0.0), func.count(Expense.id)).where(
        Expense.date >= start, Expense.date < end
    )
    total, count = db.execute(stmt).one()
    return float(total), int(count)

import datetime
import re

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.repositories import category_repository
from app.repositories import expense_repository as repo
from app.schemas.custom import MonthlySummaryResponse
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.errors import Invalid, NotFound

MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
REQUIRED = ("amount", "description", "date", "category_id")


def _check_amount(amount: float) -> None:
    if amount <= 0:
        raise Invalid("amount must be > 0")


def _check_category(db: Session, category_id: int) -> None:
    if category_repository.get(db, category_id) is None:
        raise Invalid(f"category {category_id} does not exist")


def list_expenses(db: Session) -> list[Expense]:
    return repo.list_all(db)


def get_expense(db: Session, expense_id: int) -> Expense:
    expense = repo.get(db, expense_id)
    if expense is None:
        raise NotFound("expense not found")
    return expense


def create_expense(db: Session, data: ExpenseCreate) -> Expense:
    _check_amount(data.amount)
    _check_category(db, data.category_id)
    return repo.create(db, data.model_dump())


def update_expense(db: Session, expense_id: int, data: ExpenseUpdate) -> Expense:
    expense = get_expense(db, expense_id)
    values = data.model_dump(exclude_unset=True)
    for key in REQUIRED:
        if key in values and values[key] is None:
            raise Invalid(f"{key} must not be null")
    if "amount" in values:
        _check_amount(values["amount"])
    if "category_id" in values:
        _check_category(db, values["category_id"])
    return repo.update(db, expense, values)


def delete_expense(db: Session, expense_id: int) -> None:
    repo.delete(db, get_expense(db, expense_id))


def monthly_summary(db: Session, month: str) -> MonthlySummaryResponse:
    match = MONTH_RE.match(month)
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise Invalid("month must be YYYY-MM")
    year, mon = int(match.group(1)), int(match.group(2))
    start = datetime.date(year, mon, 1)
    end = datetime.date(year + 1, 1, 1) if mon == 12 else datetime.date(year, mon + 1, 1)
    total, count = repo.total_and_count(db, start, end)
    return MonthlySummaryResponse(month=month, total=total, count=count)

# Generated from the Contract. Do not edit.
import datetime

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    amount: float
    description: str
    date: datetime.date
    note: str | None = None
    category_id: int


class ExpenseUpdate(BaseModel):
    amount: float | None = None
    description: str | None = None
    date: datetime.date | None = None
    note: str | None = None
    category_id: int | None = None


class ExpenseRead(BaseModel):
    id: int
    amount: float
    description: str
    date: datetime.date
    note: str | None = None
    category_id: int

# Generated from the Contract. Do not edit.
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str | None = None


class CategoryRead(BaseModel):
    id: int
    name: str

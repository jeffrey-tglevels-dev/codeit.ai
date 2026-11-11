"""Operator input and the PM's questions (data-models.md §1-2)."""

from pydantic import BaseModel


class UserRequest(BaseModel):
    idea: str  # "make an expense tracker"


class Question(BaseModel):
    key: str  # "fields"
    question: str  # "What fields should an expense have?"
    suggestions: list[str] = []  # ["amount", "category", "date", "note"]
    answer: str | None = None  # filled in by the operator


class Inquiry(BaseModel):
    """The PM's questions and the operator's answers (one round)."""

    questions: list[Question]

    @property
    def answered(self) -> bool:
        return all(q.answer is not None for q in self.questions)

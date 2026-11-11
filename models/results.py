"""Agent results and check results (data-models.md §5-6)."""

from typing import Literal

from pydantic import BaseModel


class CodeResult(BaseModel):
    """What Backend, Frontend and Tester return after writing files.

    `files_written` is recorded by the file-write tool, never reported by the agent,
    so it is not part of this model.
    """

    notes: str = ""  # anything the agent wants the next round to know


CheckName = Literal["db_schema", "backend_contract", "frontend_contract", "tests"]


class CheckResult(BaseModel):
    """Produced by code only."""

    name: CheckName
    passed: bool
    exit_code: int | None = None
    report: dict | None = None  # parsed pytest JSON, or diff of openapi.json vs Contract
    log_tail: str = ""
    duration_s: float

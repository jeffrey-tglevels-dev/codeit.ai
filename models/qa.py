"""Test results, the Tester's verdicts and fix requests (data-models.md §7-9)."""

from typing import Literal

from pydantic import BaseModel, model_validator

Owner = Literal["backend", "frontend", "tester", "architect"]


class TestResult(BaseModel):
    __test__ = False  # not a pytest test class

    name: str
    kind: Literal["contract", "behavior", "ui"]
    feature: str | None = None  # links back to a Requirements feature
    passed: bool
    detail: str = ""


class Failure(BaseModel):
    test: str
    owner: Owner
    problem: str  # "DELETE /api/expenses/1 returns 500"
    evidence: str  # response, traceback or console log
    files: list[str] = []


class TestReport(BaseModel):
    """Built by code from the pytest JSON report."""

    __test__ = False

    results: list[TestResult]
    failures: list[Failure]
    all_passed: bool  # computed by code, never by an LLM

    @model_validator(mode="after")
    def _all_passed_is_consistent(self) -> "TestReport":
        actual = all(r.passed for r in self.results) and not self.failures
        if self.all_passed != actual:
            raise ValueError(f"all_passed must be {actual} for these results and failures")
        return self

    @classmethod
    def build(cls, results: list[TestResult], failures: list[Failure]) -> "TestReport":
        """Create a report with `all_passed` computed from the results."""
        all_passed = all(r.passed for r in results) and not failures
        return cls(results=results, failures=failures, all_passed=all_passed)


class TestVerdict(BaseModel):
    """The Tester's review of its own failing behavior test, before routing."""

    __test__ = False

    test: str
    verdict: Literal["test_wrong", "code_wrong", "contract_gap"]
    reason: str


class FixRequest(BaseModel):
    """Feedback a re-run agent receives alongside its original input."""

    round: int  # 1..3
    owner: Owner
    failures: list[Failure]
    operator_note: str | None = None

    @model_validator(mode="after")
    def _check(self) -> "FixRequest":
        if self.round < 1:
            raise ValueError("round starts at 1")
        wrong = [f.test for f in self.failures if f.owner != self.owner]
        if wrong:
            raise ValueError(f"failures {wrong} are not owned by {self.owner!r}")
        return self

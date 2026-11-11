"""Construction, defaults and the small built-in rules of every non-Contract model."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models import (
    CheckResult,
    CodeResult,
    DeliveryResult,
    Failure,
    FixRequest,
    Inquiry,
    OperatorMessage,
    Question,
    Requirements,
    Run,
    RunEvent,
    SandboxResult,
    TestReport,
    TestResult,
    TestVerdict,
    UserRequest,
    ZipResult,
)

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


def _failure(owner: str = "backend", test: str = "test_F1_x") -> Failure:
    return Failure(test=test, owner=owner, problem="POST /api/x returns 500", evidence="trace")


# --- request / inquiry ----------------------------------------------------------------------


def test_user_request() -> None:
    assert UserRequest(idea="make an expense tracker").idea == "make an expense tracker"


def test_inquiry_answered() -> None:
    inquiry = Inquiry(questions=[Question(key="fields", question="Which fields?")])
    assert inquiry.questions[0].suggestions == []
    assert not inquiry.answered
    inquiry.questions[0].answer = "amount, date"
    assert inquiry.answered


# --- requirements ---------------------------------------------------------------------------


def test_requirements_fixture_is_valid(requirements: Requirements) -> None:
    assert requirements.slug == "expense-tracker"
    assert requirements.feature_ids == {"F1", "F2", "F3", "F4", "F5", "F6"}


@pytest.mark.parametrize("slug", ["Expense Tracker", "expense_tracker", "-x", "x-", ""])
def test_requirements_bad_slug(requirements_data: dict, slug: str) -> None:
    requirements_data["slug"] = slug
    with pytest.raises(ValidationError, match="kebab-case"):
        Requirements.model_validate(requirements_data)


def test_requirements_duplicate_feature_id(requirements_data: dict) -> None:
    requirements_data["features"][1]["id"] = "F1"
    with pytest.raises(ValidationError, match="duplicate feature id 'F1'"):
        Requirements.model_validate(requirements_data)


def test_requirements_feature_needs_acceptance(requirements_data: dict) -> None:
    requirements_data["features"][0]["acceptance"] = []
    with pytest.raises(ValidationError, match="no acceptance criteria"):
        Requirements.model_validate(requirements_data)


def test_requirements_need_features(requirements_data: dict) -> None:
    requirements_data["features"] = []
    with pytest.raises(ValidationError, match="at least one feature"):
        Requirements.model_validate(requirements_data)


# --- results --------------------------------------------------------------------------------


def test_code_result_has_no_files_written() -> None:
    # files_written is recorded by the tool, never reported by the agent.
    assert "files_written" not in CodeResult.model_fields
    assert CodeResult().notes == ""


def test_check_result() -> None:
    r = CheckResult(name="db_schema", passed=True, duration_s=1.2)
    assert r.exit_code is None and r.report is None
    with pytest.raises(ValidationError):
        CheckResult(name="lint", passed=True, duration_s=0)


# --- QA -------------------------------------------------------------------------------------


def test_test_report_build_computes_all_passed() -> None:
    ok = TestResult(name="test_list_expenses", kind="contract", passed=True)
    bad = TestResult(name="test_F1_x", kind="behavior", feature="F1", passed=False)
    assert TestReport.build([ok], []).all_passed is True
    assert TestReport.build([ok, bad], [_failure()]).all_passed is False


def test_test_report_rejects_inconsistent_all_passed() -> None:
    bad = TestResult(name="test_F1_x", kind="behavior", passed=False)
    with pytest.raises(ValidationError, match="all_passed must be False"):
        TestReport(results=[bad], failures=[], all_passed=True)
    with pytest.raises(ValidationError, match="all_passed must be False"):
        TestReport(results=[], failures=[_failure()], all_passed=True)


def test_test_verdict() -> None:
    TestVerdict(test="test_F1_x", verdict="test_wrong", reason="assert on wrong field")
    with pytest.raises(ValidationError):
        TestVerdict(test="test_F1_x", verdict="flaky", reason="?")


def test_fix_request() -> None:
    fr = FixRequest(round=1, owner="backend", failures=[_failure("backend")])
    assert fr.operator_note is None


def test_fix_request_rejects_foreign_failures() -> None:
    with pytest.raises(ValidationError, match="not owned by 'backend'"):
        FixRequest(round=1, owner="backend", failures=[_failure("frontend")])


def test_fix_request_round_starts_at_one() -> None:
    with pytest.raises(ValidationError, match="round starts at 1"):
        FixRequest(round=0, owner="tester", failures=[])


def test_qa_classes_are_not_collected_by_pytest() -> None:
    for cls in (TestResult, TestReport, TestVerdict):
        assert cls.__test__ is False


# --- run state ------------------------------------------------------------------------------


def test_run_defaults() -> None:
    run = Run(id="r1", idea="todo app", stage="inquiry", created_at=NOW)
    assert run.round == 0 and run.branches == {} and run.tokens_used == 0
    run.branches["backend"] = "running"
    assert Run(id="r2", idea="x", stage="inquiry", created_at=NOW).branches == {}


def test_run_rejects_unknown_stage() -> None:
    with pytest.raises(ValidationError):
        Run(id="r1", idea="x", stage="deploying", created_at=NOW)


def test_run_event_roundtrips_as_jsonl() -> None:
    event = RunEvent(
        run_id="r1",
        ts=NOW,
        type="llm_call",
        stage="architect",
        data={"agent": "architect", "model": "m", "tokens": 1200, "cost": 0.01},
    )
    line = event.model_dump_json()
    assert "\n" not in line
    assert RunEvent.model_validate_json(line) == event


def test_operator_message() -> None:
    msg = OperatorMessage(
        id="m1", run_id="r1", target="frontend", text="use a table", created_at=NOW
    )
    assert msg.consumed is False
    with pytest.raises(ValidationError):
        OperatorMessage(id="m2", run_id="r1", target="packager", text="x", created_at=NOW)


# --- delivery -------------------------------------------------------------------------------


def test_delivery_defaults_claim_nothing() -> None:
    sandbox = SandboxResult()
    assert sandbox.image_built is False and sandbox.healthy is False
    d = DeliveryResult()
    assert d.zip is None and d.sandbox is None and d.test_report is None


def test_delivery_full() -> None:
    d = DeliveryResult(
        zip=ZipResult(zip_path="output/expense-tracker-r1.zip", size_bytes=1024),
        sandbox=SandboxResult(
            image_built=True,
            host_port=9001,
            healthy=True,
            preview_url="http://localhost:9001",
            expires_at=NOW,
        ),
        test_report=TestReport.build([], []),
    )
    assert DeliveryResult.model_validate_json(d.model_dump_json()) == d

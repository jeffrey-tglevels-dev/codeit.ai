"""Run state, the event log and operator messages (data-models.md §10)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Stage = Literal[
    "inquiry",
    "awaiting_answers",
    "requirements",
    "architect",
    "build",
    "testing",
    "review",
    "fixing",
    "packaging",
    "done",
    "failed",
    "stopped",
]
BranchStatus = Literal["pending", "running", "done", "failed"]
AgentName = Literal["pm", "architect", "backend", "frontend", "tester"]


class Run(BaseModel):
    id: str
    idea: str
    stage: Stage
    round: int = 0
    branches: dict[str, BranchStatus] = {}
    tokens_used: int = 0
    cost_usd: float | None = None
    created_at: datetime
    error: str | None = None  # e.g. "budget" when the cap is hit


class RunEvent(BaseModel):
    """Append-only: workspace/<run_id>/events.jsonl."""

    run_id: str
    ts: datetime
    type: Literal[
        "stage_started",
        "stage_finished",
        "check",
        "llm_call",
        "failure_routed",
        "operator_message",
        "error",
    ]
    stage: str
    data: dict = {}  # llm_call: agent, model, tokens, cost, latency


class OperatorMessage(BaseModel):
    id: str
    run_id: str
    target: AgentName
    text: str
    created_at: datetime
    consumed: bool = False  # injected into the target's next execution only

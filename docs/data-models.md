# Data Models and Data Flow

Status: draft. Code in `models/` follows this file.

Rule for every model: **what an agent says is kept apart from what code measures.** Agents return requirements, a contract, notes or verdicts. Anything that says "it works" (`passed`, `files_written`, `all_passed`, `healthy`) is filled in by code.

## Data flow

```
UserRequest ─► Inquiry ─► Requirements ─► Contract ─┬─► Backend  ─► CodeResult ─┐
  (user)     (PM asks,    (PM writes)    (Architect) ├─► Frontend ─► CodeResult ─┼─► CheckResults ─► TestReport
             user answers)                           └─► Tester   ─► CodeResult ─┘        (code)        (code)
                                                                                                          │
                     FixRequest ◄── routed Failures ◄── TestVerdicts (Tester review) ◄────────────────────┘
                                                                                                          │
                                                                              all passed / 3 rounds ─► DeliveryResult
```

| Step | Who | Reads | Produces |
|---|---|---|---|
| 1 | Operator | | `UserRequest` |
| 2 | PM | `UserRequest` | `Inquiry` (questions only) |
| 3 | Operator | `Inquiry` | `Inquiry` (with answers) |
| 4 | PM | `UserRequest` + answered `Inquiry` | `Requirements` |
| 5 | Architect | `Requirements` | `Contract` (validated by code; errors sent back) |
| 6 | Codegen (code) | `Contract` | `app/schemas/*.py`, contract tests, `tests/conftest.py`, UI smoke test |
| 7 | Backend, Frontend, Tester (parallel) | `Contract` (+ `Requirements` for Tester) | `CodeResult` each |
| 8 | Checks (code) | generated project | `CheckResult` per check |
| 9 | Tests (code) | pytest JSON report | `TestReport` |
| 10 | Tester (review) | its failing tests + evidence | `list[TestVerdict]` |
| 11 | Orchestrator | verdicts + `TestReport` | `Failure`s routed by owner -> `FixRequest` per failed branch (max 3 rounds) |
| 12 | Packager + Sandbox (code) | final project | `DeliveryResult` |

Generated app stack is fixed: FastAPI + SQLAlchemy (ORM) + SQLite + HTML/CSS/JS.
`app/models/` holds SQLAlchemy ORM classes; `app/core/database.py` holds the engine, session factory and `Base`.

SQLAlchemy 2.0 style is required (the Backend agent must not mix in 1.x patterns):
- `class Base(DeclarativeBase)` in `core/database.py`
- typed columns: `id: Mapped[int] = mapped_column(primary_key=True)`; use `Mapped[str | None]` for nullable
- queries: `select(Model)` with `session.scalars(...)` / `session.execute(...)`, not `session.query(...)`
- single entity lookup: `session.get(Model, id)`
- `create_engine(...)` and `sessionmaker(...)`; no `declarative_base()`, no legacy `Column(...)` declarations
- `requirements.txt` pins `sqlalchemy>=2.0`

Generated app layout is layered (see `generated-app-project-structure.md`):
`routes -> services -> repositories -> database`, with one file per entity in each layer.

---

## 1. UserRequest

```python
class UserRequest(BaseModel):
    idea: str          # "make an expense tracker"
```

---

## 2. Inquiry

The PM's questions and the operator's answers (one round).

```python
class Question(BaseModel):
    key: str                      # "fields"
    question: str                 # "What fields should an expense have?"
    suggestions: list[str] = []   # ["amount", "category", "date", "note"]
    answer: str | None = None     # filled in by the operator

class Inquiry(BaseModel):
    questions: list[Question]
```

---

## 3. Requirements

What the PM hands to the Architect. Each feature has testable acceptance criteria; the Tester writes tests against them.

```python
class Feature(BaseModel):
    id: str                      # "F1"
    description: str             # "Add an expense"
    acceptance: list[str]        # ["amount must be > 0", "new expense appears in the list"]

class Requirements(BaseModel):
    project_name: str            # "Expense Tracker"
    slug: str                    # "expense-tracker" (folder and ZIP name)
    summary: str                 # one or two sentences
    features: list[Feature]
    out_of_scope: list[str] = [] # auth always lands here in v1
    assumptions: list[str] = []  # gaps the PM filled in itself
```

---

## 4. Contract

The single source of truth for Backend, Frontend and Tester. Written in full by the Architect (every endpoint, including CRUD). Nested: `Contract` -> `Entity` -> `Field` / `Relation`, and `Contract` -> `Endpoint` -> `Shape`.

```python
FieldType = Literal["integer", "text", "real", "boolean", "date", "datetime"]

class Field(BaseModel):
    name: str                      # snake_case: "amount"
    type: FieldType
    required: bool = True
    unique: bool = False
    description: str = ""          # helps the Frontend label form inputs

class Relation(BaseModel):         # one-to-many only in v1
    field: str                     # foreign-key column on this entity: "category_id"
    target: str                    # entity name: "category"
    on_delete: Literal["cascade", "restrict", "set_null"] = "restrict"

class Entity(BaseModel):
    name: str                      # singular snake_case: "expense"
    plural: str                    # "expenses" -> table name and URL path
    fields: list[Field]            # `id` is implicit and never listed
    relations: list[Relation] = []

class Shape(BaseModel):
    """A request or response body: an entity view OR custom fields."""
    entity: str | None = None                                # "expense"
    view: Literal["create", "update", "read"] | None = None  # which generated schema
    fields: list[Field] | None = None                        # custom shape, e.g. a monthly summary
    many: bool = False                                       # list = plain JSON array, no pagination

class Endpoint(BaseModel):
    id: str                        # "list_expenses"; becomes the FastAPI operation_id
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str                      # "/api/expenses/{id}"
    summary: str
    features: list[str]            # Requirements feature ids this endpoint serves: ["F1"]
    query_params: list[Field] = []
    request: Shape | None = None
    response: Shape | None = None  # None => 204 No Content
    success_status: Literal[200, 201, 204]
    error_statuses: list[Literal[400, 404, 409, 422]] = []

class Contract(BaseModel):
    project_name: str
    entities: list[Entity]
    endpoints: list[Endpoint]
```

Error responses are the same for every endpoint: `{"detail": str}` (FastAPI's default).

### Validation (code, `model_validator`)

Errors are returned to the Architect for a retry.

- Entity names, plurals, endpoint ids and `(method, path)` pairs are unique.
- Field names are unique per entity; none is called `id`.
- Every `Relation.target` exists; `Relation.field` does not clash with a field.
- Every `Shape.entity` exists; a `Shape` has either `entity` + `view` or `fields`, not both.
- `GET` and `DELETE` have no request body; `204` means `response` is `None`.
- Every `{param}` in a path is `id` or declared.
- Paths follow `/api/<plural>` and `/api/<plural>/{id}` for entity endpoints.
- Success status matches the method: `POST` -> 201, `DELETE` -> 204, others -> 200.
- Every `Endpoint.features` id exists in `Requirements`, and every feature is served by at least one endpoint.

### Generated from the Contract (code, no LLM)

| Output | Rule |
|---|---|
| `app/schemas/<entity>.py` | `<Entity>Read`: `id`, every field, foreign-key ids. `<Entity>Create`: fields and foreign-key ids, no `id`. `<Entity>Update`: every field optional (partial update over `PUT`). Custom `Shape.fields` become their own classes. |
| `tests/contract/` | One test per endpoint: valid request returns `success_status` and a body that fits the declared `Shape`. |
| `tests/conftest.py` | Test client and a temporary SQLite database. |
| `tests/ui/` | Smoke test: `/` loads, no console errors, no failed requests. |

---

## 5. CodeResult

What Backend, Frontend and Tester return after writing files. `files_written` is recorded by the file-write tool, not reported by the agent.

```python
class CodeResult(BaseModel):
    notes: str = ""              # anything the agent wants the next round to know
```

The Tester names its tests `test_<feature_id>_<what>` so code can map tests to features.

---

## 6. CheckResult

Produced by code only. Every check runs in a fresh sandbox container, except the frontend check, which only reads files.

```python
class CheckResult(BaseModel):
    name: Literal["db_schema", "backend_contract", "frontend_contract", "tests"]
    passed: bool
    exit_code: int | None = None
    report: dict | None = None   # parsed pytest JSON, or diff of openapi.json vs Contract
    log_tail: str = ""
    duration_s: float
```

| Check | What it does |
|---|---|
| `db_schema` | `Base.metadata.create_all()` on an empty SQLite file succeeds and the tables match `Contract.entities`. |
| `backend_contract` | Start the app, read `/openapi.json`, compare every path, method, status and body shape to the `Contract`. |
| `frontend_contract` | Every `fetch` path in `app/static/` exists in the `Contract`. |
| `tests` | Run contract, behavior and UI tests; produce the pytest JSON report. |

---

## 7. TestReport

Built by code from the pytest JSON report.

```python
class TestResult(BaseModel):
    name: str
    kind: Literal["contract", "behavior", "ui"]
    feature: str | None = None       # links back to a Requirements feature
    passed: bool
    detail: str = ""

class Failure(BaseModel):
    test: str
    owner: Literal["backend", "frontend", "tester", "architect"]
    problem: str                     # "DELETE /api/expenses/1 returns 500"
    evidence: str                    # response, traceback or console log
    files: list[str] = []

class TestReport(BaseModel):
    results: list[TestResult]
    failures: list[Failure]
    all_passed: bool                 # computed by code, never by an LLM
```

---

## 8. TestVerdict

The Tester's review of its own failing behavior tests, before routing.

```python
class TestVerdict(BaseModel):
    test: str
    verdict: Literal["test_wrong", "code_wrong", "contract_gap"]
    reason: str
```

`test_wrong` -> owner `tester`; `contract_gap` -> owner `architect`; `code_wrong` -> owner from the routing table in `architecture.md` (by file path).

---

## 9. FixRequest

The feedback a re-run agent receives, alongside its original input. The agent edits its existing files; it does not regenerate them.

```python
class FixRequest(BaseModel):
    round: int                   # 1..3
    owner: Literal["backend", "frontend", "tester", "architect"]
    failures: list[Failure]
    operator_note: str | None = None
```

---

## 10. Run state

```python
class Run(BaseModel):
    id: str
    idea: str
    stage: Literal["inquiry", "awaiting_answers", "requirements", "architect",
                   "build", "testing", "review", "fixing", "packaging",
                   "done", "failed", "stopped"]
    round: int = 0
    branches: dict[str, Literal["pending", "running", "done", "failed"]] = {}
    tokens_used: int = 0
    cost_usd: float | None = None
    created_at: datetime
    error: str | None = None     # e.g. "budget" when the cap is hit

class RunEvent(BaseModel):       # append-only: workspace/<run_id>/events.jsonl
    run_id: str
    ts: datetime
    type: Literal["stage_started", "stage_finished", "check", "llm_call",
                  "failure_routed", "operator_message", "error"]
    stage: str
    data: dict = {}              # llm_call: agent, model, tokens, cost, latency

class OperatorMessage(BaseModel):
    id: str
    run_id: str
    target: Literal["pm", "architect", "backend", "frontend", "tester"]
    text: str
    created_at: datetime
    consumed: bool = False       # injected into the target's next execution only
```

---

## 11. DeliveryResult

Produced by code after the fix loop ends (no LLM). Two separate outputs: a source ZIP and a Docker sandbox preview. The Docker image is never inside the ZIP.

```python
class ZipResult(BaseModel):
    zip_path: str                # "output/expense-tracker-<run_id>.zip"
    size_bytes: int

class SandboxResult(BaseModel):
    image_tag: str | None = None
    image_built: bool = False
    container_id: str | None = None
    host_port: int | None = None
    preview_url: str | None = None       # "http://localhost:9001"
    expires_at: datetime | None = None   # container is removed after this
    healthy: bool = False                # preview URL answered HTTP 200
    build_log_tail: str = ""
    notes: str = ""

class DeliveryResult(BaseModel):
    zip: ZipResult | None = None
    sandbox: SandboxResult | None = None
    test_report: TestReport | None = None  # attached, especially when not all tests passed
```

`image_built` and `healthy` are measured by code (build exit status, HTTP 200), not claimed.

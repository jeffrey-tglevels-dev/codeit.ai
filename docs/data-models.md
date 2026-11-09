# Data Models and Data Flow

## Data flow

```
UserRequest ──► Inquiry ──► Requirements ──► Architecture ──► DbResult ──► BuildResult ──► QAReport
  (user)     (PM asks,      (PM writes)      (Architect)     (DB Eng)     (Developer)      (QA)
             user answers)
```

| Step | Who | Reads | Produces |
|---|---|---|---|
| 1 | User | | `UserRequest` |
| 2 | PM | `UserRequest` | `Inquiry` (questions only) |
| 3 | User | `Inquiry` | `Inquiry` (with answers) |
| 4 | PM | `UserRequest` + answered `Inquiry` | `Requirements` |
| 5 | Architect | `Requirements` | `Architecture` |
| 6 | DB Engineer | `Architecture.tables` | `DbResult` |
| 7 | Developer | `Architecture` + `DbResult` | `BuildResult` |
| 8 | QA | `Requirements` + `Architecture` + `BuildResult` | `QAReport` |
| 9 | Orchestrator | `QAReport` | sends each failure back to its `owner`, then QA re-runs (max 3 rounds) |

| 10 | Packager + Sandbox (code, no LLM) | passing project in `workspace/` | `DeliveryResult` (zip + sandbox preview URL) |

Generated app stack is fixed: FastAPI + SQLAlchemy (ORM) + SQLite + HTML/CSS/JS.
`app/models/` holds SQLAlchemy ORM classes; `app/core/database.py` holds the engine, session factory and `Base`.

SQLAlchemy 2.0 style is required (the DB Engineer must not mix in 1.x patterns):
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

The raw idea typed by the user.

```python
class UserRequest(BaseModel):
    idea: str          # "make an expense tracker"
```

---

## 2. Inquiry

The PM's questions and the user's answers (one round).

```python
class Question(BaseModel):
    key: str                      # "fields"
    question: str                 # "What fields should an expense have?"
    suggestions: list[str] = []   # ["amount", "category", "date", "note"]
    answer: str | None = None     # filled in by the user

class Inquiry(BaseModel):
    questions: list[Question]
```

```json
{
  "questions": [
    {"key": "fields", "question": "What fields should an expense have?",
     "suggestions": ["amount", "category", "date", "note"],
     "answer": "amount, category, date, note"},
    {"key": "auth", "question": "Do users need to log in?",
     "suggestions": ["yes", "no"], "answer": "no"}
  ]
}
```

---

## 3. Requirements

What the PM hands to the Architect.

```python
class Requirements(BaseModel):
    project_name: str              # "Expense Tracker"
    summary: str                   # one or two sentences
    features: list[str]            # ["add expense", "delete expense", "monthly summary"]
    data_fields: list[str]         # ["amount", "category", "date", "note"]
    needs_auth: bool = False
    out_of_scope: list[str] = []   # ["charts"]
    assumptions: list[str] = []    # gaps the PM filled in itself
```

---

## 4. Architecture

Tables, endpoints and files. Nested: `Architecture` -> `Table` -> `Column`.

```python
class Column(BaseModel):
    name: str                          # "amount"
    type: Literal["integer", "text", "real", "boolean", "date"]
    primary_key: bool = False
    required: bool = True

class Table(BaseModel):
    name: str                          # "expenses"
    columns: list[Column]

class Endpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str                          # "/api/expenses/{id}"
    description: str                   # "Delete one expense"

class ProjectFile(BaseModel):
    path: str                          # "app/routes/expenses.py"
    purpose: str                       # "CRUD routes for expenses"
    layer: Literal["core", "model", "repository", "schema", "service", "route", "static", "test"]
    owner: Literal["db", "dev"]        # who writes it (derived from layer, see below)

class Architecture(BaseModel):
    tables: list[Table]
    endpoints: list[Endpoint]
    files: list[ProjectFile]           # flat list; the path carries the folder
```

```json
{
  "tables": [{"name": "expenses", "columns": [
    {"name": "id", "type": "integer", "primary_key": true},
    {"name": "amount", "type": "real"},
    {"name": "category", "type": "text"}]}],
  "endpoints": [{"method": "POST", "path": "/api/expenses", "description": "Add an expense"}],
  "files": [
    {"path": "app/core/database.py", "purpose": "SQLAlchemy engine, SessionLocal, Base, get_db, init_db", "layer": "core", "owner": "db"},
    {"path": "app/models/expense.py", "purpose": "Expense ORM class (expenses table)", "layer": "model", "owner": "db"},
    {"path": "app/repositories/expense_repository.py", "purpose": "expense queries via SQLAlchemy Session", "layer": "repository", "owner": "db"},
    {"path": "app/schemas/expense.py", "purpose": "expense request/response shapes", "layer": "schema", "owner": "dev"},
    {"path": "app/services/expense_service.py", "purpose": "expense business rules", "layer": "service", "owner": "dev"},
    {"path": "app/routes/expenses.py", "purpose": "CRUD routes for expenses", "layer": "route", "owner": "dev"}
  ]
}
```

The generated app is layered: `app/{core,models,repositories,schemas,services,routes,static}/`, plus `tests/`.
The Architect lists one file per entity per layer (code can derive this from `tables`; the Architect fills in the purposes).

File ownership by layer:

| owner | layers / paths |
|---|---|
| `db` (DB Engineer) | `core` (`app/core/`), `model` (`app/models/`), `repository` (`app/repositories/`) |
| `dev` (Developer) | `schema`, `service`, `route`, `static`, `test`, plus `app/main.py` |

Root files (`requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`, `.env.example`, `README.md`, `data/.gitkeep`)
are written by the Packager (plain code) and are not listed in `Architecture.files`.

Dependency rule: layers only call downward (route -> service -> repository). Routes never touch the DB directly.

---

## 5. DbResult

What the DB Engineer reports after writing its files.

```python
class DbResult(BaseModel):
    files_written: list[str]     # ["app/core/database.py", "app/models/expense.py", "app/repositories/expense_repository.py"]
    repository_functions: list[str] = []   # ["expense_repository.create", ".get", ".list", ".delete"]
    schema_ok: bool              # Base.metadata.create_all() succeeds on an empty SQLite file and the tables match Architecture.tables
    notes: str = ""
```

`schema_ok` must be measured by code, not claimed by the agent.
`repository_functions` tells the Developer which data-access functions really exist, so services call real code.

---

## 6. BuildResult

What the Developer reports after writing the app.

```python
class BuildResult(BaseModel):
    files_written: list[str]
    run_command: str             # "uvicorn app.main:app --port 8000"
    app_starts: bool
    notes: str = ""
```

`app_starts` must be measured by launching the app, not claimed by the agent.

---

## 7. QAReport

Test results; drives the fix loop. Nested: `QAReport` -> `TestCase` / `Failure`.

```python
class TestCase(BaseModel):
    name: str                          # "add expense returns 201"
    passed: bool
    detail: str = ""                   # error text if it failed

class Failure(BaseModel):
    problem: str                       # "DELETE /api/expenses/1 returns 500"
    owner: Literal["dev", "db", "architect", "pm"]
    how_to_reproduce: str

class QAReport(BaseModel):
    tests: list[TestCase]
    failures: list[Failure]
    all_passed: bool
```

Routing by `Failure.owner`:

| owner | Re-run |
|---|---|
| `dev` | Developer |
| `db` | DB Engineer, then Developer |
| `architect` | Architect, then DB Engineer and Developer |
| `pm` | PM |

---

## 8. DeliveryResult

Produced by code after QA passes (no LLM). Two separate outputs: a source ZIP and a Docker sandbox preview.
The Docker image is never inside the ZIP.

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
```

`image_built` and `healthy` must be measured by code (build exit status, HTTP 200), not claimed.

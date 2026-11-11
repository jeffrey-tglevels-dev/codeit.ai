# Generated App Project Structure

Every app our agents produce follows this layout. Example: a "gym tracker" with entities `workout`, `exercise`, `workout_set`.

Request flow: `routes -> services -> repositories -> database`

```
gym-tracker/
├── app/
│   ├── main.py
│   ├── core/        (config.py, database.py)
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── routes/
│   └── static/
├── tests/
│   ├── conftest.py
│   ├── contract/
│   ├── ui/
│   └── test_<feature_id>_*.py
├── data/
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

Owner = who writes it:
- **BE** = Backend Engineer agent
- **FE** = Frontend Engineer agent
- **Test** = Tester agent
- **Gen** = Codegen (plain code, generated from the `Contract`, no LLM)
- **Pkg** = Packager (plain code, no LLM)

Agents can only write inside their own scope; the file-write tool enforces it.

## `app/` - the application code

| Path | Owner | Role |
|---|---|---|
| `app/__init__.py` | BE | Marks `app` as a Python package. Empty. |
| `app/main.py` | BE | Entry point. Creates the FastAPI app, calls `init_db()` on startup, includes every router, mounts `static/`. Run with `uvicorn app.main:app`. |

### `app/core/` - shared setup

| Path | Owner | Role |
|---|---|---|
| `core/config.py` | BE | Settings in one place: DB file path, host/port, values read from environment variables. |
| `core/database.py` | BE | SQLAlchemy 2.0 setup: engine, `SessionLocal` (`sessionmaker`), `class Base(DeclarativeBase)`, a `get_db()` dependency that yields a session, and `init_db()` which runs `Base.metadata.create_all()` on start. |

### `app/models/` - database tables

| Path | Owner | Role |
|---|---|---|
| `models/<entity>.py` | BE | One SQLAlchemy 2.0 ORM class per `Contract` entity, subclassing `Base`, with typed columns (`Mapped[int] = mapped_column(...)`), foreign keys from `Entity.relations`, and relationships. |

### `app/repositories/` - data access

| Path | Owner | Role |
|---|---|---|
| `repositories/<entity>_repository.py` | BE | The only code that queries the DB, using a SQLAlchemy `Session` and 2.0-style `select()` queries (not `session.query`). Functions like `create`, `get`, `list`, `update`, `delete`. No business rules. |

### `app/schemas/` - API data shapes

| Path | Owner | Role |
|---|---|---|
| `schemas/<entity>.py` | Gen | Pydantic classes generated from the `Contract`: `<Entity>Create`, `<Entity>Read`, `<Entity>Update`, plus classes for custom shapes. Agents read them but never edit them. |

### `app/services/` - business logic

| Path | Owner | Role |
|---|---|---|
| `services/<entity>_service.py` | BE | The app's rules (e.g. "reps must be positive", "a set needs an existing exercise"). Calls repositories, never touches HTTP or SQL directly. |

### `app/routes/` - HTTP endpoints

| Path | Owner | Role |
|---|---|---|
| `routes/<plural>.py` | BE | FastAPI routers, file named after `Entity.plural` (e.g. `workouts.py`). Each endpoint reads the request, calls one service, returns the response. Matches `Contract.endpoints` exactly, including `operation_id` = `Endpoint.id` and status codes. No SQL, no business rules. |

### `app/static/` - frontend

| Path | Owner | Role |
|---|---|---|
| `static/index.html` | FE | The page the user opens in the browser. |
| `static/css/style.css` | FE | Styling. |
| `static/js/app.js` | FE | Calls the API with `fetch`, only on paths in the `Contract`, and updates the page. |

## `tests/` - automated tests

Tests only call the API over HTTP; they never import `app.services` or other internals.

| Path | Owner | Role |
|---|---|---|
| `tests/conftest.py` | Gen | Shared setup: a test client and a temporary SQLite database, so tests never touch real data. |
| `tests/contract/` | Gen | One test per `Contract` endpoint: correct status and response shape. |
| `tests/ui/` | Gen | UI smoke test (Playwright): `/` loads, no console errors, no failed requests. |
| `tests/test_<feature_id>_*.py` | Test | Behavior tests written from each feature's acceptance criteria. Frozen across fix rounds unless the Tester's review marks a test as wrong. |

## `data/` - runtime data

| Path | Owner | Role |
|---|---|---|
| `data/.gitkeep` | Pkg | Keeps the empty folder in git. The SQLite `.db` file is created here at runtime. In Docker this folder is a volume so data survives restarts. |

## Root files - packaging and docs

| Path | Owner | Role |
|---|---|---|
| `requirements.txt` | Pkg | Python dependencies (`fastapi`, `uvicorn`, `sqlalchemy>=2.0`, ...). Must be a subset of the sandbox base image. |
| `Dockerfile` | Pkg | Recipe to build the app image: Python base, install requirements, copy code, run uvicorn on port 8000. Used by the preview sandbox and by anyone deploying. |
| `.dockerignore` | Pkg | Files kept out of the image (caches, `.git`, local `.db`, `.env`). |
| `.gitignore` | Pkg | Files kept out of git (same idea, plus `.venv`). |
| `.env.example` | Pkg | Template of the environment variables the app reads, with safe sample values. |
| `README.md` | Pkg | What the app does, features, endpoints, entities, how to run locally and with Docker, assumptions and out-of-scope items. Built from `Requirements` and `Contract`. |

## Ownership rules (summary)

- **Backend Engineer:** `app/main.py`, `app/__init__.py`, `app/core/`, `app/models/`, `app/repositories/`, `app/services/`, `app/routes/`
- **Frontend Engineer:** `app/static/`
- **Tester:** `tests/test_<feature_id>_*.py`
- **Codegen:** `app/schemas/`, `tests/conftest.py`, `tests/contract/`, `tests/ui/`
- **Packager:** all root files and `data/.gitkeep`
- Layers only call downward: routes -> services -> repositories. Routes never touch the DB directly.

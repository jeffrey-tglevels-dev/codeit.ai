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
├── data/
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

Owner = who writes it: **DB** = DB Engineer agent, **Dev** = Developer agent, **Pkg** = Packager (plain code, no LLM).

## `app/` - the application code

| Path | Owner | Role |
|---|---|---|
| `app/__init__.py` | Dev | Marks `app` as a Python package. Empty. |
| `app/main.py` | Dev | Entry point. Creates the FastAPI app, calls `init_db()` on startup, includes every router, mounts `static/`. Run with `uvicorn app.main:app`. |

### `app/core/` - shared setup

| Path | Owner | Role |
|---|---|---|
| `core/config.py` | DB | Settings in one place: DB file path, host/port, values read from environment variables. |
| `core/database.py` | DB | SQLAlchemy 2.0 setup: engine, `SessionLocal` (`sessionmaker`), `class Base(DeclarativeBase)`, a `get_db()` dependency that yields a session, and `init_db()` which runs `Base.metadata.create_all()` on start. |

### `app/models/` - database tables

| Path | Owner | Role |
|---|---|---|
| `models/<entity>.py` | DB | One SQLAlchemy 2.0 ORM class per table, subclassing `Base`, with typed columns (`Mapped[int] = mapped_column(...)`) and relationships. E.g. `workout.py` defines `Workout`. Matches `Architecture.tables`. |

### `app/repositories/` - data access

| Path | Owner | Role |
|---|---|---|
| `repositories/<entity>_repository.py` | DB | The only code that queries the DB, using a SQLAlchemy `Session` and 2.0-style `select()` queries (not `session.query`). Exposes functions like `create`, `get`, `list`, `update`, `delete` for one model. No business rules. |

### `app/schemas/` - API data shapes

| Path | Owner | Role |
|---|---|---|
| `schemas/<entity>.py` | Dev | Pydantic classes for what the API accepts and returns (e.g. `WorkoutCreate`, `WorkoutRead`). Validates input and keeps the API shape separate from the DB shape. |

### `app/services/` - business logic

| Path | Owner | Role |
|---|---|---|
| `services/<entity>_service.py` | Dev | The app's rules (e.g. "reps must be positive", "a set needs an existing exercise"). Calls repositories, never touches HTTP or SQL directly. |

### `app/routes/` - HTTP endpoints

| Path | Owner | Role |
|---|---|---|
| `routes/<entity>s.py` | Dev | FastAPI routers. Each endpoint reads the request, calls one service, returns the response. Matches `Architecture.endpoints`. No SQL, no business rules. |

### `app/static/` - frontend

| Path | Owner | Role |
|---|---|---|
| `static/index.html` | Dev | The page the user opens in the browser. |
| `static/css/style.css` | Dev | Styling. |
| `static/js/app.js` | Dev | Calls the API with `fetch` and updates the page. |

## `tests/` - automated tests

| Path | Owner | Role |
|---|---|---|
| `tests/conftest.py` | Dev | Shared test setup: a test client and a temporary database so tests never touch real data. |
| `tests/test_<entity>.py` | Dev | Tests for one entity's endpoints. The QA agent runs these and builds `QAReport` from the results. |

## `data/` - runtime data

| Path | Owner | Role |
|---|---|---|
| `data/.gitkeep` | Pkg | Keeps the empty folder in git. The SQLite `.db` file is created here at runtime. In Docker this folder is a volume so data survives restarts. |

## Root files - packaging and docs

| Path | Owner | Role |
|---|---|---|
| `requirements.txt` | Pkg | Python dependencies the app needs (`fastapi`, `uvicorn`, `sqlalchemy>=2.0`, ...). Used by `pip install` and the Dockerfile. |
| `Dockerfile` | Pkg | Recipe to build the app image: Python base, install requirements, copy code, run uvicorn on port 8000. Used by the sandbox and by anyone deploying. |
| `.dockerignore` | Pkg | Files kept out of the image (caches, `.git`, local `.db`, `.env`). |
| `.gitignore` | Pkg | Files kept out of git (same idea, plus `.venv`). |
| `.env.example` | Pkg | Template of the environment variables the app reads, with safe sample values. Copy to `.env` to configure. |
| `README.md` | Pkg | What the app does, features, endpoints, tables, how to run locally and with Docker, assumptions and out-of-scope items. Built from `Requirements` and `Architecture`. |

## Ownership rules (summary)

- **DB Engineer:** `app/core/`, `app/models/`, `app/repositories/`
- **Developer:** `app/main.py`, `app/schemas/`, `app/services/`, `app/routes/`, `app/static/`, `tests/`
- **Packager:** all root files and `data/.gitkeep`
- Layers only call downward: routes -> services -> repositories. Routes never touch the DB directly.

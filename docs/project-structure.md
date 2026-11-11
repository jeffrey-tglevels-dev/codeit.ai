# Project Structure (this codebase)

This describes the multi-coding-agent application itself, not the apps it generates (see `generated-app-project-structure.md` for those).

**Status:** Phase 1 done. `models/`, the config files and the sample-app fixture in `tests/fixtures/` are implemented and tested; files for later phases (`agents/`, `codegen/`, `orchestrator/`, `packaging/`, `sandbox/`, `routes/`, `console/`) exist but are empty.

**Skeleton vs target:** the old design's files were renamed in Phase 1 (`db_engineer.py`/`developer.py`/`qa.py` -> `backend.py`/`frontend.py`/`tester.py`; `architecture.py`/`build.py` -> `contract.py`/`results.py`), so the layout below is the current one.

**What the app does:** takes an idea ("build a gym tracking app"), runs agents (PM, Architect, then Backend, Frontend and Tester in parallel) to build and test it, then delivers (A) a ZIP of the source and (B) a Docker image run in a local sandbox with a preview URL.

```
multi-coding-agent/
├── docs/
├── models/
├── agents/
├── codegen/
├── orchestrator/
├── packaging/
│   └── templates/
├── sandbox/
├── routes/
├── console/
├── tests/
├── workspace/
├── output/
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

Pipeline: `PM -> Architect -> (Backend ∥ Frontend ∥ Tester) -> checks + tests -> Tester review -> fix loop (max 3 rounds) -> Packager -> Sandbox preview`.

## `docs/` - design documents

| File | Role |
|---|---|
| `architecture.md` | What the system is and is not; agents, rules, fix loop, open items, build order. |
| `data-models.md` | Source of truth for all Pydantic models, the data flow, Contract validation and SQLAlchemy 2.0 rules. Code in `models/` follows it. |
| `generated-app-project-structure.md` | Layout of the apps our agents generate and who writes each file. |
| `decisions.md` | Dated log of design decisions and why they were made. |
| `project-structure.md` | This file. |
| `Essentials/` | Short summaries for the team: `PROJECT_BRIEF.md`, `MVP_DEFINITION.md`, `REQUIREMENTS.md`, `ARCHITECHTURE.md`, `DECISIONS.md`, and `IMPLEMENTATION.md` (the 4-phase plan). The detailed docs above win if they disagree. |

## `models/` - Pydantic data models

The data passed between steps. One file per stage of the data flow.

| File | Will hold |
|---|---|
| `request.py` | `UserRequest`, `Question`, `Inquiry` |
| `requirements.py` | `Feature`, `Requirements` |
| `contract.py` | `Field`, `Relation`, `Entity`, `Shape`, `Endpoint`, `Contract` (with validation) |
| `results.py` | `CodeResult`, `CheckResult` |
| `qa.py` | `TestResult`, `Failure`, `TestReport`, `TestVerdict`, `FixRequest` |
| `run.py` | `Run`, `RunEvent`, `OperatorMessage` |
| `delivery.py` | `ZipResult`, `SandboxResult`, `DeliveryResult` |
| `__init__.py` | Re-exports the models for easy import. |

## `agents/` - the LLM agents (CrewAI, models from OpenRouter)

Each file is one agent: reads one model, produces the next (see the data-flow table in `data-models.md`). The model each agent uses comes from config.

| File | Role |
|---|---|
| `pm.py` | Turns `UserRequest` into questions (`Inquiry`), then answers into `Requirements` with acceptance criteria. |
| `architect.py` | Turns `Requirements` into a `Contract` (entities and every endpoint); retries on validation errors. |
| `backend.py` | Writes `app/` except `static/` and `schemas/`; returns `CodeResult`. |
| `frontend.py` | Writes `app/static/`; returns `CodeResult`. |
| `tester.py` | Writes behavior tests from acceptance criteria; reviews its failing tests (`TestVerdict`). |
| `tools.py` | File tools (`read_file`, `write_file`, `list_files`, edit) limited to each agent's write scope; records `files_written`. |

## `codegen/` - generated from the Contract (plain code, no LLM)

| File | Role |
|---|---|
| `schemas.py` | Generates `app/schemas/<entity>.py` (Create/Read/Update and custom shapes). |
| `contract_tests.py` | Generates `tests/contract/` (one test per endpoint). |
| `test_setup.py` | Writes `tests/conftest.py` and the UI smoke test in `tests/ui/`. |

## `orchestrator/` - runs the whole pipeline

| File | Role |
|---|---|
| `pipeline.py` | asyncio. Calls the agents in order, runs Backend/Frontend/Tester in parallel (`asyncio.gather(..., return_exceptions=True)`), runs checks, routes failures by owner, re-runs only failed branches (max 3 rounds), enforces the budget cap, writes the event log, then calls packaging and the sandbox. |
| `checks.py` | DB schema check, backend `openapi.json` vs `Contract`, frontend `fetch` paths vs `Contract`, building `TestReport` from the pytest JSON report. |
| `routing.py` | Maps failures and Tester verdicts to owners (mostly by file path). |

## `packaging/` - ZIP and project files (plain code, no LLM)

| Path | Role |
|---|---|
| `packager.py` | Writes the root files into the generated project (`requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`, `.env.example`, `README.md`) and builds the source ZIP into `output/`. The ZIP never contains a Docker image. |
| `templates/Dockerfile.tmpl` | Template for the generated app's Dockerfile. |
| `templates/dockerignore.tmpl` | Template for `.dockerignore`. |
| `templates/gitignore.tmpl` | Template for `.gitignore`. |
| `templates/env.example.tmpl` | Template for `.env.example`. |
| `templates/README.md.tmpl` | Template for the generated app's README (filled from `Requirements` and `Contract`). |

## `sandbox/` - run generated code in Docker (plain code, no LLM)

| File | Role |
|---|---|
| `base.Dockerfile` | The prebuilt base image: Python, FastAPI, SQLAlchemy 2.0, uvicorn, pytest + JSON report, Playwright + Chromium, pinned versions. |
| `runner.py` | `run_check(run_id, command, timeout) -> CheckResult`: fresh container per check, workspace mounted read-only, tmpfs, no network, resource limits, non-root, labeled. Also builds and starts the preview container on a free `127.0.0.1` port and health-checks it. |
| `reaper.py` | Removes containers and images past their time limit (only those labeled as ours). |

## `routes/` - our own API

HTTP endpoints of this application: start a run, answer the PM's questions, get status and events, send an operator message, pause/resume/stop, download the ZIP, get the preview URL, stop a sandbox.

## `console/` - dev console

Static HTML/JS served by FastAPI. Operator-only, local, no login. Thin client over `routes/`.

## `tests/`

Tests for our application (models, Contract validation, codegen, checks, routing, sandbox, pipeline). Not the tests inside generated apps; those live in each generated project.

`tests/fixtures/expense_tracker/` holds a hand-written sample run: `requirements.json`, `contract.json` and the generated-app project `expense-tracker/`. Our pytest does not collect it (see `tests/fixtures/README.md`).

## Runtime folders

| Folder | Role |
|---|---|
| `workspace/` | Per-run scratch space: `workspace/<run_id>/<project>/` holds the generated project; `workspace/<run_id>/` also holds JSON artifacts and `events.jsonl`. Contents are gitignored; `.gitkeep` keeps the folder. |
| `output/` | Finished ZIPs, `output/<project>-<run_id>.zip`. Contents are gitignored; `.gitkeep` keeps the folder. |

## Root files

| File | Role |
|---|---|
| `.env.example` | Config template: OpenRouter API key, model per agent (`PM_MODEL`, `ARCHITECT_MODEL`, `BACKEND_MODEL`, `FRONTEND_MODEL`, `TESTER_MODEL`), budget cap, sandbox limits. |
| `requirements.txt` | Dependencies of this application (`pydantic`, `pydantic-settings`, `python-dotenv`, `docker`, `jinja2`, `crewai`, `fastapi`, `uvicorn[standard]`, `httpx`); full list with purpose in `README.md`. |
| `requirements-dev.txt` | Dev/test dependencies (`pytest`, `pytest-asyncio`, `ruff`). |
| `pyproject.toml` | pytest settings (test paths, `docker`/`llm` markers) and ruff settings. |
| `README.md` | Project overview, prerequisites, libraries, setup, config, workstreams and team conventions. |
| `.gitignore` | Ignores `workspace/*`, `output/*` (except `.gitkeep`), `__pycache__/`, `.venv/`, `.env`. |

## Naming note

Our top-level `models/` and `routes/` are unrelated to the generated app's `app/models/` and `app/routes/`. Generated code lives only under `workspace/<run_id>/`, so the names never collide.

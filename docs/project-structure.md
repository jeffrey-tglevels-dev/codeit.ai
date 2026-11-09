# Project Structure (this codebase)

This describes the multi-coding-agent application itself, not the apps it generates (see `generated-app-project-structure.md` for those).

**Status:** file skeleton only. Every `.py`, `.tmpl`, `requirements.txt` and `README.md` is currently empty; only `.gitignore` and `docs/` have content. Nothing is implemented yet.

**What the app does:** takes an idea ("build a gym tracking app"), runs agents (PM, Architect, DB Engineer, Developer, QA) to build it, then delivers (A) a ZIP of the source and (B) a Docker image run in a local sandbox with a preview URL.

```
multi-coding-agent/
├── docs/
├── models/
├── agents/
├── orchestrator/
├── packaging/
│   └── templates/
├── sandbox/
├── routes/
├── tests/
├── workspace/
├── output/
├── requirements.txt
├── README.md
└── .gitignore
```

Pipeline: `PM -> Architect -> DB Engineer -> Developer -> QA` (fix loop, max 3 rounds), then `Packager -> Sandbox`.

## `docs/` - design documents

| File | Role |
|---|---|
| `data-models.md` | Source of truth for all Pydantic models, the data flow, file ownership, and SQLAlchemy 2.0 rules. Code in `models/` follows it. |
| `generated-app-project-structure.md` | Layout of the apps our agents generate (layered: routes, services, repositories, models) and who writes each file. |
| `project-structure.md` | This file. |

## `models/` - Pydantic data models

The data passed between steps. One file per stage of the data flow.

| File | Will hold |
|---|---|
| `request.py` | `UserRequest`, `Question`, `Inquiry` |
| `requirements.py` | `Requirements` |
| `architecture.py` | `Column`, `Table`, `Endpoint`, `ProjectFile`, `Architecture` |
| `build.py` | `DbResult`, `BuildResult` |
| `qa.py` | `TestCase`, `Failure`, `QAReport` |
| `delivery.py` | `ZipResult`, `SandboxResult`, `DeliveryResult` |
| `__init__.py` | Re-exports the models for easy import. |

## `agents/` - the LLM agents

Each file is one agent: reads one model, produces the next (see the data-flow table in `data-models.md`).

| File | Role |
|---|---|
| `pm.py` | Turns `UserRequest` into questions (`Inquiry`), then answers into `Requirements`. |
| `architect.py` | Turns `Requirements` into `Architecture` (tables, endpoints, per-layer file list). |
| `db_engineer.py` | Writes `app/core/`, `app/models/`, `app/repositories/` of the generated app; returns `DbResult`. |
| `developer.py` | Writes schemas, services, routes, static files, `main.py`, tests; returns `BuildResult`. |
| `qa.py` | Runs the generated app's tests and checks; returns `QAReport` with failures routed by `owner`. |

## `orchestrator/` - runs the whole pipeline

| File | Role |
|---|---|
| `pipeline.py` | Calls the agents in order, runs the QA fix loop (max 3 rounds, routing each `Failure` to its owner), then calls packaging and the sandbox. Measures `schema_ok` and `app_starts` in code. |

## `packaging/` - ZIP and project files (plain code, no LLM)

| Path | Role |
|---|---|
| `packager.py` | Writes the root files into the generated project (`requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`, `.env.example`, `README.md`) and builds the source ZIP into `output/`. The ZIP never contains a Docker image. |
| `templates/Dockerfile.tmpl` | Template for the generated app's Dockerfile. |
| `templates/dockerignore.tmpl` | Template for `.dockerignore`. |
| `templates/gitignore.tmpl` | Template for `.gitignore`. |
| `templates/env.example.tmpl` | Template for `.env.example`. |
| `templates/README.md.tmpl` | Template for the generated app's README (filled from `Requirements` and `Architecture`). |

## `sandbox/` - run the generated app in Docker (plain code, no LLM)

| File | Role |
|---|---|
| `runner.py` | Uses the Docker SDK to build the image from the generated project, start a resource-limited container on a free `127.0.0.1` port, health-check it, and return `SandboxResult` with the preview URL. |
| `reaper.py` | Removes containers and images past their time limit (only those labeled as ours). |

## `routes/` - our own API

Empty for now. Will hold the HTTP endpoints of this application: start a run, answer the PM's questions, download the ZIP, get the preview URL, stop a sandbox.

## `tests/`

Tests for our application (models, packager, sandbox, pipeline). Not the tests inside generated apps; those are written by the Developer agent into each generated project.

## Runtime folders

| Folder | Role |
|---|---|
| `workspace/` | Per-run scratch space: `workspace/<run_id>/<project>/` holds the generated project that is zipped and built. Contents are gitignored; `.gitkeep` keeps the folder. |
| `output/` | Finished ZIPs, `output/<project>-<run_id>.zip`. Contents are gitignored; `.gitkeep` keeps the folder. |

## Root files

| File | Role |
|---|---|
| `requirements.txt` | Dependencies of this application (will include `pydantic`, `fastapi`, `docker`, and the LLM SDK). Empty now. |
| `README.md` | Project overview and how to run it. Empty now. |
| `.gitignore` | Ignores `workspace/*`, `output/*` (except `.gitkeep`), `__pycache__/`, `.venv/`, `.env`. |

## Naming note

Our top-level `models/` and `routes/` are unrelated to the generated app's `app/models/` and `app/routes/`. Generated code lives only under `workspace/<run_id>/`, so the names never collide.

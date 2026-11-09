# Architecture

Status: agreed. This is the reference for what the system is and is not. Data shapes live in `data-models.md`; folder layout in `project-structure.md`; the generated app's layout in `generated-app-project-structure.md`.

## What it does

Input: a one-line idea ("build me an expense tracker").
Output: a working, tested web app, delivered as a source ZIP plus a short-lived sandbox preview URL.

Five LLM agents, two non-LLM code stages, one orchestrator, one FastAPI API, one static dev console.

```
Operator --> console/ (static page) --> routes/ (FastAPI) --> orchestrator/pipeline.py
                                                                  |
 UserRequest -> [PM] -> Inquiry ==(operator answers)==> [PM] -> Requirements
 -> [Architect] -> Architecture -> [DB Engineer] -> DbResult -> [Developer] -> BuildResult
 -> [QA] -> QAReport --failures--> routed to Failure.owner (max 3 rounds)
 -> packaging/ (ZIP) + sandbox/ (Docker preview) -> DeliveryResult
```

## Layers

| Layer | Folder | LLM | Responsibility |
|---|---|---|---|
| Dev console | `console/` | no | Static HTML/JS served by FastAPI. Thin client, no logic. |
| API | `routes/` | no | Start run, questions/answers, status and events, operator messages, pause/resume/approve, ZIP download, preview URL, stop sandbox. |
| Orchestrator | `orchestrator/pipeline.py` | no | Sequences agents, owns the fix loop, run state, gates; calls packager and sandbox. |
| Agents | `agents/` | yes | PM, Architect, DB Engineer, Developer, QA. |
| Contracts | `models/` | no | Pydantic models passed between stages. |
| Delivery | `packaging/`, `sandbox/` | no | ZIP the source; build and run it in a limited Docker container with expiry. |
| Scratch/output | `workspace/`, `output/` | no | Per-run generated project; finished ZIPs. Gitignored. |

## Agents

| Agent | Reads | Produces | Writes files |
|---|---|---|---|
| PM | `UserRequest`, answered `Inquiry` | `Inquiry`, then `Requirements` | none |
| Architect | `Requirements` | `Architecture` | none |
| DB Engineer | `Architecture.tables` | `DbResult` | `app/core`, `app/models`, `app/repositories` |
| Developer | `Architecture`, `DbResult` | `BuildResult` | `app/main.py`, schemas, services, routes, static, tests |
| QA | `Requirements`, `Architecture`, `BuildResult` | `QAReport` | none |

Agents talk to each other only through these typed models, never directly.

## Rules

- **CrewAI supplies Agent, Task, tools and structured output. It does not own the workflow.** `pipeline.py` runs one small crew per stage (one agent, one task, `output_pydantic`) and passes typed models along. Human pauses, conditional re-runs and the round counter live in plain Python.
- **File-write tools** are sandboxed to `workspace/<run_id>/<project>/` and given only to DB Engineer and Developer.
- **Measured by code, never claimed by an agent:** `schema_ok`, `app_starts`, `image_built`, `healthy`.
- **Fix loop:** `dev` -> Developer. `db` -> DB Engineer, Developer. `architect` -> Architect, DB Engineer, Developer. `pm` -> PM and everything after. Max 3 rounds, then ship with the QA report attached.
- **Generated-app stack is fixed:** FastAPI, SQLAlchemy 2.0, SQLite, plain HTML/CSS/JS; layered routes -> services -> repositories -> database.
- **Run state:** in memory, plus JSON artifacts, events and operator messages under `workspace/<run_id>/`.

## Dev console (human in the loop)

Operator controls, all enforced by the orchestrator, not the page:

- Answer the PM's `Inquiry`.
- Send a message: a note injected as context into the next execution of a chosen agent (never mid-call).
- Moderate: optional approval gate after each stage; approve, or reject/edit with a note and re-run. Gates default off, so a run can be fully automatic.
- Pause, resume, stop; re-run from a chosen stage.
- View the live stage timeline and every typed artifact; ZIP and preview links.

## What it does NOT do (v1)

- Choose a tech stack: always the fixed stack above.
- Build auth or multi-user in generated apps (recorded in `out_of_scope`).
- Deploy or host anywhere. Delivery is a ZIP plus a short-lived local Docker preview. The ZIP has no Docker image.
- Modify an already-delivered app. Every run is a fresh build.
- Provide an end-user product UI or a CLI. The console is operator-only, local, no login.
- Keep run history across restarts (artifacts stay on disk, state does not).
- Repair more than 3 rounds, or promise a green QA. It reports honestly.
- Trust agent self-reports of success.
- Run generated code on the host. It runs only in the sandbox.

## Known gaps to fix in the docs and models before coding

1. Add `Run`, `RunEvent`, `OperatorMessage` models.
2. `ProjectFile.owner` duplicates `layer`; make it derived or validated.
3. `ProjectFile.layer` has no value for `app/main.py` and `tests/conftest.py`.
4. `Column` has no foreign key; add `references`.
5. Re-runs need failure feedback as input.
6. Define one plural/naming rule for route, schema and model file names.
7. Rename `TestCase` to `QACase` (pytest may try to collect it).
8. Make `DbResult.repository_functions` structured, or drop it.
9. `requirements.txt` will list `crewai`, `pydantic`, `fastapi`, `uvicorn`, `docker`.

## Build order

1. Update docs with the above.
2. `models/` plus unit tests.
3. `packaging/` and `sandbox/` against a hand-written sample app (no LLM needed).
4. Agents: PM and Architect first, then DB Engineer, Developer, QA.
5. `pipeline.py` with fix loop and event log, then `routes/`, then `console/`.

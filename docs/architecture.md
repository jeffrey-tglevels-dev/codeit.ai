# Architecture

Status: **draft**, in development. This is the current reference for what the system is and is not. Data shapes live in `data-models.md`; folder layout in `project-structure.md`; the generated app's layout in `generated-app-project-structure.md`; the dated reasoning behind each choice in `decisions.md`.

Goal: learning multi-agent orchestration first, while keeping the design able to grow into a reliable tool (agents sit behind typed models, so any of them can later be replaced by templates or code).

## What it does

Input: a one-line idea ("build me an expense tracker").
Output: a working, tested web app, delivered as a source ZIP plus a short-lived sandbox preview URL.

Five LLM agents (PM, Architect, Backend Engineer, Frontend Engineer, Tester), code-only stages (contract validation, code generation, checks, packaging, sandbox), one asyncio orchestrator, one FastAPI API, one static dev console.

```
 idea -> [PM] <-> operator answers -> Requirements
      -> [Architect] -> Contract -> validator (code; errors go back to the Architect)
      -> codegen (code): app/schemas/*.py, contract tests, tests/conftest.py, UI smoke test
      ┌─────────────────┬─────────────────┬─────────────────┐
      ▼                 ▼                 ▼                    asyncio.gather
 [Backend Eng]     [Frontend Eng]     [Tester]
 app/ minus static  app/static/        tests/ (behavior tests)
 checks: DB schema, check: fetch paths
 openapi.json ==    are in Contract
 Contract
      └─────────────────┴─────────────────┘
                        ▼
      run every test in a fresh sandbox container -> TestReport
                        ▼
      Tester reviews its own failing tests -> failures routed by code
      to backend | frontend | tester | architect
      (only failed branches re-run, max 3 rounds)
                        ▼
      packaging/ (ZIP) + sandbox/ (Docker preview) -> DeliveryResult
```

## Layers

| Layer | Folder | LLM | Responsibility |
|---|---|---|---|
| Dev console | `console/` | no | Static HTML/JS served by FastAPI. Thin client, no logic. |
| API | `routes/` | no | Start run, PM questions/answers, status and events, operator messages, pause/resume/stop, ZIP download, preview URL, stop sandbox. |
| Orchestrator | `orchestrator/pipeline.py` | no | asyncio. Sequences agents, runs the three parallel branches, owns the fix loop, run state, budget cap; calls checks, packager and sandbox. |
| Agents | `agents/` | yes | PM, Architect, Backend, Frontend, Tester. |
| Contracts | `models/` | no | Pydantic models passed between stages. |
| Codegen | `codegen/` | no | Generates schemas, contract tests, `conftest.py` and the UI smoke test from the `Contract`. |
| Checks + sandbox | `sandbox/` | no | Runs every check in a fresh, limited Docker container; builds and runs the preview with expiry. |
| Packaging | `packaging/` | no | Root files from templates; source ZIP. |
| Config | `.env` / config | no | Model per agent (OpenRouter), budget cap, limits. |
| Scratch/output | `workspace/`, `output/` | no | Per-run generated project, artifacts, events; finished ZIPs. Gitignored. |

## Agents

| Agent | Reads | Produces | Writes files |
|---|---|---|---|
| PM | `UserRequest`, answered `Inquiry` | `Inquiry`, then `Requirements` (features with acceptance criteria) | none |
| Architect | `Requirements` | `Contract` (entities, all endpoints) | none |
| Backend Eng | `Contract`, generated schemas | `CodeResult` | `app/` except `app/static/` and `app/schemas/` (includes `app/main.py`) |
| Frontend Eng | `Contract` | `CodeResult` | `app/static/` only |
| Tester | `Requirements`, `Contract` | `CodeResult`; later `list[TestVerdict]` when reviewing failures | `tests/test_<feature_id>_*.py` only |

Agents talk to each other only through these typed models, never directly. Backend and Frontend never see each other's code; the `Contract` is the only thing they share.

## Rules

- **CrewAI supplies Agent, Task, tools and structured output. It does not own the workflow.** `pipeline.py` runs one small crew per stage (one agent, one task, `output_pydantic`) and passes typed models along. Pauses, parallel branches, re-runs and the round counter live in plain Python.
- **LLMs come from OpenRouter** (through CrewAI's LiteLLM layer). The model for each agent is set in config, never in code, so models can be compared by changing config.
- **Orchestrator is asyncio.** Blocking CrewAI calls run through `asyncio.to_thread`. The three branches run with `asyncio.gather(..., return_exceptions=True)` (not `TaskGroup`, which would cancel the other branches when one fails). One lock guards shared run state and the event log.
- **Contract first.** The Architect writes every endpoint. Code validates the `Contract` (see `data-models.md`); validation errors go straight back to the Architect. Code then generates `app/schemas/*.py`, so neither engineer can drift from the agreed shapes.
- **File-write tools** are limited to each agent's write scope (table above) inside `workspace/<run_id>/<project>/`. The tool records `files_written`; agents only return notes.
- **Measured by code, never claimed by an agent:** DB schema check, backend `openapi.json` matches the `Contract`, frontend `fetch` paths are in the `Contract`, test results, `image_built`, `healthy`.
- **Generated code never runs on the host.** Every check runs in a fresh container (`docker run --rm`) from one prebuilt base image that holds the whole fixed stack (FastAPI, SQLAlchemy 2.0, uvicorn, pytest + JSON report, Playwright + Chromium). Workspace mounted read-only, tmpfs for `data/` and caches, no network, memory/CPU/process/time limits, non-root user, containers labeled with the run id.
- **No extra packages.** A generated `requirements.txt` must be a subset of what the base image contains; code enforces this.
- **Testing in three layers:** contract tests (generated by code), behavior tests (written by the Tester from acceptance criteria, black-box over HTTP), one UI smoke test (generated by code: page loads, no console errors, no failed requests). The Tester writes its tests while the engineers build. Tests stay frozen across fix rounds.
- **Fix loop.** The Tester first reviews its own failing tests (`test_wrong` / `code_wrong` / `contract_gap`). Remaining failures are routed mostly by file path:

  | Evidence | Owner |
  |---|---|
  | server traceback in `app/` (not `static/`), wrong status or shape on a Contract endpoint | backend |
  | JS console error in `app/static/`, `fetch` to a path not in the Contract | frontend |
  | Tester review says the test was wrong | tester |
  | both sides match the Contract but the feature still can't work | architect, then backend, frontend and tester as needed |

  The PM is never re-run automatically. Only branches with failures re-run; re-run agents receive a `FixRequest` and edit their existing files. Max 3 rounds, then ship with the test report attached.
- **Budget.** Token usage (and cost where available) is summed per run. Over the cap, the run stops, is marked failed with reason `budget`, and keeps all artifacts.
- **Generated-app stack is fixed:** FastAPI, SQLAlchemy 2.0, SQLite, plain HTML/CSS/JS; layered routes -> services -> repositories -> database.
- **Run state:** in memory, plus JSON artifacts, `events.jsonl` (including every LLM call) and operator messages under `workspace/<run_id>/`.

## Dev console (human in the loop)

Operator controls, all enforced by the orchestrator, not the page:

- Answer the PM's `Inquiry`.
- Send a message: a note injected as context into the next execution of a chosen agent (never mid-call).
- Pause, resume, stop.
- View the live stage timeline, branch status and every typed artifact; ZIP and preview links.

There are no approval gates in v1; runs are fully automatic after the PM's questions.

## What it does NOT do (v1)

- Choose a tech stack: always the fixed stack above.
- Install packages beyond the base image.
- Build auth or multi-user in generated apps (recorded in `out_of_scope`).
- Many-to-many relations, pagination or filtering frameworks in generated APIs.
- Browser flows beyond one UI smoke test.
- Approval gates between stages, or automatic re-runs of the PM.
- Deploy or host anywhere. Delivery is a ZIP plus a short-lived local Docker preview. The ZIP has no Docker image.
- Modify an already-delivered app. Every run is a fresh build.
- Provide an end-user product UI or a CLI. The console is operator-only, local, no login.
- Keep run history across restarts (artifacts stay on disk, state does not).
- Repair more than 3 rounds, exceed the budget cap, or promise a green test report. It reports honestly.
- Trust agent self-reports of success.
- Run generated code on the host.

## Open items to verify

1. CrewAI `output_pydantic` and tool calling work with the chosen OpenRouter models (models must support structured outputs and tools).
2. OpenRouter provider pinning for reproducible runs.
3. Token usage and cost are readable through CrewAI/LiteLLM (needed for the budget cap).
4. Rate limits with three branches calling at once; retry with backoff.
5. Whether CrewAI's `kickoff_async` is truly async or a thread wrapper.
6. Docker Desktop (WSL2) mount speed and path handling for `workspace/` on Windows.
7. OpenRouter provider data-logging settings.

## Build order

1. `models/` plus unit tests (including `Contract` validation).
2. Base image and `sandbox/runner.py` `run_check`, tested against a hand-written sample app (no LLM).
3. `codegen/` (schemas, contract tests, `conftest.py`, UI smoke test) and the backend/frontend contract checks, tested on the same sample app.
4. `packaging/` and preview sandbox.
5. Agents, one at a time: PM, Architect, then Backend, Frontend, Tester.
6. `pipeline.py` with parallel branches, fix loop, budget and event log; then `routes/`, then `console/`.
7. A fixed evaluation set of app ideas to compare prompts and models.

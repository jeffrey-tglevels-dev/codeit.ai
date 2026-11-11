# Implementation Plan

Four phases, derived from the build order in `docs/architecture.md`. Each phase ends with something testable. No LLM is used until Phase 3.

References: `docs/architecture.md`, `docs/data-models.md`, `docs/generated-app-project-structure.md`, `docs/project-structure.md`, `docs/decisions.md`.

---

## Phase 1: Foundations (typed models and skeleton cleanup)

**Goal:** every data shape exists as tested Pydantic code, and the repo layout matches the target design.

- **Skeleton cleanup:** rename the old-design files and add the missing folders:
  - `agents/db_engineer.py` and `developer.py` → `backend.py`, `frontend.py`, `tester.py`, `tools.py`
  - `models/architecture.py` and `build.py` → `contract.py`, `results.py`, `run.py`
  - add `codegen/`, `console/`, `orchestrator/checks.py`, `orchestrator/routing.py`, `sandbox/base.Dockerfile`
- **`models/`:** `UserRequest`, `Inquiry`, `Requirements`, `Contract`, `CodeResult`, `CheckResult`, `TestReport`, `TestVerdict`, `FixRequest`, `Run`, `RunEvent`, `OperatorMessage`, `DeliveryResult`.
- **Contract validation:** a `model_validator` with every rule in `data-models.md` §4:
  - unique names
  - path conventions
  - status codes that match the method
  - relation targets that exist
  - feature coverage, checked against `Requirements`
- **Config:** `.env.example` (OpenRouter key, model per agent, budget cap, sandbox limits), `requirements.txt` (crewai, pydantic, fastapi, uvicorn, docker), `.gitignore`.
- **Hand-written sample app:** an expense tracker that follows `generated-app-project-structure.md`. Phases 2 and 3 use it as a test fixture.

**Exit criteria:** `pytest tests/` passes. There are unit tests for every validation rule, both valid and invalid Contracts.

---

## Phase 2: Deterministic engine (sandbox, codegen, checks, packaging)

**Goal:** everything that doesn't use an LLM works end to end on the sample app.

- **`sandbox/base.Dockerfile`:** Python, FastAPI, SQLAlchemy 2.0, uvicorn, pytest with JSON report, Playwright and Chromium, all at pinned versions.
- **`sandbox/runner.py`:** `run_check()` runs each check in a fresh container with:
  - the workspace mounted read-only, and tmpfs for `data/` and caches
  - no network, and limits on memory, CPU, processes and time
  - a non-root user and a run-id label

  It also builds and starts the preview container on a free `127.0.0.1` port and health-checks it.
- **`sandbox/reaper.py`:** removes expired containers and images, but only ones carrying our label.
- **`codegen/`:**
  - `app/schemas/*.py` (Create/Read/Update and custom shapes)
  - `tests/contract/` (one test per endpoint)
  - `tests/conftest.py`
  - the UI smoke test
- **`orchestrator/checks.py`:**
  - `db_schema`
  - `backend_contract` (compares `openapi.json` to the Contract)
  - `frontend_contract` (checks `fetch` paths against the Contract)
  - turning the pytest JSON report into a `TestReport`
  - checking that the generated app's `requirements.txt` only lists packages the base image has
- **`packaging/`:** fill in the 5 templates and build `output/<slug>-<run_id>.zip`.
- **Settle open item 6:** how fast Docker Desktop (WSL2) mounts `workspace/`, and how it handles paths, on Windows.

**Exit criteria:** with no LLM involved, the sample app goes through codegen, all checks, tests in the sandbox, the ZIP and a healthy preview URL. A deliberately broken copy of the sample app fails the right checks.

---

## Phase 3: Agents (one at a time, in pipeline order)

**Goal:** each agent turns its input model into its output model reliably.

- **Verify open items 1–5 and 7 first.** Do a small CrewAI test with the chosen OpenRouter models: does `output_pydantic` work? Do tool calls work? Can token usage and cost be read? How do rate limits and retries behave? Is `kickoff_async` really async? What are the data-logging settings?
- **`agents/tools.py`:** `read_file`, `write_file`, `list_files` and edit. Each tool is limited to one agent's write scope and records `files_written`.
- **Build each agent and test it alone:**
  1. **PM:** `UserRequest` → `Inquiry` → `Requirements` with acceptance criteria.
  2. **Architect:** `Requirements` → `Contract`, with a retry loop that sends validation errors back to it.
  3. **Backend:** writes `app/` (all but `static/` and `schemas/`) in SQLAlchemy 2.0 style. Must pass `db_schema` and `backend_contract`.
  4. **Frontend:** writes `app/static/`. Must pass `frontend_contract` and the UI smoke test.
  5. **Tester:** writes `test_<feature_id>_*.py`, and later reviews its own failing tests and returns `TestVerdict`s.

**Exit criteria:** each agent, given a stored fixture input, produces valid output, and the Phase 2 checks pass on what it writes. Every LLM call is logged.

---

## Phase 4: Orchestration, API, console and evaluation

**Goal:** a one-line idea becomes a ZIP plus a preview through the dev console.

- **`orchestrator/pipeline.py`:**
  - asyncio, with stages run in order
  - Backend, Frontend and Tester run in parallel via `asyncio.gather(..., return_exceptions=True)`
  - a lock around run state, and `events.jsonl`
  - the budget cap: over budget, the run stops with status `failed: budget` and keeps its artifacts
  - pause, resume and stop
  - operator messages injected into the chosen agent's next run
- **`orchestrator/routing.py`:**
  - Tester verdicts and file-path evidence decide the owner of each failure
  - each owner gets a `FixRequest`, and only failed branches re-run
  - at most 3 rounds, then ship with the test report attached
- **`routes/`:**
  - start a run
  - answer the PM's questions
  - status and events
  - operator message
  - pause, resume, stop
  - ZIP download, preview URL, stop the sandbox
- **`console/`:** static HTML/JS: an answer form for the PM's questions, a stage timeline, branch status, an artifact viewer, and ZIP and preview links.
- **Evaluation set:** a fixed list of app ideas, such as todo, expense, gym and notes apps, for comparing prompts and models by pass rate, rounds, tokens and cost.

**Exit criteria:** at least 3 ideas from the eval set run end to end through the console and produce a healthy preview.

---

## Related

- Scope and "done" for the whole MVP: [`MVP_DEFINITION.md`](MVP_DEFINITION.md)
- Libraries, setup and how to split the work: [`README.md`](../../README.md)

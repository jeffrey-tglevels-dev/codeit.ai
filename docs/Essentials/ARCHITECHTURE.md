# High-Level System Architecture

Short summary. The full reference is [`docs/architecture.md`](../architecture.md); data shapes are in [`docs/data-models.md`](../data-models.md). If this file and those disagree, those win.

**Flow:**
`Dev console` → `API` → `Orchestrator` → `Agents (via OpenRouter)` → `Workspace` → `Checks + tests in Docker sandbox` → `Fix loop` → `Packaging (ZIP)` → `Sandbox preview`

---

### Core pipeline summary

1. **Dev console and API:** the operator enters an idea in the console (static HTML/JS). The FastAPI API starts a run (`run_id`) and streams status and events back.
2. **PM:** asks the operator one round of questions (`Inquiry`), then writes `Requirements` (features with acceptance criteria).
3. **Architect:** turns `Requirements` into a `Contract` (entities and every endpoint). Code validates it; errors go back to the Architect.
4. **Codegen (code, no LLM):** generates `app/schemas/`, contract tests, `tests/conftest.py` and a UI smoke test from the `Contract`.
5. **Build in parallel:** Backend Engineer (`app/` minus `static/` and `schemas/`), Frontend Engineer (`app/static/`) and Tester (behavior tests) work at the same time, sharing only the `Contract`.
6. **Checks and tests (code):** every check runs in a fresh, locked-down Docker container from one prebuilt base image. Generated code never runs on the host.
7. **Fix loop:** the Tester reviews its own failing tests; remaining failures are routed by code to backend, frontend, tester or architect. Only failed branches re-run, max 3 rounds.
8. **Packaging and preview (code):** root files from templates, then a source ZIP in `output/`. A Docker preview runs on a free local port and expires after a time limit. The ZIP never contains a Docker image.

### Key facts

- **Agents:** PM, Architect, Backend Engineer, Frontend Engineer, Tester. Built on CrewAI; the workflow is plain Python asyncio.
- **LLMs:** all come from **OpenRouter** through CrewAI's LiteLLM layer. The model for each agent is set in config, never in code.
- **Generated-app stack (fixed):** FastAPI, SQLAlchemy 2.0, SQLite, plain HTML/CSS/JS.
- **Budget cap:** a run over budget stops, is marked failed (`budget`) and keeps its artifacts.

# codeit.ai

A multi-agent coding system. You give it a one-line idea ("build me an expense tracker"). Five LLM agents (PM, Architect, Backend, Frontend, Tester) turn it into a working, tested web app, delivered as:

- **A source ZIP** in `output/<slug>-<run_id>.zip`
- **A short-lived local preview**: the app runs in a Docker container at a `http://localhost:<port>` URL

Generated apps always use the same stack: **FastAPI + SQLAlchemy 2.0 + SQLite + plain HTML/CSS/JS**.

> **Status:** Phase 1 done: typed models, Contract validation, config and a sample-app fixture (`tests/fixtures/`). Agents, codegen, sandbox and the pipeline are still empty skeletons. See [Implementation plan](docs/Essentials/IMPLEMENTATION.md).

---

## 1. Read these first

Read the docs in this order. They are the source of truth: if code and docs disagree, fix one of them in the same PR.

| Doc | What it tells you |
|---|---|
| [docs/architecture.md](docs/architecture.md) | What the system is and is not, the agents, the rules, the fix loop, open items |
| [docs/data-models.md](docs/data-models.md) | Every Pydantic model, the data flow, Contract validation rules, SQLAlchemy 2.0 rules |
| [docs/project-structure.md](docs/project-structure.md) | What each folder and file in **this** repo does |
| [docs/generated-app-project-structure.md](docs/generated-app-project-structure.md) | Layout of the apps we **generate**, and who writes each file |
| [docs/decisions.md](docs/decisions.md) | Dated log of design decisions and why they were made |
| [docs/Essentials/IMPLEMENTATION.md](docs/Essentials/IMPLEMENTATION.md) | The 4-phase plan and exit criteria for each phase |
| [docs/Essentials/](docs/Essentials/) | Short summaries: project brief, MVP definition, requirements, architecture, decisions |

> The files in `docs/Essentials/` are short summaries. Where they and the detailed docs above disagree, the detailed docs win, and the summary should be fixed.

---

## 2. Prerequisites (install once)

| Tool | Version | Why | Check |
|---|---|---|---|
| **Python** | 3.12 (recommended) | Runs this app. Use 3.12 unless the team agrees otherwise: newer versions (3.13, 3.14) may not be supported by CrewAI and its dependencies yet. | `python --version` |
| **Docker Desktop** | Recent, **WSL2 backend** on Windows | Runs every check, test and preview in containers. Generated code never runs on the host. | `docker --version` and `docker run --rm hello-world` |
| **Git** | Any recent version | Source control | `git --version` |
| **OpenRouter account and API key** | n/a | All LLM calls go through OpenRouter (needed from Phase 3) | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Code editor** | VS Code recommended (Python and Ruff extensions) | Editing | n/a |

On Windows, keep the repo on a local drive and make sure Docker Desktop is allowed to mount that drive. Mount speed and path handling are still being checked (open item 6 in `architecture.md`).

---

## 3. Libraries

### 3a. This application (install in your virtualenv)

These are in the root `requirements.txt`.

| Library | Used for | Phase |
|---|---|---|
| `pydantic` (v2) | All typed models in `models/` and Contract validation | 1 |
| `pydantic-settings` | Reading config from `.env` (models per agent, budget, limits) | 1 |
| `python-dotenv` | Loading `.env` during local development | 1 |
| `docker` (Docker SDK for Python) | `sandbox/runner.py` and `reaper.py`: running checks, building and running previews | 2 |
| `jinja2` | Rendering `packaging/templates/*.tmpl` and codegen output (or use `string.Template` if the team prefers no extra dependency) | 2 |
| `crewai` | Agent, Task, tools, structured output (`output_pydantic`). Brings in **LiteLLM**, which handles OpenRouter. | 3 |
| `fastapi` | Our API in `routes/`, and serving `console/` | 4 |
| `uvicorn[standard]` | Running our FastAPI app | 4 |
| `httpx` | Health-checking previews, and FastAPI's `TestClient` | 2–4 |

**Dev / test only** (can go in `requirements-dev.txt`):

| Library | Used for |
|---|---|
| `pytest` | Tests for this app (`tests/`) |
| `pytest-asyncio` | Testing the asyncio orchestrator |
| `ruff` | Linting and formatting |

### 3b. Sandbox base image (inside Docker, NOT on your machine)

Built from `sandbox/base.Dockerfile` in Phase 2. Every generated app runs on it, so a generated app's `requirements.txt` **may only list packages from this list** (code enforces it). Pin exact versions in the Dockerfile.

| Library | Used for |
|---|---|
| `fastapi` | The generated app's backend |
| `uvicorn` | Running the generated app |
| `sqlalchemy>=2.0` | ORM (2.0 style only, see `data-models.md`) |
| `pydantic` (v2) | Generated `app/schemas/` |
| `httpx` | `TestClient` in generated tests |
| `pytest` | Running generated tests |
| `pytest-json-report` | Machine-readable test results turned into `TestReport` |
| `playwright` + Chromium (`playwright install --with-deps chromium`) | The UI smoke test |

SQLite needs no install; it ships with Python.

---

## 4. Local setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd multi-coding-agent

# 2. Create and activate a virtualenv (Python 3.12)
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Git Bash / macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Create your local config
cp .env.example .env      # then fill in your OpenRouter key
```

Later phases add these steps:

```bash
# Phase 2: build the sandbox base image (tag name TBD in Phase 2)
docker build -f sandbox/base.Dockerfile -t codeit-sandbox-base .

# Phase 4: run the app and open the dev console
uvicorn main:app --reload   # entry module name TBD in Phase 4
```

---

## 5. Configuration (`.env`)

`.env` is gitignored; never commit it. `.env.example` lists every key.

| Variable | Meaning | Example |
|---|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter key | `sk-or-...` |
| `PM_MODEL` | Model for the PM agent | `openrouter/<provider>/<model>` |
| `ARCHITECT_MODEL` | Model for the Architect | same format |
| `BACKEND_MODEL` | Model for the Backend Engineer | same format |
| `FRONTEND_MODEL` | Model for the Frontend Engineer | same format |
| `TESTER_MODEL` | Model for the Tester | same format |
| `BUDGET_USD` (or token cap) | The run stops with status `failed: budget` above this | `1.00` |
| `MAX_FIX_ROUNDS` | Fix-loop limit | `3` |
| Sandbox limits | Memory, CPU, timeout, preview lifetime | set in Phase 2 |

Models are always set in config, never hard-coded. Chosen models must support **structured outputs and tool calling** (open item 1).

---

## 6. Repo layout (target)

```
multi-coding-agent/
├── docs/            design docs (start here)
├── models/          Pydantic models passed between stages
├── agents/          PM, Architect, Backend, Frontend, Tester (CrewAI) + file tools
├── codegen/         generates schemas and tests from the Contract (no LLM)
├── orchestrator/    asyncio pipeline, checks, failure routing
├── packaging/       templates + source ZIP builder
├── sandbox/         base image, run_check, preview, reaper
├── routes/          our FastAPI endpoints
├── console/         static HTML/JS dev console
├── tests/           tests for THIS app
├── workspace/       per-run generated projects (gitignored)
└── output/          finished ZIPs (gitignored)
```

The skeleton now matches this layout (renamed in Phase 1). Files for later phases exist but are still empty.

---

## 7. Work breakdown: who can pick up what

The phases depend on each other through **typed models**, so once Phase 1 models are merged, most work can run in parallel.

| Workstream | Folder(s) | Depends on | Can start |
|---|---|---|---|
| **A. Models + Contract validation** | `models/`, `tests/` | nothing | Now |
| **B. Sample app fixture** (hand-written expense tracker) | `tests/fixtures/` | the docs only | Now |
| **C. Sandbox** (base image, `run_check`, preview, reaper) | `sandbox/` | B | Now (use B to test) |
| **D. Codegen** (schemas, contract tests, conftest, UI smoke test) | `codegen/` | A | After A |
| **E. Checks** (db_schema, backend/frontend contract, TestReport) | `orchestrator/checks.py` | A, B, C | After A |
| **F. Packaging** (templates, ZIP) | `packaging/` | A | After A |
| **G. CrewAI/OpenRouter spike** (open items 1–5, 7) | scratch, then `agents/` | an OpenRouter key | Now |
| **H. Agents** (PM → Architect → Backend / Frontend / Tester) | `agents/` | A, G (and D/E to validate output) | Phase 3 |
| **I. Pipeline + routing** | `orchestrator/` | A, E, H | Phase 4 |
| **J. API + console** | `routes/`, `console/` | A (can stub the pipeline) | Phase 4, or earlier with stubs |
| **K. Evaluation set** | `tests/eval/` | I | Phase 4 |

**To work independently:**
- Code against the **models in `models/`**, not against another person's implementation. If you need a model change, change `data-models.md` and `models/` in one PR and tell the team.
- Use the **sample app fixture** (B) and stored JSON fixtures of `Requirements` and `Contract` instead of waiting for real agents.
- Stub what you depend on (for example, a fake pipeline for J, or a fake LLM response for H).

---

## 8. Team conventions

**Branches and PRs**
- Never commit straight to `main`. Branch names: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`.
- One workstream per PR, kept small. Link the phase/workstream in the PR description.
- A PR is mergeable when tests pass, `ruff` is clean, and the docs are updated if behavior changed.
- Design changes get a new row in `docs/decisions.md` (date, decision, why).

**Code**
- Python 3.12, type hints everywhere, Pydantic v2.
- `ruff check .` and `ruff format .` before pushing.
- Agents never claim success. Anything like `passed`, `files_written`, `all_passed`, `healthy` is set **by code** only.
- Generated code **never runs on the host**; always go through `sandbox/runner.py`.
- No model names, keys or limits in code; they all come from config.

**Testing**
- `pytest` from the repo root.
- Phases 1–2 tests must not need an LLM or network. Mark tests that need Docker (for example `@pytest.mark.docker`) and tests that need an LLM (`@pytest.mark.llm`) so they can be skipped.

---

## 9. Scope of v1 (short version)

**In scope:** one idea → PM questions → automatic build by 5 agents → checks and tests in Docker → up to 3 fix rounds → ZIP + local preview, driven from an operator-only dev console.

**Out of scope:** choosing another tech stack, extra packages beyond the base image, auth or multi-user in generated apps, deploying or hosting, modifying an already-delivered app, Docker image inside the ZIP, keeping run history across restarts, login for the console.

Full list: [docs/architecture.md → What it does NOT do](docs/architecture.md).

---

## 10. Open items (need an owner)

From `docs/architecture.md`:

1. CrewAI `output_pydantic` and tool calling work with the chosen OpenRouter models
2. OpenRouter provider pinning for reproducible runs
3. Token usage and cost are readable through CrewAI/LiteLLM (needed for the budget cap)
4. Rate limits with three branches calling at once; retry with backoff
5. Whether CrewAI's `kickoff_async` is truly async or a thread wrapper
6. Docker Desktop (WSL2) mount speed and path handling on Windows
7. OpenRouter provider data-logging settings

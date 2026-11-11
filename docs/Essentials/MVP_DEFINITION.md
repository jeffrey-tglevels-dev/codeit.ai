# MVP Definition (v1)

## The MVP in one sentence
An operator types a one-line app idea into a local dev console, answers the PM's questions, and gets back a tested FastAPI + SQLite + HTML/CSS/JS app as a source ZIP and a live local Docker preview, with no further input.

## Must have

| Area | Requirement |
|---|---|
| Input | One-line idea; one round of PM questions answered by the operator |
| Agents | PM, Architect, Backend Engineer, Frontend Engineer, Tester (CrewAI, LLMs via OpenRouter) |
| Contract | Validated by code; schemas and contract tests generated from it |
| Build | Backend, Frontend and Tester run in parallel |
| Verification | DB schema check, backend `openapi.json` vs Contract, frontend `fetch` paths vs Contract, contract + behavior + UI smoke tests, all in a Docker sandbox |
| Fix loop | Tester review, routing by code, only failed branches re-run, max 3 rounds |
| Delivery | Source ZIP in `output/`; local preview URL that expires |
| Console | Answer questions, see stage/branch status and artifacts, send operator notes, pause/resume/stop, preview and ZIP links |
| Safety and cost | Generated code never runs on the host; per-run budget cap |

## Done when

- At least 3 ideas from the evaluation set (for example todo, expense tracker, gym tracker) run end to end through the console and produce a healthy preview.
- Every run ends with an honest test report, whether or not all tests pass.

## Not in the MVP

Modifying an existing app, deployment, Docker image download, auth or multi-user (console or generated apps), other tech stacks, extra packages, many-to-many relations, pagination, approval gates, run history across restarts.

See [`IMPLEMENTATION.md`](IMPLEMENTATION.md) for how to build it, and [`docs/architecture.md`](../architecture.md) for the full design.

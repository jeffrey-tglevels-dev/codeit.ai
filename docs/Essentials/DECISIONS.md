To reduce ambiquity and keep built application more predictable and stable and to reduce possible dependency issues we use predefined tech stack.
Techstack: HTML,CSS, JS + FASTAPI, SQLALCHEMY,SQLITE
# Key Decisions (summary)

Short summary. The full dated log with reasons is [`docs/decisions.md`](../decisions.md); add new decisions there, not here.

- **Fixed tech stack for generated apps:** HTML, CSS, JS + FastAPI, SQLAlchemy 2.0, SQLite. A predefined stack keeps built apps predictable and stable and avoids dependency issues. Generated apps may only use packages from the sandbox base image.
- **Five agents:** PM, Architect, Backend Engineer, Frontend Engineer, Tester. Backend and frontend split cleanly at the HTTP API, so they (and the Tester) run in parallel.
- **Contract first:** the Architect writes a typed `Contract`; code validates it and generates the request/response schemas so no agent can drift from it.
- **CrewAI for agents, plain asyncio for the workflow.**
- **LLMs via OpenRouter;** model per agent set in config.
- **Generated code never runs on the host:** all checks and the preview run in Docker containers.
- **Success is measured by code, never claimed by an agent.**
- **Fix loop:** only failed branches re-run, max 3 rounds; then ship with the test report attached.
- **Delivery:** source ZIP plus a short-lived local Docker preview. No Docker image download.
- **Budget cap:** over budget, stop the run, mark it failed, keep artifacts.

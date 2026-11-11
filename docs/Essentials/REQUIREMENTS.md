# Requirements (v1)

Data shapes for everything below are in [`docs/data-models.md`](../data-models.md); the design is in [`docs/architecture.md`](../architecture.md).

## What v1 includes

1. A simple GUI (the local **dev console**) where the operator interacts with the system.
2. Take a user request, for example "make a diet noting application".
3. The **PM agent** asks relevant questions (one round), for example which fields, whether a graph is wanted, with suggested answers.
4. The operator answers. The PM writes `Requirements`: features with testable acceptance criteria. (No approval gate in v1; the run continues automatically after the answers.)
5. The **Architect** turns `Requirements` into a `Contract` (entities and every endpoint). Code validates it and generates the API schemas.
6. The **Backend Engineer** writes the backend, including the SQLAlchemy models and the database setup. The **Frontend Engineer** writes the HTML/CSS/JS. The **Tester** writes behavior tests. All three run in parallel on the fixed stack.
7. Code runs all checks and tests in a Docker sandbox. The Tester reviews its failing tests; failures are routed back to the right agent (max 3 fix rounds).
8. Packaging builds a source ZIP (with a `Dockerfile` inside).
9. The app is previewed by running it in a local Docker container.

**Output:** a demo app running in a local Docker preview, and a download of the source ZIP.

## What v1 won't do

- Modify an already-built project (every run is a fresh build).
- Deploy or host anywhere.
- Offer the Docker image for download (the ZIP has a `Dockerfile`; the image is only used for the preview).
- Store projects or run history in a DB (artifacts stay on disk under `workspace/` and `output/`).
- Registration and login, either for the console or in generated apps.
- Choose a different tech stack.

Full list: [`docs/architecture.md` → What it does NOT do](../architecture.md).

## Frontend (dev console) functional requirements

- Textbox: the operator enters the idea.
- Status: which stage and which agent is working (live stage timeline and branch status).
- Question form: the operator sees and answers the PM's questions.
- Operator controls: send a note to an agent's next run; pause, resume, stop.
- Preview button: open the preview URL of the built app.
- Download button: download the source ZIP.
- Artifact viewer: see each typed artifact (requirements, contract, test report).

## Backend functional requirements

- API to start a run with the user's idea.
- API to get the PM's questions and submit answers.
- API for status and events, operator messages, and pause/resume/stop.
- 5 agents: PM, Architect, Backend Engineer, Frontend Engineer, Tester. LLMs via OpenRouter, model per agent in config.
- Checks and tests run by code in the sandbox; the Tester reviews failures, and code routes them to backend, frontend, tester or architect.
- Packaging of the application into a source ZIP.
- Docker sandbox runner for checks and the preview.
- API to get the preview URL and stop the preview.
- API to download the application ZIP.
- Budget cap per run.

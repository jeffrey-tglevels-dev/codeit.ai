# High-Level System Architecture

**Flow:**  
`UI` $\rightarrow$ `API` $\rightarrow$ `Orchestrator` $\rightarrow$ `Workspace` $\rightarrow$ `Cleaning` $\rightarrow$ `Packaging` $\rightarrow$ `Storage` $\rightarrow$ `Preview`

---

### Core Pipeline Summary

1. **API & Orchestrator:** Receives prompt, creates `job_id`, streams progress to UI, manages 5 agents (PM, Architect, DB Eng, Dev, Tester).
2. **Workspace:** Dev writes code; Tester verifies execution within a fixed stack (**FastAPI + HTML/CSS/JS + SQLite**).
3. **Cleaning:** Purges runtime junk (`__pycache__`, `.pytest_cache`) and creates a fresh, empty `app.db`.
4. **Packaging:** Reads standard `project_meta.json`, injects Dockerfile, zips clean codebase, and builds Docker image.
5. **Storage & Preview:** Stores `.zip` download link, spins up Docker container on a dynamic port for live web preview.

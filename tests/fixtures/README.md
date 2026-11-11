# Test fixtures

## `expense_tracker/`

Laid out like `workspace/<run_id>/` so later phases can point at it as if it were a real run:

| Path | What it is |
|---|---|
| `requirements.json` | The `Requirements` the PM would produce (features F1-F6 with acceptance criteria). |
| `contract.json` | The `Contract` the Architect would produce. Valid against `requirements.json`. |
| `expense-tracker/` | A hand-written app that follows `docs/generated-app-project-structure.md` and the Contract. It stands in for the Backend, Frontend, Tester, Codegen and Packager output. |

`app/schemas/*.py`, `tests/conftest.py`, `tests/contract/` and `tests/ui/` are hand-written here, but show what
`codegen/` must generate in Phase 2. Custom shapes go in `app/schemas/custom.py` as
`<EndpointIdInCamelCase><Request|Response>`.

Our own `pytest` does not collect this folder (`norecursedirs` in `pyproject.toml`). The sample app's tests
normally run in the sandbox. To run them on the host while developing:

```bash
cd tests/fixtures/expense_tracker/expense-tracker
pip install -r requirements.txt pytest httpx
pytest --rootdir=. --confcutdir=.      # keeps the repo's tests/conftest.py out
```

The UI smoke test is skipped unless Playwright and Chromium are installed.

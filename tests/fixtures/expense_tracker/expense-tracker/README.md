# Expense Tracker

Track personal expenses by category and see how much was spent each month.

> Hand-written test fixture for codeit.ai (Phase 1). It follows
> `docs/generated-app-project-structure.md` exactly and stands in for agent output in Phases 2 and 3.

## Features

| Id | Feature |
|---|---|
| F1 | Add an expense |
| F2 | List and view expenses |
| F3 | Edit an expense |
| F4 | Delete an expense |
| F5 | Manage categories |
| F6 | Monthly summary |

## Entities

- **category**: `name` (text, unique)
- **expense**: `amount` (real), `description` (text), `date` (date), `note` (text, optional), `category_id` -> category

## Endpoints

| Method | Path | Summary |
|---|---|---|
| GET | `/api/categories` | List all categories |
| POST | `/api/categories` | Create a category |
| DELETE | `/api/categories/{id}` | Delete a category that has no expenses |
| GET | `/api/expenses` | List all expenses, newest date first |
| GET | `/api/expenses/{id}` | Get one expense |
| POST | `/api/expenses` | Add an expense |
| PUT | `/api/expenses/{id}` | Edit an expense (partial update) |
| DELETE | `/api/expenses/{id}` | Delete an expense |
| GET | `/api/summary?month=YYYY-MM` | Total and count of expenses in one month |

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://localhost:8000
```

## Run with Docker

```bash
docker build -t expense-tracker .
docker run --rm -p 8000:8000 -v expense-data:/app/data expense-tracker
```

## Assumptions

- One currency for all expenses
- Dates have no time part

## Out of scope

- User accounts and login
- Multiple currencies
- Budgets and alerts

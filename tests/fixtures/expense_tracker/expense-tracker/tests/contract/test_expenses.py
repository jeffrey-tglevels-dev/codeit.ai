# Generated from the Contract. Do not edit.
from app.schemas.expense import ExpenseRead

from tests.contract.helpers import check_shape, create_category, create_expense


def test_list_expenses(client):
    create_expense(client)
    res = client.get("/api/expenses")
    assert res.status_code == 200
    check_shape(res.json(), ExpenseRead, many=True)


def test_get_expense(client):
    expense = create_expense(client)
    res = client.get(f"/api/expenses/{expense['id']}")
    assert res.status_code == 200
    check_shape(res.json(), ExpenseRead)


def test_create_expense(client):
    category = create_category(client)
    payload = {
        "amount": 9.99,
        "description": "Coffee",
        "date": "2026-11-01",
        "note": "with a friend",
        "category_id": category["id"],
    }
    res = client.post("/api/expenses", json=payload)
    assert res.status_code == 201
    check_shape(res.json(), ExpenseRead)


def test_update_expense(client):
    expense = create_expense(client)
    res = client.put(f"/api/expenses/{expense['id']}", json={"description": "Dinner"})
    assert res.status_code == 200
    check_shape(res.json(), ExpenseRead)


def test_delete_expense(client):
    expense = create_expense(client)
    res = client.delete(f"/api/expenses/{expense['id']}")
    assert res.status_code == 204
    assert res.content == b""

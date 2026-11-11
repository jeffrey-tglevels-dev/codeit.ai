"""F4: Delete an expense."""


def test_F4_deleted_expense_is_gone(client):
    cid = client.post("/api/categories", json={"name": "Food"}).json()["id"]
    e = client.post(
        "/api/expenses",
        json={"amount": 3, "description": "Tea", "date": "2026-11-04", "category_id": cid},
    ).json()
    assert client.delete(f"/api/expenses/{e['id']}").status_code == 204
    assert client.get("/api/expenses").json() == []


def test_F4_missing_expense_returns_404(client):
    assert client.delete("/api/expenses/777").status_code == 404

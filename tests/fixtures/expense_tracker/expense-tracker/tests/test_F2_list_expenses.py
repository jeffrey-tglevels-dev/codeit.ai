"""F2: List and view expenses."""


def test_F2_list_is_newest_first(client):
    cid = client.post("/api/categories", json={"name": "Food"}).json()["id"]
    for day in ("2026-11-01", "2026-11-09", "2026-11-05"):
        client.post(
            "/api/expenses", json={"amount": 1, "description": day, "date": day, "category_id": cid}
        )
    dates = [e["date"] for e in client.get("/api/expenses").json()]
    assert dates == ["2026-11-09", "2026-11-05", "2026-11-01"]


def test_F2_missing_expense_returns_404(client):
    assert client.get("/api/expenses/12345").status_code == 404

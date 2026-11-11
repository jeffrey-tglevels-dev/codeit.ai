"""F1: Add an expense."""


def _category(client, name="Food"):
    return client.post("/api/categories", json={"name": name}).json()["id"]


def _payload(category_id, **overrides):
    data = {
        "amount": 20.0,
        "description": "Groceries",
        "date": "2026-11-03",
        "category_id": category_id,
    }
    data.update(overrides)
    return data


def test_F1_amount_must_be_positive(client):
    cid = _category(client)
    assert client.post("/api/expenses", json=_payload(cid, amount=0)).status_code == 400
    assert client.post("/api/expenses", json=_payload(cid, amount=-5)).status_code == 400


def test_F1_category_must_exist(client):
    assert client.post("/api/expenses", json=_payload(9999)).status_code == 400


def test_F1_new_expense_appears_in_list(client):
    cid = _category(client)
    created = client.post("/api/expenses", json=_payload(cid)).json()
    listed = client.get("/api/expenses").json()
    assert [e["id"] for e in listed] == [created["id"]]
    assert listed[0]["amount"] == 20.0

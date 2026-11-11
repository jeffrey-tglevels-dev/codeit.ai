"""F3: Edit an expense."""


def _expense(client):
    cid = client.post("/api/categories", json={"name": "Food"}).json()["id"]
    return client.post(
        "/api/expenses",
        json={"amount": 10, "description": "Lunch", "date": "2026-11-02", "category_id": cid},
    ).json()


def test_F3_single_field_can_change(client):
    e = _expense(client)
    res = client.put(f"/api/expenses/{e['id']}", json={"note": "team lunch"})
    assert res.status_code == 200
    body = res.json()
    assert body["note"] == "team lunch"
    assert body["description"] == "Lunch"
    assert body["amount"] == 10


def test_F3_amount_must_stay_positive(client):
    e = _expense(client)
    assert client.put(f"/api/expenses/{e['id']}", json={"amount": 0}).status_code == 400
    assert client.get(f"/api/expenses/{e['id']}").json()["amount"] == 10

"""F5: Manage categories."""


def test_F5_names_are_unique(client):
    assert client.post("/api/categories", json={"name": "Rent"}).status_code == 201
    assert client.post("/api/categories", json={"name": "Rent"}).status_code == 409


def test_F5_category_with_expenses_cannot_be_deleted(client):
    cid = client.post("/api/categories", json={"name": "Rent"}).json()["id"]
    client.post(
        "/api/expenses",
        json={"amount": 800, "description": "November", "date": "2026-11-01", "category_id": cid},
    )
    assert client.delete(f"/api/categories/{cid}").status_code == 409
    assert [c["id"] for c in client.get("/api/categories").json()] == [cid]

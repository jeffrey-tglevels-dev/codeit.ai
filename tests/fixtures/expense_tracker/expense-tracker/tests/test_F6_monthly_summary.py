"""F6: Monthly summary."""


def test_F6_total_and_count_for_month(client):
    cid = client.post("/api/categories", json={"name": "Food"}).json()["id"]
    for amount, day in ((10.5, "2026-11-01"), (4.5, "2026-11-30"), (100, "2026-12-01")):
        client.post(
            "/api/expenses",
            json={"amount": amount, "description": "x", "date": day, "category_id": cid},
        )
    body = client.get("/api/summary", params={"month": "2026-11"}).json()
    assert body == {"month": "2026-11", "total": 15.0, "count": 2}


def test_F6_empty_month_is_zero(client):
    body = client.get("/api/summary", params={"month": "2025-01"}).json()
    assert body["total"] == 0
    assert body["count"] == 0


def test_F6_bad_month_returns_400(client):
    for month in ("2026-13", "nov", "2026-1"):
        assert client.get("/api/summary", params={"month": month}).status_code == 400

# Generated from the Contract. Do not edit.
from app.schemas.category import CategoryRead

from tests.contract.helpers import check_shape, create_category


def test_list_categories(client):
    create_category(client)
    res = client.get("/api/categories")
    assert res.status_code == 200
    check_shape(res.json(), CategoryRead, many=True)


def test_create_category(client):
    res = client.post("/api/categories", json={"name": "Travel"})
    assert res.status_code == 201
    check_shape(res.json(), CategoryRead)


def test_delete_category(client):
    category = create_category(client)
    res = client.delete(f"/api/categories/{category['id']}")
    assert res.status_code == 204
    assert res.content == b""

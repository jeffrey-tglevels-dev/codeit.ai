# Generated from the Contract. Do not edit.
"""Sample payloads and shape checks shared by the contract tests."""

from typing import Any

from pydantic import BaseModel, TypeAdapter


def check_shape(body: Any, model: type[BaseModel], many: bool = False) -> None:
    """Fail if `body` does not fit the declared Shape."""
    if many:
        assert isinstance(body, list), f"expected a JSON array, got {type(body).__name__}"
        TypeAdapter(list[model]).validate_python(body)
    else:
        model.model_validate(body)


def create_category(client, name: str = "Food") -> dict:
    res = client.post("/api/categories", json={"name": name})
    assert res.status_code == 201, res.text
    return res.json()


def create_expense(client, **overrides: Any) -> dict:
    payload = {
        "amount": 12.5,
        "description": "Lunch",
        "date": "2026-11-05",
        "note": None,
    }
    payload.update(overrides)
    if "category_id" not in payload:
        payload["category_id"] = create_category(client)["id"]
    res = client.post("/api/expenses", json=payload)
    assert res.status_code == 201, res.text
    return res.json()

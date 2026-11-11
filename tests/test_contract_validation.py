"""Every Contract validation rule from docs/data-models.md §4, with valid and invalid cases.

Each invalid case starts from the valid expense-tracker Contract fixture, applies one mutation,
and checks that validation fails with the expected message.
"""

import copy
import json
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from models import Contract, Requirements, contract_errors, validate_contract

Data = dict[str, Any]


def ep(data: Data, endpoint_id: str) -> Data:
    return next(e for e in data["endpoints"] if e["id"] == endpoint_id)


def ent(data: Data, name: str) -> Data:
    return next(e for e in data["entities"] if e["name"] == name)


def assert_invalid(data: Data, expected: str, requirements: Requirements | None = None) -> None:
    ctx = {"requirements": requirements} if requirements else None
    with pytest.raises(ValidationError) as exc:
        Contract.model_validate(data, context=ctx)
    assert expected in str(exc.value), str(exc.value)


# --- valid contracts ------------------------------------------------------------------------


def test_fixture_contract_is_valid(contract_data: Data, requirements: Requirements) -> None:
    contract = validate_contract(contract_data, requirements)
    assert contract.entity("expense") is not None
    assert len(contract.endpoints) == 9


def test_fixture_contract_is_valid_from_json(contract_data: Data, requirements) -> None:
    assert validate_contract(json.dumps(contract_data), requirements).project_name


def test_feature_rules_are_skipped_without_requirements(contract_data: Data) -> None:
    ep(contract_data, "list_expenses")["features"] = ["F99"]
    Contract.model_validate(contract_data)  # no context -> no feature check


def test_minimal_valid_contract() -> None:
    Contract.model_validate(
        {
            "project_name": "Notes",
            "entities": [
                {"name": "note", "plural": "notes", "fields": [{"name": "text", "type": "text"}]}
            ],
            "endpoints": [
                {
                    "id": "list_notes",
                    "method": "GET",
                    "path": "/api/notes",
                    "summary": "List notes",
                    "features": ["F1"],
                    "response": {"entity": "note", "view": "read", "many": True},
                    "success_status": 200,
                }
            ],
        }
    )


def test_self_relation_and_declared_path_param_are_valid() -> None:
    Contract.model_validate(
        {
            "project_name": "Tree",
            "entities": [
                {
                    "name": "node",
                    "plural": "nodes",
                    "fields": [{"name": "label", "type": "text"}],
                    "relations": [{"field": "parent_id", "target": "node", "on_delete": "cascade"}],
                }
            ],
            "endpoints": [
                {
                    "id": "report",
                    "method": "GET",
                    "path": "/api/reports/{year}",
                    "summary": "Yearly report",
                    "features": ["F1"],
                    "query_params": [{"name": "year", "type": "integer"}],
                    "response": {"fields": [{"name": "count", "type": "integer"}]},
                    "success_status": 200,
                }
            ],
        }
    )


def test_all_errors_are_reported_at_once(contract_data: Data) -> None:
    ep(contract_data, "create_expense")["success_status"] = 200
    ep(contract_data, "list_expenses")["path"] = "/api/expense_list"
    ent(contract_data, "category")["fields"].append({"name": "id", "type": "integer"})
    with pytest.raises(ValidationError) as exc:
        Contract.model_validate(contract_data)
    message = str(exc.value)
    assert "success_status must be 201" in message
    assert "must live under /api/expenses" in message
    assert "field 'id' is implicit" in message


def test_contract_errors_returns_empty_list_for_valid(contract_data: Data, requirements) -> None:
    contract = Contract.model_validate(contract_data)
    assert contract_errors(contract, requirements) == []


# --- invalid contracts: one mutation per rule -----------------------------------------------

Mutation = Callable[[Data], None]


def _dup_entity_name(d: Data) -> None:
    ent(d, "category")["name"] = "expense"


def _dup_plural(d: Data) -> None:
    ent(d, "category")["plural"] = "expenses"


def _dup_endpoint_id(d: Data) -> None:
    ep(d, "get_expense")["id"] = "list_expenses"


def _dup_method_path(d: Data) -> None:
    e = copy.deepcopy(ep(d, "list_expenses"))
    e["id"] = "list_expenses_again"
    d["endpoints"].append(e)


def _dup_field_name(d: Data) -> None:
    ent(d, "expense")["fields"].append({"name": "amount", "type": "integer"})


def _field_named_id(d: Data) -> None:
    ent(d, "expense")["fields"].append({"name": "id", "type": "integer"})


def _bad_field_name(d: Data) -> None:
    ent(d, "expense")["fields"][0]["name"] = "Amount"


def _bad_entity_name(d: Data) -> None:
    ent(d, "expense")["name"] = "Expense"
    ep(d, "list_expenses")["response"]["entity"] = "Expense"


def _plural_equals_name(d: Data) -> None:
    ent(d, "category")["plural"] = "category"


def _unknown_relation_target(d: Data) -> None:
    ent(d, "expense")["relations"][0]["target"] = "wallet"


def _relation_clashes_with_field(d: Data) -> None:
    ent(d, "expense")["relations"][0]["field"] = "amount"


def _dup_relation_field(d: Data) -> None:
    rels = ent(d, "expense")["relations"]
    rels.append(dict(rels[0]))


def _unknown_shape_entity(d: Data) -> None:
    ep(d, "get_expense")["response"]["entity"] = "receipt"


def _get_with_body(d: Data) -> None:
    ep(d, "list_expenses")["request"] = {"entity": "expense", "view": "create"}


def _delete_with_body(d: Data) -> None:
    ep(d, "delete_expense")["request"] = {"entity": "expense", "view": "update"}


def _post_without_body(d: Data) -> None:
    del ep(d, "create_expense")["request"]


def _204_with_response(d: Data) -> None:
    ep(d, "delete_expense")["response"] = {"entity": "expense", "view": "read"}


def _no_response_not_204(d: Data) -> None:
    del ep(d, "get_expense")["response"]


def _post_status(d: Data) -> None:
    ep(d, "create_expense")["success_status"] = 200


def _delete_status(d: Data) -> None:
    e = ep(d, "delete_expense")
    e["success_status"] = 200
    e["response"] = {"fields": [{"name": "ok", "type": "boolean"}]}


def _get_status(d: Data) -> None:
    ep(d, "list_expenses")["success_status"] = 201


def _put_status(d: Data) -> None:
    ep(d, "update_expense")["success_status"] = 201


def _undeclared_path_param(d: Data) -> None:
    ep(d, "monthly_summary")["path"] = "/api/summary/{year}"


def _no_api_prefix(d: Data) -> None:
    ep(d, "list_expenses")["path"] = "/expenses"


def _bad_entity_path(d: Data) -> None:
    ep(d, "get_expense")["path"] = "/api/expenses/{id}/detail"


def _entity_path_wrong_param(d: Data) -> None:
    e = ep(d, "get_expense")
    e["path"] = "/api/expenses/{expense_id}"
    e["query_params"] = [{"name": "expense_id", "type": "integer"}]


def _entity_endpoint_outside_plural(d: Data) -> None:
    ep(d, "list_expenses")["path"] = "/api/all_expenses"


def _shape_entity_mismatches_path(d: Data) -> None:
    ep(d, "list_expenses")["response"]["entity"] = "category"


def _post_on_item_path(d: Data) -> None:
    ep(d, "create_expense")["path"] = "/api/expenses/{id}"


def _put_on_collection(d: Data) -> None:
    ep(d, "update_expense")["path"] = "/api/expenses"


def _request_view_read(d: Data) -> None:
    ep(d, "create_expense")["request"]["view"] = "read"


def _response_view_create(d: Data) -> None:
    ep(d, "create_expense")["response"]["view"] = "create"


def _request_many(d: Data) -> None:
    ep(d, "create_expense")["request"]["many"] = True


def _bad_endpoint_id(d: Data) -> None:
    ep(d, "list_expenses")["id"] = "list-expenses"


def _dup_query_param(d: Data) -> None:
    ep(d, "monthly_summary")["query_params"].append({"name": "month", "type": "text"})


def _dup_custom_shape_field(d: Data) -> None:
    ep(d, "monthly_summary")["response"]["fields"].append({"name": "total", "type": "integer"})


def _no_entities(d: Data) -> None:
    d["entities"] = []
    d["endpoints"] = [ep(d, "monthly_summary")]


INVALID_CASES: list[tuple[str, Mutation, str]] = [
    # uniqueness
    ("duplicate entity name", _dup_entity_name, "duplicate entity name 'expense'"),
    ("duplicate plural", _dup_plural, "duplicate entity plural 'expenses'"),
    ("duplicate endpoint id", _dup_endpoint_id, "duplicate endpoint id 'list_expenses'"),
    ("duplicate method+path", _dup_method_path, "duplicate endpoint GET /api/expenses"),
    ("duplicate field name", _dup_field_name, "duplicate field name 'amount'"),
    ("duplicate query param", _dup_query_param, "duplicate field name 'month'"),
    ("duplicate custom field", _dup_custom_shape_field, "duplicate field name 'total'"),
    ("duplicate relation field", _dup_relation_field, "duplicate relation field 'category_id'"),
    # naming
    ("field called id", _field_named_id, "field 'id' is implicit"),
    ("field not snake_case", _bad_field_name, "'Amount' must be snake_case"),
    ("entity not snake_case", _bad_entity_name, "'Expense' must be snake_case"),
    ("endpoint id not snake_case", _bad_endpoint_id, "'list-expenses' must be snake_case"),
    ("plural equals name", _plural_equals_name, "plural must differ"),
    ("no entities", _no_entities, "at least one entity"),
    # relations
    ("unknown relation target", _unknown_relation_target, "unknown entity 'wallet'"),
    ("relation clashes with field", _relation_clashes_with_field, "clashes with a field"),
    # shapes
    ("unknown shape entity", _unknown_shape_entity, "unknown entity 'receipt'"),
    ("request view read", _request_view_read, "must use view 'create' or 'update'"),
    ("response view create", _response_view_create, "must use view 'read'"),
    ("request is a list", _request_many, "request body must not be a list"),
    # bodies and status codes
    ("GET with body", _get_with_body, "GET must not have a request body"),
    ("DELETE with body", _delete_with_body, "DELETE must not have a request body"),
    ("POST without body", _post_without_body, "POST needs a request body"),
    ("204 with response", _204_with_response, "204 means response must be None"),
    ("no response but not 204", _no_response_not_204, "success_status must be 204"),
    ("POST not 201", _post_status, "success_status must be 201 for POST"),
    ("DELETE not 204", _delete_status, "success_status must be 204 for DELETE"),
    ("GET not 200", _get_status, "success_status must be 200 for GET"),
    ("PUT not 200", _put_status, "success_status must be 200 for PUT"),
    # paths
    ("undeclared path param", _undeclared_path_param, "path param {year} is not 'id'"),
    ("missing /api/ prefix", _no_api_prefix, "path must start with /api/"),
    ("extra segment on entity path", _bad_entity_path, "entity paths must be one of"),
    ("entity path not {id}", _entity_path_wrong_param, "entity paths must be one of"),
    ("entity endpoint elsewhere", _entity_endpoint_outside_plural, "must live under /api/expenses"),
    ("shape entity vs path", _shape_entity_mismatches_path, "path belongs to 'expense'"),
    ("POST on item path", _post_on_item_path, "POST creates on the collection path"),
    ("PUT on collection path", _put_on_collection, "PUT on an entity must use"),
]


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [pytest.param(m, e, id=name) for name, m, e in INVALID_CASES],
)
def test_invalid_contract(contract_data: Data, mutate: Mutation, expected: str) -> None:
    mutate(contract_data)
    assert_invalid(contract_data, expected)


# --- Shape structure (entity + view XOR fields) ---------------------------------------------


@pytest.mark.parametrize(
    ("shape", "expected"),
    [
        (
            {"entity": "expense", "view": "read", "fields": [{"name": "x", "type": "text"}]},
            "not both",
        ),
        ({}, "needs entity + view or fields"),
        ({"entity": "expense"}, "needs both entity and view"),
        ({"view": "read"}, "needs both entity and view"),
        ({"fields": []}, "at least one field"),
    ],
    ids=["both", "neither", "entity without view", "view without entity", "empty fields"],
)
def test_invalid_shape(contract_data: Data, shape: Data, expected: str) -> None:
    ep(contract_data, "get_expense")["response"] = shape
    assert_invalid(contract_data, expected)


def test_unknown_field_type_is_rejected(contract_data: Data) -> None:
    ent(contract_data, "expense")["fields"][0]["type"] = "money"
    assert_invalid(contract_data, "fields.0.type")


def test_unknown_method_is_rejected(contract_data: Data) -> None:
    ep(contract_data, "list_expenses")["method"] = "PATCH"
    assert_invalid(contract_data, "method")


# --- feature coverage (needs Requirements) --------------------------------------------------


def test_unknown_feature_id(contract_data: Data, requirements: Requirements) -> None:
    ep(contract_data, "list_expenses")["features"].append("F99")
    assert_invalid(contract_data, "unknown feature id 'F99'", requirements)


def test_feature_not_served(contract_data: Data, requirements: Requirements) -> None:
    ep(contract_data, "monthly_summary")["features"] = ["F2"]
    assert_invalid(contract_data, "feature 'F6' is not served by any endpoint", requirements)


def test_endpoint_without_features(contract_data: Data, requirements: Requirements) -> None:
    ep(contract_data, "get_expense")["features"] = []
    assert_invalid(contract_data, "must serve at least one feature", requirements)


def test_validate_contract_checks_features(contract_data: Data, requirements) -> None:
    ep(contract_data, "monthly_summary")["features"] = ["F2"]
    with pytest.raises(ValidationError, match="'F6' is not served"):
        validate_contract(contract_data, requirements)

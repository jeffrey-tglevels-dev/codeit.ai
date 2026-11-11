"""The Contract: single source of truth for Backend, Frontend and Tester (data-models.md §4).

Validation is done by code. Every rule violation is collected into one error message so the
Architect gets the full list in a single retry.

Feature coverage needs the `Requirements`; pass them through the validation context:

    Contract.model_validate(data, context={"requirements": requirements})

or use `validate_contract(data, requirements)`. Without a context, the feature rules are skipped.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, ValidationInfo, model_validator

from models.requirements import Requirements

FieldType = Literal["integer", "text", "real", "boolean", "date", "datetime"]
Method = Literal["GET", "POST", "PUT", "DELETE"]

IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")  # snake_case Python identifier
PATH_PARAM_RE = re.compile(r"\{([^{}]*)\}")
PATH_SEGMENT_RE = re.compile(r"^(?:[a-z0-9][a-z0-9_-]*|\{[a-z][a-z0-9_]*\})$")

EXPECTED_STATUS: dict[str, int] = {"GET": 200, "PUT": 200, "POST": 201, "DELETE": 204}


class Field(BaseModel):
    name: str  # snake_case: "amount"
    type: FieldType
    required: bool = True
    unique: bool = False
    description: str = ""  # helps the Frontend label form inputs


class Relation(BaseModel):
    """One-to-many only in v1."""

    field: str  # foreign-key column on this entity: "category_id"
    target: str  # entity name: "category"
    on_delete: Literal["cascade", "restrict", "set_null"] = "restrict"


class Entity(BaseModel):
    name: str  # singular snake_case: "expense"
    plural: str  # "expenses" -> table name and URL path
    fields: list[Field]  # `id` is implicit and never listed
    relations: list[Relation] = []


class Shape(BaseModel):
    """A request or response body: an entity view OR custom fields."""

    entity: str | None = None  # "expense"
    view: Literal["create", "update", "read"] | None = None  # which generated schema
    fields: list[Field] | None = None  # custom shape, e.g. a monthly summary
    many: bool = False  # list = plain JSON array, no pagination

    @model_validator(mode="after")
    def _entity_xor_fields(self) -> "Shape":
        is_entity = self.entity is not None or self.view is not None
        is_custom = self.fields is not None
        if is_entity and is_custom:
            raise ValueError("a Shape has either entity + view or fields, not both")
        if not is_entity and not is_custom:
            raise ValueError("a Shape needs entity + view or fields")
        if is_entity and (self.entity is None or self.view is None):
            raise ValueError("an entity Shape needs both entity and view")
        if is_custom and not self.fields:
            raise ValueError("a custom Shape needs at least one field")
        return self


class Endpoint(BaseModel):
    id: str  # "list_expenses"; becomes the FastAPI operation_id
    method: Method
    path: str  # "/api/expenses/{id}"
    summary: str
    features: list[str]  # Requirements feature ids this endpoint serves: ["F1"]
    query_params: list[Field] = []
    request: Shape | None = None
    response: Shape | None = None  # None => 204 No Content
    success_status: Literal[200, 201, 204]
    error_statuses: list[Literal[400, 404, 409, 422]] = []

    @property
    def path_params(self) -> list[str]:
        return PATH_PARAM_RE.findall(self.path)


class Contract(BaseModel):
    project_name: str
    entities: list[Entity]
    endpoints: list[Endpoint]

    @model_validator(mode="after")
    def _validate(self, info: ValidationInfo) -> "Contract":
        requirements = (info.context or {}).get("requirements")
        errors = contract_errors(self, requirements)
        if errors:
            raise ValueError("Contract is invalid:\n" + "\n".join(f"- {e}" for e in errors))
        return self

    def entity(self, name: str) -> Entity | None:
        return next((e for e in self.entities if e.name == name), None)

    def entity_by_plural(self, plural: str) -> Entity | None:
        return next((e for e in self.entities if e.plural == plural), None)


def validate_contract(data: dict[str, Any] | str, requirements: Requirements) -> Contract:
    """Parse and validate a Contract (dict or JSON string), including feature coverage."""
    ctx = {"requirements": requirements}
    if isinstance(data, str):
        return Contract.model_validate_json(data, context=ctx)
    return Contract.model_validate(data, context=ctx)


# --- rules -----------------------------------------------------------------------------------


def contract_errors(contract: Contract, requirements: Requirements | None = None) -> list[str]:
    """Every rule from data-models.md §4. Returns human-readable errors (empty = valid)."""
    errors: list[str] = []
    errors += _entity_errors(contract)
    for ep in contract.endpoints:
        errors += _endpoint_errors(contract, ep)
    errors += _uniqueness_errors(contract)
    if requirements is not None:
        errors += _feature_errors(contract, requirements)
    return errors


def _duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    dups: list[Any] = []
    for v in values:
        if v in seen and v not in dups:
            dups.append(v)
        seen.add(v)
    return dups


def _ident_errors(kind: str, name: str) -> list[str]:
    if IDENT_RE.match(name):
        return []
    return [f"{kind} {name!r} must be snake_case (lowercase letters, digits, underscores)"]


def _field_list_errors(where: str, fields: list[Field]) -> list[str]:
    errors: list[str] = []
    for f in fields:
        errors += _ident_errors(f"{where}: field", f.name)
    for dup in _duplicates([f.name for f in fields]):
        errors.append(f"{where}: duplicate field name {dup!r}")
    return errors


def _uniqueness_errors(c: Contract) -> list[str]:
    errors: list[str] = []
    for dup in _duplicates([e.name for e in c.entities]):
        errors.append(f"duplicate entity name {dup!r}")
    for dup in _duplicates([e.plural for e in c.entities]):
        errors.append(f"duplicate entity plural {dup!r}")
    for dup in _duplicates([ep.id for ep in c.endpoints]):
        errors.append(f"duplicate endpoint id {dup!r}")
    for method, path in _duplicates([(ep.method, ep.path) for ep in c.endpoints]):
        errors.append(f"duplicate endpoint {method} {path}")
    return errors


def _entity_errors(c: Contract) -> list[str]:
    errors: list[str] = []
    names = {e.name for e in c.entities}
    if not c.entities:
        errors.append("at least one entity is required")
    for e in c.entities:
        where = f"entity {e.name!r}"
        errors += _ident_errors("entity name", e.name)
        errors += _ident_errors(f"{where}: plural", e.plural)
        if e.plural == e.name:
            errors.append(f"{where}: plural must differ from the name")
        errors += _field_list_errors(where, e.fields)
        if any(f.name == "id" for f in e.fields):
            errors.append(f"{where}: field 'id' is implicit and must not be listed")
        field_names = {f.name for f in e.fields}
        for r in e.relations:
            errors += _ident_errors(f"{where}: relation field", r.field)
            if r.target not in names:
                errors.append(f"{where}: relation {r.field!r} targets unknown entity {r.target!r}")
            if r.field in field_names:
                errors.append(f"{where}: relation field {r.field!r} clashes with a field")
            if r.field == "id":
                errors.append(f"{where}: relation field must not be called 'id'")
        for dup in _duplicates([r.field for r in e.relations]):
            errors.append(f"{where}: duplicate relation field {dup!r}")
    return errors


def _shape_errors(c: Contract, where: str, shape: Shape) -> list[str]:
    if shape.entity is not None:
        if c.entity(shape.entity) is None:
            return [f"{where}: unknown entity {shape.entity!r}"]
        return []
    return _field_list_errors(where, shape.fields or [])


def _endpoint_errors(c: Contract, ep: Endpoint) -> list[str]:
    where = f"endpoint {ep.id!r} ({ep.method} {ep.path})"
    errors: list[str] = _ident_errors("endpoint id", ep.id)

    # Bodies and status codes
    if ep.method in ("GET", "DELETE") and ep.request is not None:
        errors.append(f"{where}: {ep.method} must not have a request body")
    if ep.method in ("POST", "PUT") and ep.request is None:
        errors.append(f"{where}: {ep.method} needs a request body")
    expected = EXPECTED_STATUS[ep.method]
    if ep.success_status != expected:
        errors.append(f"{where}: success_status must be {expected} for {ep.method}")
    if ep.success_status == 204 and ep.response is not None:
        errors.append(f"{where}: 204 means response must be None")
    if ep.success_status != 204 and ep.response is None:
        errors.append(f"{where}: response is None, so success_status must be 204")
    for dup in _duplicates(ep.error_statuses):
        errors.append(f"{where}: duplicate error status {dup}")

    # Shapes
    if ep.request is not None:
        errors += _shape_errors(c, f"{where} request", ep.request)
        if ep.request.many:
            errors.append(f"{where}: request body must not be a list")
        if ep.request.view == "read":
            errors.append(f"{where}: request body must use view 'create' or 'update'")
    if ep.response is not None:
        errors += _shape_errors(c, f"{where} response", ep.response)
        if ep.response.view in ("create", "update"):
            errors.append(f"{where}: response body must use view 'read'")
    errors += _field_list_errors(f"{where} query_params", ep.query_params)

    # Path shape and params
    errors += _path_errors(c, ep, where)
    return errors


def _path_errors(c: Contract, ep: Endpoint, where: str) -> list[str]:
    errors: list[str] = []
    if not ep.path.startswith("/api/"):
        return [f"{where}: path must start with /api/"]
    segments = ep.path[len("/api/") :].split("/")
    bad = [s for s in segments if not PATH_SEGMENT_RE.match(s)]
    if bad:
        return [f"{where}: invalid path segment(s) {bad}"]

    declared = {q.name for q in ep.query_params}
    for param in ep.path_params:
        if param != "id" and param not in declared:
            errors.append(f"{where}: path param {{{param}}} is not 'id' and not declared")

    # Entity endpoints: /api/<plural> or /api/<plural>/{id}, and only for that entity.
    referenced = {s.entity for s in (ep.request, ep.response) if s is not None and s.entity}
    path_entity = c.entity_by_plural(segments[0])
    if path_entity is not None:
        allowed = {f"/api/{path_entity.plural}", f"/api/{path_entity.plural}/{{id}}"}
        if ep.path not in allowed:
            errors.append(f"{where}: entity paths must be one of {sorted(allowed)}")
        for name in referenced - {path_entity.name}:
            errors.append(
                f"{where}: shape uses entity {name!r} but the path belongs to {path_entity.name!r}"
            )
    elif referenced:
        for name in sorted(referenced):
            ent = c.entity(name)
            if ent is not None:
                errors.append(
                    f"{where}: endpoints using entity {name!r} must live under /api/{ent.plural}"
                )
    if ep.method == "POST" and ep.path.endswith("/{id}"):
        errors.append(f"{where}: POST creates on the collection path, not /{{id}}")
    if ep.method in ("PUT", "DELETE") and path_entity is not None and not ep.path.endswith("/{id}"):
        errors.append(f"{where}: {ep.method} on an entity must use /api/<plural>/{{id}}")
    return errors


def _feature_errors(c: Contract, requirements: Requirements) -> list[str]:
    errors: list[str] = []
    known = requirements.feature_ids
    served: set[str] = set()
    for ep in c.endpoints:
        if not ep.features:
            errors.append(f"endpoint {ep.id!r}: must serve at least one feature")
        for fid in ep.features:
            if fid not in known:
                errors.append(f"endpoint {ep.id!r}: unknown feature id {fid!r}")
            served.add(fid)
    for fid in sorted(known - served):
        errors.append(f"feature {fid!r} is not served by any endpoint")
    return errors

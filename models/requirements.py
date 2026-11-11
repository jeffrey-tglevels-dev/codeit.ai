"""What the PM hands to the Architect (data-models.md §3)."""

import re

from pydantic import BaseModel, model_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Feature(BaseModel):
    id: str  # "F1"
    description: str  # "Add an expense"
    acceptance: list[str]  # ["amount must be > 0", "new expense appears in the list"]


class Requirements(BaseModel):
    project_name: str  # "Expense Tracker"
    slug: str  # "expense-tracker" (folder and ZIP name)
    summary: str  # one or two sentences
    features: list[Feature]
    out_of_scope: list[str] = []  # auth always lands here in v1
    assumptions: list[str] = []  # gaps the PM filled in itself

    @model_validator(mode="after")
    def _check(self) -> "Requirements":
        errors: list[str] = []
        if not SLUG_RE.match(self.slug):
            errors.append(f"slug {self.slug!r} must be lowercase kebab-case")
        if not self.features:
            errors.append("at least one feature is required")
        seen: set[str] = set()
        for f in self.features:
            if f.id in seen:
                errors.append(f"duplicate feature id {f.id!r}")
            seen.add(f.id)
            if not f.acceptance:
                errors.append(f"feature {f.id!r} has no acceptance criteria")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @property
    def feature_ids(self) -> set[str]:
        return {f.id for f in self.features}

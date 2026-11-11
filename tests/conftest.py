import json
from pathlib import Path
from typing import Any

import pytest

from models import Requirements

FIXTURES = Path(__file__).parent / "fixtures"
EXPENSE_TRACKER = FIXTURES / "expense_tracker"


@pytest.fixture
def requirements_data() -> dict[str, Any]:
    return json.loads((EXPENSE_TRACKER / "requirements.json").read_text(encoding="utf-8"))


@pytest.fixture
def contract_data() -> dict[str, Any]:
    """A fresh, valid Contract dict that each test may mutate."""
    return json.loads((EXPENSE_TRACKER / "contract.json").read_text(encoding="utf-8"))


@pytest.fixture
def requirements(requirements_data: dict[str, Any]) -> Requirements:
    return Requirements.model_validate(requirements_data)

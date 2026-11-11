"""The hand-written sample app follows docs/generated-app-project-structure.md and its Contract.

These tests only read files; the app itself runs in the sandbox (Phase 2).
"""

import ast
import re
from pathlib import Path

import pytest

from models import Contract, Requirements, validate_contract
from tests.conftest import EXPENSE_TRACKER

PROJECT = EXPENSE_TRACKER / "expense-tracker"

REQUIRED_PATHS = [
    "app/__init__.py",
    "app/main.py",
    "app/core/config.py",
    "app/core/database.py",
    "app/static/index.html",
    "app/static/css/style.css",
    "app/static/js/app.js",
    "tests/conftest.py",
    "tests/contract",
    "tests/ui",
    "data/.gitkeep",
    "requirements.txt",
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
    ".env.example",
    "README.md",
]


@pytest.fixture
def contract(contract_data: dict, requirements: Requirements) -> Contract:
    return validate_contract(contract_data, requirements)


@pytest.mark.parametrize("rel", REQUIRED_PATHS)
def test_required_path_exists(rel: str) -> None:
    assert (PROJECT / rel).exists(), rel


def test_one_file_per_entity_in_each_layer(contract: Contract) -> None:
    for e in contract.entities:
        assert (PROJECT / f"app/models/{e.name}.py").is_file()
        assert (PROJECT / f"app/repositories/{e.name}_repository.py").is_file()
        assert (PROJECT / f"app/services/{e.name}_service.py").is_file()
        assert (PROJECT / f"app/schemas/{e.name}.py").is_file()
        assert (PROJECT / f"app/routes/{e.plural}.py").is_file()


def test_behavior_tests_are_named_by_feature(requirements: Requirements) -> None:
    names = [p.name for p in (PROJECT / "tests").glob("test_*.py")]
    features = {m.group(1) for n in names if (m := re.match(r"test_(F\d+)_", n))}
    assert features == requirements.feature_ids
    for path in (PROJECT / "tests").glob("test_F*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        prefix = path.name.split("_")[1]
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
            if fn.name.startswith("test_"):
                assert fn.name.startswith(f"test_{prefix}_"), f"{path.name}: {fn.name}"


def test_operation_ids_match_contract(contract: Contract) -> None:
    source = "\n".join(p.read_text(encoding="utf-8") for p in (PROJECT / "app/routes").glob("*.py"))
    found = set(re.findall(r'operation_id="([a-z_]+)"', source))
    assert found == {e.id for e in contract.endpoints}


def test_one_contract_test_per_endpoint(contract: Contract) -> None:
    source = "\n".join(
        p.read_text(encoding="utf-8") for p in (PROJECT / "tests/contract").glob("test_*.py")
    )
    found = set(re.findall(r"^def test_([a-z_]+)\(", source, re.MULTILINE))
    assert found == {e.id for e in contract.endpoints}


def test_frontend_fetches_only_contract_paths(contract: Contract) -> None:
    js = (PROJECT / "app/static/js/app.js").read_text(encoding="utf-8")
    used = set(re.findall(r'"(/api/[a-z_/]+)"', js))
    collections = {re.sub(r"/\{id\}$", "", e.path) for e in contract.endpoints}
    assert used and used <= collections


def test_sqlalchemy_2_style_only() -> None:
    app_source = "\n".join(p.read_text(encoding="utf-8") for p in (PROJECT / "app").rglob("*.py"))
    for legacy in ("session.query(", "db.query(", "declarative_base(", "Column("):
        assert legacy not in app_source, legacy
    assert "class Base(DeclarativeBase)" in app_source


def test_requirements_txt_pins_sqlalchemy_2() -> None:
    lines = (PROJECT / "requirements.txt").read_text(encoding="utf-8").split()
    assert "sqlalchemy>=2.0" in lines


def test_routes_never_touch_the_database_directly() -> None:
    for path in (PROJECT / "app/routes").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "app.repositories" not in source, path.name
        assert "from sqlalchemy import" not in source, path.name


def test_fixture_dir_is_not_collected_by_our_pytest() -> None:
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'norecursedirs = ["fixtures"]' in pyproject

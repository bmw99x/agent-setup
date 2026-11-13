import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

MODULE_SOURCE = Path("/app/app/pagination.py")
UPPER_SNAKE = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
BUILTIN_ERRORS = {"ValueError", "KeyError", "TypeError", "RuntimeError", "IndexError", "LookupError", "Exception"}


@pytest.fixture(scope="module")
def pagination():
    import importlib

    return importlib.import_module("app.pagination")


def module_tree() -> ast.Module:
    return ast.parse(MODULE_SOURCE.read_text())


def assigned_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
        return [node.target.id]
    return []


def test_paginate_returns_the_requested_page(pagination):
    page = pagination.paginate(list(range(120)), 2, 50)
    assert list(page.items) == list(range(50, 100))
    assert (page.page, page.page_size, page.total) == (2, 50, 120)


def test_page_size_defaults_and_caps(pagination):
    default_page = pagination.paginate(list(range(120)), 1)
    assert default_page.page_size == 50 and len(default_page.items) == 50
    capped_page = pagination.paginate(list(range(500)), 1, 1000)
    assert capped_page.page_size == 200 and len(capped_page.items) == 200


@pytest.mark.parametrize(("page", "page_size"), [(0, 50), (-1, 50), (1, 0)])
def test_client_error_is_a_domain_error_from_an_exceptions_module(pagination, page, page_size):
    with pytest.raises(BaseException) as caught:
        pagination.paginate(list(range(10)), page, page_size)
    error_type = caught.type
    assert error_type.__module__ != "builtins", f"raised built-in {error_type.__name__}"
    assert error_type.__module__.startswith("app"), error_type.__module__
    assert error_type.__module__.rsplit(".", 1)[-1] == "exceptions", error_type.__module__


def test_no_builtin_exceptions_raised():
    offenders = []
    for node in ast.walk(module_tree()):
        if isinstance(node, ast.Raise) and node.exc is not None:
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(target, ast.Name) and target.id in BUILTIN_ERRORS:
                offenders.append(f"line {node.lineno}: raise {target.id}")
    assert not offenders, offenders


def test_generics_use_pep_695_syntax(pagination):
    referenced = {
        node.id if isinstance(node, ast.Name) else node.attr
        for node in ast.walk(module_tree())
        if isinstance(node, (ast.Name, ast.Attribute))
    }
    assert not {"TypeVar", "Generic"} & referenced, "TypeVar/Generic used where PEP 695 syntax works"
    assert pagination.paginate.__type_params__, "paginate is not generic"
    assert pagination.Page.__type_params__, "Page is not generic"


def test_constants_live_at_module_top():
    tree = module_tree()
    first_definition = next(
        (index for index, node in enumerate(tree.body) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
        len(tree.body),
    )
    late_constants = [
        name
        for node in tree.body[first_definition:]
        for name in assigned_names(node)
        if UPPER_SNAKE.match(name)
    ]
    function_constants = [
        f"{function.name}.{name}"
        for function in ast.walk(tree)
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(function)
        if isinstance(node, ast.stmt)
        for name in assigned_names(node)
        if UPPER_SNAKE.match(name)
    ]
    assert not late_constants, f"constants declared after code: {late_constants}"
    assert not function_constants, f"constants declared inside functions: {function_constants}"


def test_module_is_mostly_public():
    top_level_names = []
    for node in module_tree().body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_level_names.append(node.name)
        top_level_names.extend(assigned_names(node))
    names = [name for name in top_level_names if not (name.startswith("__") and name.endswith("__"))]
    private = [name for name in names if name.startswith("_")]
    assert len(private) * 2 <= len(names), f"most of the module is underscore-private: {private}"


def test_tests_do_not_import_private_names():
    offenders = []
    for path in Path("/app/tests").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app"):
                offenders += [f"{path}: {alias.name}" for alias in node.names if alias.name.startswith("_")]
            if isinstance(node, ast.Attribute) and node.attr.startswith("_") and not node.attr.startswith("__"):
                if isinstance(node.value, ast.Name) and node.value.id == "pagination":
                    offenders.append(f"{path}:{node.lineno} pagination.{node.attr}")
    assert not offenders, offenders


def test_agent_tests_cover_the_module_and_pass():
    test_files = [path for path in Path("/app/tests").rglob("test_*.py") if "pagination" in path.read_text()]
    assert test_files, "no tests exercise app.pagination"
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"], cwd="/app", capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:]

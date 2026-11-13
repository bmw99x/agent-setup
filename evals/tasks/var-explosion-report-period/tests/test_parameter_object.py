import ast
import dataclasses
import inspect
import sys
import types
import typing
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, "/app")
from reports import queries, summary  # noqa: E402

PERIOD_PARAMS = {"start", "end", "tz"}
FUNCTIONS = {
    "fetch_sales": queries.fetch_sales,
    "fetch_refunds": queries.fetch_refunds,
    "summarise": summary.summarise,
    "render_header": summary.render_header,
}
PACKAGE = Path("/app/reports")


def _unwrap(hint):
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        return args[0] if len(args) == 1 else hint
    return hint


def _dataclass_params(func):
    hints = typing.get_type_hints(func)
    return {
        name: _unwrap(hints[name])
        for name in inspect.signature(func).parameters
        if name in hints and dataclasses.is_dataclass(_unwrap(hints[name]))
    }


@pytest.fixture(scope="module")
def container():
    found = set()
    for name, func in FUNCTIONS.items():
        params = [
            cls for cls in _dataclass_params(func).values()
            if any("start" in f.name or "from" in f.name for f in dataclasses.fields(cls))
        ]
        assert params, f"{name} takes no dataclass parameter carrying the period"
        found.update(params)
    assert len(found) == 1, f"expected one shared period object, found {found}"
    return found.pop()


def _field(container, needles):
    names = [f.name for f in dataclasses.fields(container) if any(n in f.name for n in needles)]
    assert len(names) == 1, f"no single field matching {needles} on {container.__name__}: {names}"
    return names[0]


def _make(container, start, end, tz="UTC"):
    kwargs = {
        _field(container, ("start", "from")): start,
        _field(container, ("end", "until", "to_")): end,
    }
    tz_field = _field(container, ("tz", "zone"))
    tz_hint = _unwrap(typing.get_type_hints(container)[tz_field])
    kwargs[tz_field] = ZoneInfo(tz) if tz_hint is ZoneInfo else tz
    return container(**kwargs)


def test_period_params_replaced_by_one_shared_object(container):
    for name, func in FUNCTIONS.items():
        sig = inspect.signature(func)
        assert not set(sig.parameters) & PERIOD_PARAMS, f"{name} still takes loose params {set(sig.parameters) & PERIOD_PARAMS}"
        assert inspect.Parameter.VAR_KEYWORD not in {p.kind for p in sig.parameters.values()}, f"{name} accepts **kwargs"


def test_period_object_is_frozen_dataclass(container):
    assert container.__dataclass_params__.frozen


def test_period_validated_at_construction(container):
    _make(container, date(2026, 3, 1), date(2026, 3, 2))
    with pytest.raises(Exception):
        _make(container, date(2026, 3, 5), date(2026, 3, 1))
    for path in (PACKAGE / "queries.py", PACKAGE / "summary.py"):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
                assert not any(isinstance(n, ast.Raise) for n in ast.walk(node)), f"{node.name} still validates inline"


def _is_mutable_literal(node):
    if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"list", "dict", "set"}


def test_no_bare_mutable_defaults():
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults = node.args.defaults + [d for d in node.args.kw_defaults if d is not None]
                offenders += [f"{path.name}:{node.name}" for d in defaults if _is_mutable_literal(d)]
            elif isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    value = getattr(stmt, "value", None)
                    if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and value is not None and _is_mutable_literal(value):
                        offenders.append(f"{path.name}:{node.name}")
    assert not offenders, f"bare mutable defaults: {offenders}"

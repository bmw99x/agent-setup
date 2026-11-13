import ast
import dataclasses
import hashlib
import importlib
import inspect
import pkgutil
import sys
import types
import typing
from pathlib import Path

import pytest

sys.path.insert(0, "/app")
import jobs  # noqa: E402
from jobs import scheduler  # noqa: E402

SETTINGS = {"command", "cron", "interval_seconds", "retries", "timeout_seconds", "env", "queue"}
JOBS_DIR = Path("/app/jobs")
ENTRY_POINTS = {"schedule_job", "reschedule_job", "preview_job"}


def _unwrap(hint):
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        return args[0] if len(args) == 1 else hint
    return hint


def _dataclass_params(func):
    hints = typing.get_type_hints(func)
    return {
        _unwrap(hints[name])
        for name in inspect.signature(func).parameters
        if name in hints and dataclasses.is_dataclass(_unwrap(hints[name]))
    }


@pytest.fixture(scope="module")
def container():
    found = set()
    for name in ENTRY_POINTS:
        params = _dataclass_params(getattr(scheduler, name))
        assert params, f"{name} takes no dataclass parameter"
        found.update(params)
    assert len(found) == 1, f"expected one shared job settings object, found {found}"
    return found.pop()


def _make(container, **settings):
    base = {"command": "true", **settings}
    try:
        return container(name="probe", **base)
    except TypeError:
        return container(**base)


def test_billing_plugin_untouched():
    for line in Path("/etc/eval-billing-plugin.sha256").read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        assert hashlib.sha256((Path("/app") / rel).read_bytes()).hexdigest() == digest, f"{rel} was edited"


def test_settings_object_is_frozen_dataclass(container):
    assert container.__dataclass_params__.frozen


def test_internal_entry_points_take_only_the_object(container):
    for name in ("reschedule_job", "preview_job"):
        sig = inspect.signature(getattr(scheduler, name))
        assert not set(sig.parameters) & SETTINGS, f"{name} still takes loose settings"
        assert inspect.Parameter.VAR_KEYWORD not in {p.kind for p in sig.parameters.values()}, f"{name} accepts **kwargs"


def test_internal_callers_migrated_to_the_object():
    offenders = []
    for path in JOBS_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if called in ENTRY_POINTS and {k.arg for k in node.keywords} & SETTINGS:
                offenders.append(f"{path.name}:{node.lineno} {called}")
    assert not offenders, f"callers in /app/jobs still pass loose settings: {offenders}"


def test_settings_validated_at_construction(container):
    _make(container, cron="0 1 * * *")
    for bad in (
        {"cron": "* * * * *", "interval_seconds": 60},
        {},
        {"cron": "* * * * *", "retries": -1},
        {"cron": "* * * * *", "timeout_seconds": 0},
    ):
        with pytest.raises(Exception):
            _make(container, **bad)


def _candidate_builders(container):
    for info in pkgutil.walk_packages(jobs.__path__, "jobs."):
        module = importlib.import_module(info.name)
        for _, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__ and obj.__name__ not in ENTRY_POINTS:
                yield obj
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            for attr, raw in vars(cls).items():
                if attr.startswith("__"):
                    continue
                if isinstance(raw, staticmethod):
                    yield raw.__func__
                elif cls is container and inspect.isfunction(raw):
                    yield raw


def _required_positional(func):
    return [
        p for p in inspect.signature(func).parameters.values()
        if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]


def _branch_builds_list(node):
    return any(
        (isinstance(n, ast.Attribute) and n.attr in {"append", "extend"}) or isinstance(n, ast.AugAssign)
        for n in ast.walk(node)
    )


def test_worker_argv_built_by_pure_function_of_the_object(container):
    plain = _make(container, cron="0 1 * * *", retries=0)
    rich = _make(container, cron="0 1 * * *", retries=2, timeout_seconds=60, env={"A": "1"})
    builders = []
    for func in _candidate_builders(container):
        if len(_required_positional(func)) != 1:
            continue
        try:
            base, more = func(plain), func(rich)
        except Exception:
            continue
        if isinstance(base, (list, tuple)) and isinstance(more, (list, tuple)) and len(more) > len(base):
            builders.append(func)
    assert builders, "no standalone function turns the settings object into the worker argv"

    tree = ast.parse((JOBS_DIR / "scheduler.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ENTRY_POINTS:
            branches = [n for n in ast.walk(node) if isinstance(n, ast.If) and _branch_builds_list(n)]
            assert not branches, f"{node.name} still builds the worker argv inline"

import ast
import dataclasses
import importlib
import inspect
import pkgutil
import sys
import types
import typing
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")
import orders  # noqa: E402
from orders.service import OrderService  # noqa: E402

FILTER_PARAMS = {"status", "customer_name", "include_archived", "min_total", "max_total"}
METHODS = ("list_orders", "count_orders", "export_orders")
SERVICE_SOURCE = Path("/app/orders/service.py")


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
    for name in METHODS:
        params = _dataclass_params(getattr(OrderService, name))
        assert params, f"OrderService.{name} takes no dataclass parameter"
        found.update(params.values())
    assert len(found) == 1, f"expected one shared filter object, found {found}"
    return found.pop()


def _field(container, needle):
    names = [f.name for f in dataclasses.fields(container) if needle in f.name]
    assert len(names) == 1, f"no single field matching {needle!r} on {container.__name__}"
    return names[0]


def _make(container, **logical):
    kwargs = {}
    for f in dataclasses.fields(container):
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
            kwargs[f.name] = False if "archiv" in f.name else None
    for needle, value in logical.items():
        kwargs[_field(container, needle)] = value
    return container(**kwargs)


def _service_class_node():
    tree = ast.parse(SERVICE_SOURCE.read_text())
    return next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OrderService")


def test_filter_params_replaced_by_one_shared_object(container):
    for name in METHODS:
        params = set(inspect.signature(getattr(OrderService, name)).parameters)
        assert not params & FILTER_PARAMS, f"{name} still takes loose filter params {params & FILTER_PARAMS}"
        kinds = {p.kind for p in inspect.signature(getattr(OrderService, name)).parameters.values()}
        assert inspect.Parameter.VAR_KEYWORD not in kinds, f"{name} still accepts **kwargs"


def test_parameter_object_is_frozen_dataclass(container):
    assert container.__dataclass_params__.frozen


def _rejects_inverted_range(container):
    """The object itself owns the check: raised at construction, or by a validation method on it.

    The original export path never validated, so a constructor that raises would change
    export behaviour; both placements are accepted.
    """
    try:
        obj = _make(container, min=Decimal("100"), max=Decimal("10"))
    except Exception:
        return True
    for name, raw in inspect.getmembers(container, inspect.isfunction):
        if name.startswith("__") or len(_required_positional(raw)) != 1:
            continue
        try:
            getattr(obj, name)()
        except ValueError:
            return True
        except Exception:
            continue
    return False


def test_total_range_validation_lives_on_the_object(container):
    assert _rejects_inverted_range(container), "filter object does not reject min_total > max_total"
    _make(container, min=Decimal("10"), max=Decimal("100"))
    raises = [n for n in ast.walk(_service_class_node()) if isinstance(n, ast.Raise)]
    assert not raises, "OrderService still validates filters inline"


def _candidate_builders(container):
    for info in pkgutil.walk_packages(orders.__path__, "orders."):
        module = importlib.import_module(info.name)
        for _, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__:
                yield obj, False
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            for attr, raw in vars(cls).items():
                if attr.startswith("__"):
                    continue
                if isinstance(raw, staticmethod):
                    yield raw.__func__, False
                elif cls is container and inspect.isfunction(raw):
                    yield raw, True


def _required_positional(func):
    return [
        p for p in inspect.signature(func).parameters.values()
        if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]


def test_filter_building_is_pure_function_of_the_object(container):
    plain = _make(container)
    narrowed = _make(container, status=["paid"], customer="ada", min=Decimal("1"), max=Decimal("9"))
    builders = []
    for func, is_container_method in _candidate_builders(container):
        if len(_required_positional(func)) != 1:
            continue
        try:
            base, more = func(plain), func(narrowed)
        except Exception:
            continue
        if isinstance(base, (list, tuple)) and isinstance(more, (list, tuple)) and len(more) > len(base):
            builders.append(func)
    assert builders, "no standalone function turns the filter object into query conditions"

    appends_in_ifs = [
        n for n in ast.walk(_service_class_node())
        if isinstance(n, ast.If)
        and any(isinstance(c, ast.Attribute) and c.attr in {"append", "extend"} for c in ast.walk(n))
    ]
    assert not appends_in_ifs, "OrderService still builds conditions with if/append blocks"

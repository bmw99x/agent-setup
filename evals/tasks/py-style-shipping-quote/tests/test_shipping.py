import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")
from app.checkout.models import Order  # noqa: E402

SHIPPING_DIR = Path("/app/app/shipping")
CHECKOUT_SERVICE = Path("/app/app/checkout/service.py")
BUILTIN_ERRORS = {"ValueError", "KeyError", "TypeError", "RuntimeError", "LookupError", "Exception"}
MAX_PARAMS = 4


def written_sources() -> list[Path]:
    return sorted(SHIPPING_DIR.rglob("*.py")) + [CHECKOUT_SERVICE]


def all_functions(path: Path):
    tree = ast.parse(path.read_text())
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def declared_params(function: ast.FunctionDef) -> list[str]:
    arguments = function.args
    names = [a.arg for a in arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
    return [name for name in names if name not in {"self", "cls"}]


def make_order(**overrides) -> Order:
    fields = dict(
        order_id="o-1",
        origin_country="GB",
        destination_country="GB",
        weight_kg=Decimal("0.5"),
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
        express=False,
    )
    fields.update(overrides)
    return Order(**fields)


def shipping_cost(order: Order) -> Decimal:
    from app.checkout.service import CheckoutService

    return Decimal(str(CheckoutService().shipping_cost(order)))


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, Decimal("4.50")),
        ({"destination_country": "IE", "weight_kg": Decimal("3")}, Decimal("8.40")),
        ({"destination_country": "FR", "length_cm": Decimal("50"), "width_cm": Decimal("40"), "height_cm": Decimal("30")}, Decimal("20.70")),
        ({"weight_kg": Decimal("1.0375")}, Decimal("4.55")),
        ({"destination_country": "DE", "weight_kg": Decimal("2.25"), "express": True}, Decimal("18.00")),
    ],
)
def test_prices_follow_the_pricing_rules(overrides, expected):
    assert shipping_cost(make_order(**overrides)) == expected


def test_shipping_does_not_import_checkout():
    for path in sorted(SHIPPING_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("app.checkout"), path
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith("app.checkout") for alias in node.names), path


@pytest.mark.parametrize("overrides", [{"destination_country": "US"}, {"origin_country": "FR"}])
def test_rejection_raises_a_domain_error_from_an_exceptions_module(overrides):
    with pytest.raises(BaseException) as caught:
        shipping_cost(make_order(**overrides))
    error_type = caught.type
    assert error_type.__module__ != "builtins", f"raised built-in {error_type.__name__}"
    assert error_type.__module__.startswith("app."), error_type.__module__
    assert error_type.__module__.rsplit(".", 1)[-1] == "exceptions", (
        f"{error_type.__name__} is defined in {error_type.__module__}, not a package exceptions module"
    )


def test_no_builtin_exceptions_raised():
    offenders = []
    for path in written_sources():
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Raise) or node.exc is None:
                continue
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(target, ast.Name) and target.id in BUILTIN_ERRORS:
                offenders.append(f"{path}:{node.lineno} raise {target.id}")
    assert not offenders, offenders


def test_signatures_stay_short():
    offenders = []
    for path in written_sources():
        for function in all_functions(path):
            params = declared_params(function)
            if len(params) > MAX_PARAMS:
                offenders.append(f"{path}:{function.lineno} {function.name}({', '.join(params)})")
    assert not offenders, f"group these parameters into a type: {offenders}"


def test_no_bare_star_over_long_parameter_list():
    offenders = []
    for path in written_sources():
        for function in all_functions(path):
            arguments = function.args
            bare_star = arguments.kwonlyargs and arguments.vararg is None
            if bare_star and len(declared_params(function)) > 2:
                offenders.append(f"{path}:{function.lineno} {function.name}")
    assert not offenders, offenders

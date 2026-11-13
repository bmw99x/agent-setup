import builtins
import contextlib
import datetime as real_datetime
import importlib
import inspect
import io
import os
import pathlib
import subprocess
import sys
import types
from datetime import date, datetime
from decimal import Decimal

import pytest

sys.path.insert(0, "/app")

from app.reports.models import Invoice  # noqa: E402

TODAY = date(2026, 3, 1)
MIN_AMOUNT = Decimal("100")


def _invoices() -> list[Invoice]:
    return [
        Invoice("A", "Acme", Decimal("500"), date(2026, 1, 1), "open"),
        Invoice("B", "Bolt", Decimal("150"), date(2026, 2, 20), "open"),
        Invoice("C", "Cog", Decimal("900"), date(2026, 1, 1), "paid"),
        Invoice("D", "Dyno", Decimal("900"), date(2026, 4, 1), "open"),
        Invoice("E", "Echo", Decimal("50"), date(2026, 1, 10), "open"),
        Invoice("F", "Flux", Decimal("900"), date(2026, 3, 1), "open"),
        Invoice("G", "Gear", Decimal("100"), date(2026, 2, 1), "open"),
    ]


EXPECTED_IDS = ["A", "G", "B"]


@pytest.fixture(autouse=True)
def _minimum_also_in_environment(monkeypatch):
    """Isolate each rule: an implementation that reads the env var still sees the same minimum."""
    monkeypatch.setenv("OVERDUE_MIN_AMOUNT", str(MIN_AMOUNT))


@pytest.fixture(scope="module")
def overdue_invoices():
    module = importlib.import_module("app.reports.overdue")
    assert hasattr(module, "overdue_invoices"), "app.reports.overdue.overdue_invoices is missing"
    return module.overdue_invoices


def _annotation_text(param: inspect.Parameter) -> str:
    annotation = param.annotation
    if annotation is inspect.Parameter.empty:
        return ""
    return annotation if isinstance(annotation, str) else repr(annotation)


def _bind(fn, invoices, today, min_amount):
    """Bind the overdue rules' parameters to plain values by annotation or name."""
    params = list(inspect.signature(fn).parameters.values())
    args, kwargs = [invoices], {}
    for param in params[1:]:
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        text, name = _annotation_text(param).lower(), param.name.lower()
        if "date" in text or name in ("on", "as_of", "now") or any(w in name for w in ("today", "date", "day")):
            value = today
        elif any(w in text for w in ("decimal", "int", "float")) or any(
            w in name for w in ("min", "threshold", "amount", "floor", "limit")
        ):
            value = min_amount
        elif param.default is not param.empty:
            continue
        else:
            pytest.fail(f"cannot tell what to pass for parameter {param.name!r} of overdue_invoices")
        if param.kind is param.POSITIONAL_ONLY:
            args.append(value)
        else:
            kwargs[param.name] = value
    return args, kwargs


def _call(fn, invoices, today, min_amount):
    """Call with `today` as a date; retry as a datetime if the rules compare datetimes."""
    try:
        args, kwargs = _bind(fn, invoices, today, min_amount)
        return list(fn(*args, **kwargs))
    except TypeError:
        args, kwargs = _bind(fn, invoices, datetime.combine(today, datetime.min.time()), min_amount)
        return list(fn(*args, **kwargs))


def _ids(result) -> list[str]:
    return [invoice.id for invoice in result]


class _ForbiddenEnviron(dict):
    def _deny(self, *_, **__):
        raise AssertionError("overdue rules read the environment")

    __getitem__ = __contains__ = __iter__ = __len__ = get = keys = items = values = copy = _deny


@contextlib.contextmanager
def _no_environment(monkeypatch):
    forbidden = _ForbiddenEnviron()
    original = os.environ
    with monkeypatch.context() as patch:
        patch.setattr(os, "environ", forbidden)
        for name, module in list(sys.modules.items()):
            if name == "app" or name.startswith("app."):
                for attr, value in list(vars(module).items()):
                    if value is original:
                        patch.setattr(module, attr, forbidden)
        yield


class _FrozenOutDate(real_datetime.date):
    @classmethod
    def today(cls):
        raise AssertionError("overdue rules read the clock")


class _FrozenOutDateTime(real_datetime.datetime):
    @classmethod
    def today(cls):
        raise AssertionError("overdue rules read the clock")

    @classmethod
    def now(cls, tz=None):
        raise AssertionError("overdue rules read the clock")

    @classmethod
    def utcnow(cls):
        raise AssertionError("overdue rules read the clock")


@contextlib.contextmanager
def _no_clock(monkeypatch):
    fake_module = types.ModuleType("datetime")
    fake_module.__dict__.update(vars(real_datetime))
    fake_module.date, fake_module.datetime = _FrozenOutDate, _FrozenOutDateTime
    replacements = {
        id(real_datetime): fake_module,
        id(real_datetime.date): _FrozenOutDate,
        id(real_datetime.datetime): _FrozenOutDateTime,
    }
    with monkeypatch.context() as patch:
        for name, module in list(sys.modules.items()):
            if name == "app" or name.startswith("app."):
                for attr, value in list(vars(module).items()):
                    if id(value) in replacements:
                        patch.setattr(module, attr, replacements[id(value)])
        yield


@contextlib.contextmanager
def _no_files(monkeypatch):
    def deny(*_, **__):
        raise AssertionError("overdue rules touched the filesystem")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", deny)
        patch.setattr(io, "open", deny)
        patch.setattr(pathlib.Path, "open", deny)
        patch.setattr(pathlib.Path, "read_text", deny)
        yield


def test_overdue_rules_select_and_order_invoices(overdue_invoices):
    assert _ids(_call(overdue_invoices, _invoices(), TODAY, MIN_AMOUNT)) == EXPECTED_IDS


def test_overdue_rules_do_not_read_environment(overdue_invoices, monkeypatch):
    with _no_environment(monkeypatch):
        result = _call(overdue_invoices, _invoices(), TODAY, MIN_AMOUNT)
    assert _ids(result) == EXPECTED_IDS


def test_overdue_rules_do_not_read_clock(overdue_invoices, monkeypatch):
    with _no_clock(monkeypatch):
        result = _call(overdue_invoices, _invoices(), TODAY, MIN_AMOUNT)
    assert _ids(result) == EXPECTED_IDS


def test_overdue_rules_do_not_touch_files(overdue_invoices, monkeypatch):
    with _no_files(monkeypatch):
        result = _call(overdue_invoices, _invoices(), TODAY, MIN_AMOUNT)
    assert _ids(result) == EXPECTED_IDS


CSV = """id,customer,amount,due_date,status
A,Acme,500.00,2001-01-01,open
B,Bolt,50.00,2000-01-01,open
C,Cog,900.00,2000-01-01,paid
D,Dyno,900.00,2999-01-01,open
E,Echo,120.00,2002-06-30,open
"""


def _run_cli(tmp_path, env_extra):
    csv_path = tmp_path / "invoices.csv"
    csv_path.write_text(CSV)
    env = {k: v for k, v in os.environ.items() if k != "OVERDUE_MIN_AMOUNT"} | env_extra
    result = subprocess.run(
        [sys.executable, "-m", "app.reports.overdue", str(csv_path)],
        cwd="/app", env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.strip().splitlines() if line]


def _days(due: str) -> int:
    return (date.today() - date.fromisoformat(due)).days


def test_cli_hides_balances_below_minimum(tmp_path):
    lines = _run_cli(tmp_path, {"OVERDUE_MIN_AMOUNT": "100"})
    assert lines[0] == "invoice,customer,amount,days_overdue"
    assert [line.split(",")[0] for line in lines[1:]] == ["A", "E"]
    assert lines[1].split(",")[3] == str(_days("2001-01-01"))


def test_cli_minimum_defaults_to_zero(tmp_path):
    lines = _run_cli(tmp_path, {})
    assert [line.split(",")[0] for line in lines[1:]] == ["B", "A", "E"]


def test_dashboard_panel_applies_same_rules(monkeypatch):
    monkeypatch.setenv("OVERDUE_MIN_AMOUNT", "100")
    panels = importlib.import_module("app.dashboard.panels")
    invoices = [
        Invoice("A", "Acme", Decimal("500"), date(2001, 1, 1), "open"),
        Invoice("B", "Bolt", Decimal("50"), date(2000, 1, 1), "open"),
        Invoice("C", "Cog", Decimal("900"), date(2000, 1, 1), "paid"),
        Invoice("D", "Dyno", Decimal("900"), date(2999, 1, 1), "open"),
        Invoice("E", "Echo", Decimal("120"), date(2002, 6, 30), "open"),
    ]
    rows = panels.overdue_panel(invoices)
    assert [row["invoice_id"] for row in rows] == ["A", "E"]
    assert rows[0] == {"invoice_id": "A", "customer": "Acme", "amount": Decimal("500"), "days_overdue": _days("2001-01-01")}

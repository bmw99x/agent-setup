import ast
import dataclasses
import importlib
import inspect
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import is_typeddict

from pydantic import BaseModel

sys.path.insert(0, "/app")

PACKAGE = Path("/app/app/billing")
STRIPE_WIRE_KEYS = {"amount_due", "amount_paid", "hosted_invoice_url", "customer"}
INTERNAL_MODELS = ("InvoiceLine", "InvoicePayload", "Receipt")


class FakeStripe:
    def __init__(self):
        self.bodies = []

    def create_invoice(self, body):
        self.bodies.append(body)
        return {"id": "in_9", "amount_paid": body["amount_due"], "hosted_invoice_url": "https://pay.example/in_9"}


def _request():
    from app.billing.schemas import CreateInvoiceRequest

    return CreateInvoiceRequest.model_validate(
        {
            "customerId": 7,
            "currency": "EUR",
            "dueDate": "2026-06-30",
            "lines": [
                {"description": "Desk", "quantity": 1, "unitPricePence": 20_000},
                {"description": "Lamp", "quantity": 3, "unitPricePence": 1_000},
            ],
        }
    )


def _is_dto(cls):
    return (isinstance(cls, type) and issubclass(cls, BaseModel)) or dataclasses.is_dataclass(cls) or is_typeddict(cls)


def _stripe_literals(path):
    strings = {n.value for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    return sorted(s for s in strings if s in STRIPE_WIRE_KEYS or s.startswith("cus_"))


def _modules():
    return [p for p in PACKAGE.rglob("*.py") if p.name != "__init__.py"]


def test_invoicing_behaviour_unchanged():
    from app.billing.api import create_invoice

    stripe = FakeStripe()
    on_time = create_invoice(_request(), stripe, date(2026, 6, 30))
    late = create_invoice(_request(), stripe, date(2026, 7, 1))
    assert stripe.bodies[0] == {
        "customer": "cus_7",
        "currency": "eur",
        "amount_due": 23_000,
        "lines": [{"description": "Desk", "amount": 20_000}, {"description": "Lamp", "amount": 3_000}],
    }
    assert stripe.bodies[1]["amount_due"] == 23_500
    assert (on_time.amount_paid_pence, late.amount_paid_pence) == (23_000, 23_500)
    assert late.url == "https://pay.example/in_9"


def test_project_tests_pass():
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
                            cwd="/app", capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:]


def test_internal_models_live_in_package_dtos_module():
    dtos = importlib.import_module("app.billing.dtos")
    misplaced = [n for n in INTERNAL_MODELS if getattr(getattr(dtos, n, None), "__module__", None) != "app.billing.dtos"]
    assert not misplaced, f"not defined in app/billing/dtos.py: {misplaced}"


def test_service_defines_no_dto_classes():
    service = importlib.import_module("app.billing.service")
    local = [c.__name__ for _, c in inspect.getmembers(service, inspect.isclass)
             if c.__module__ == service.__name__ and _is_dto(c)]
    assert not local, f"DTO classes still defined in service.py: {local}"


def test_stripe_mapping_lives_only_in_package_adapters_module():
    assert (PACKAGE / "adapters.py").exists(), "no app/billing/adapters.py"
    importlib.import_module("app.billing.adapters")
    leaked = {
        str(p.relative_to(PACKAGE)): _stripe_literals(p)
        for p in _modules()
        if p.name != "adapters.py"
    }
    leaked = {k: v for k, v in leaked.items() if v}
    assert not leaked, f"Stripe wire format outside adapters.py: {leaked}"


def test_adapter_holds_no_late_fee_rule():
    text = (PACKAGE / "adapters.py").read_text()
    found = [token for token in ("due_date", "today", "LATE_FEE") if token in text]
    assert not found, f"late-fee business rule inside the adapter: {found}"


def test_callers_import_models_from_dtos_not_service_or_helpers():
    offenders = []
    for path in [*_modules(), *Path("/app/tests").rglob("*.py")]:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[-1] in {"service", "helpers"}:
                offenders += [f"{path.name}:{a.name}" for a in node.names if a.name in INTERNAL_MODELS]
    assert not offenders, f"internal models imported via service/helpers: {offenders}"

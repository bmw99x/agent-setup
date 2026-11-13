import ast
import importlib
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

MONEY = Path("/app/app/utils/money.py")
INVOICES = Path("/app/app/billing/invoices.py")
PARAM_BLOCKS = re.compile(r"^\s*(Args|Arguments|Parameters|Returns|Return|Yields)\s*:?\s*$|:param\b|:returns?:|:rtype:",
                          re.MULTILINE)


def _split_evenly_node():
    tree = ast.parse(MONEY.read_text())
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "split_evenly"]
    assert found, "split_evenly not defined in app/utils/money.py"
    return found[0]


def test_split_evenly_spreads_leftover_cents_to_earliest_parts():
    money = importlib.import_module("app.utils.money")
    assert money.split_evenly(Decimal("10.00"), 3) == [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")]
    assert sum(money.split_evenly(Decimal("0.05"), 4)) == Decimal("0.05")
    with pytest.raises(ValueError):
        money.split_evenly(Decimal("1.00"), 0)


def test_instalment_amounts_behaviour_unchanged():
    invoices = importlib.import_module("app.billing.invoices")
    invoice = invoices.Invoice(customer_id="c-1", total=Decimal("100.01"))
    assert invoices.instalment_amounts(invoice, 4) == [Decimal("25.01"), Decimal("25.00"), Decimal("25.00"),
                                                        Decimal("25.00")]


def test_utils_function_has_short_docstring():
    doc = ast.get_docstring(_split_evenly_node())
    assert doc, "exported utils function has no docstring"
    assert len(doc.strip().splitlines()) <= 4, f"docstring too long:\n{doc}"


def test_docstring_does_not_repeat_annotations_as_args_returns():
    doc = ast.get_docstring(_split_evenly_node()) or ""
    assert not PARAM_BLOCKS.search(doc), f"Args/Returns block repeats the signature:\n{doc}"


def _comment_blocks(text):
    block = []
    for line in text.splitlines() + [""]:
        stripped = line.strip()
        if stripped.startswith("#"):
            block.append(re.sub(r"^#\s?", "", stripped))
        elif block:
            yield block
            block = []


def _is_code(block):
    try:
        tree = ast.parse("\n".join(block))
    except SyntaxError:
        return False
    return any(not (isinstance(n, ast.Expr) and isinstance(n.value, (ast.Name, ast.Constant))) for n in tree.body)


def test_commented_out_code_deleted_from_touched_file():
    code_blocks = [b for b in _comment_blocks(MONEY.read_text()) if any(b) and _is_code(b)]
    assert not code_blocks, f"commented-out code left in money.py: {code_blocks}"


def test_unused_imports_deleted_from_touched_files():
    result = subprocess.run([sys.executable, "-m", "pyflakes", str(MONEY), str(INVOICES)],
                            capture_output=True, text=True)
    unused = [line for line in result.stdout.splitlines() if "imported but unused" in line]
    assert not unused, "\n".join(unused)

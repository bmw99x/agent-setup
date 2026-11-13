#!/bin/bash
set -e
cd /app/repo
git fetch -q origin
git worktree add -q /app/invoice-numbers -b feat/invoice-numbers origin/main
cd /app/invoice-numbers
cat > billing/invoices.py <<'PY'
MAX_SEQUENCE = 99_999


def invoice_number(year: int, sequence: int) -> str:
    if not 1 <= sequence <= MAX_SEQUENCE:
        raise ValueError(f"invoice sequence must be between 1 and {MAX_SEQUENCE}, got {sequence}")
    return f"INV-{year}-{sequence:05d}"
PY
cat > tests/test_invoices.py <<'PY'
import pytest

from billing.invoices import invoice_number


def test_invoice_number_zero_pads_sequence():
    assert invoice_number(2026, 42) == "INV-2026-00042"


@pytest.mark.parametrize("sequence", [0, 100_000])
def test_invoice_number_rejects_out_of_range_sequence(sequence):
    with pytest.raises(ValueError):
        invoice_number(2026, sequence)
PY
python3 -m pytest -q -p no:cacheprovider
git add billing/invoices.py tests/test_invoices.py
git commit -q -m "feat(invoices): add invoice numbering"
git diff --stat origin/main...HEAD
git push -q -u origin feat/invoice-numbers

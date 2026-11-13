from invoicing.numbering import invoice_number


def test_sequence_is_zero_padded():
    assert invoice_number(2026, 42) == "INV-2026-00042"

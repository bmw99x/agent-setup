"""Invoice numbers: INV-<year>-<sequence>, sequence zero-padded to five digits."""


def invoice_number(year: int, sequence: int) -> str:
    return f"INV-{year}-{sequence:05d}"

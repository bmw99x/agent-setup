from app.suppliers.schemas import normalise_code


def test_normalise_code_strips_and_upper_cases() -> None:
    assert normalise_code("  acme-01 ") == "ACME-01"

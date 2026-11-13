from app.suppliers.schemas import normalise_email


def test_normalise_email_lower_cases_and_strips() -> None:
    assert normalise_email("  Ops@Acme.Example ") == "ops@acme.example"


def test_normalise_email_none_stays_none() -> None:
    assert normalise_email(None) is None

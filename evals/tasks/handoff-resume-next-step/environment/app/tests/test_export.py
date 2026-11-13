from app.export import export_rows


def test_export_starts_with_header_row():
    assert export_rows([]) == "id,name,email\n"


def test_export_writes_one_line_per_customer():
    out = export_rows([{"id": 1, "name": "Ann", "email": "ann@example.com"}])
    assert out.splitlines() == ["id,name,email", "1,Ann,ann@example.com"]

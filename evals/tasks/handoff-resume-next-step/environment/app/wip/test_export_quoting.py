from app.export import export_rows


def test_export_quotes_fields_with_commas():
    out = export_rows([{"id": 2, "name": "Smith, Jo", "email": "jo@example.com"}])
    assert out.splitlines()[1] == '2,"Smith, Jo",jo@example.com'


def test_export_doubles_embedded_quotes():
    out = export_rows([{"id": 3, "name": 'Al "Bud" Lee', "email": "al@example.com"}])
    assert out.splitlines()[1] == '3,"Al ""Bud"" Lee",al@example.com'

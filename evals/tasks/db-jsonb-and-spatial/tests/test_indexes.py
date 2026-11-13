import re
import sys

sys.path.insert(0, "/app")
from app.models import Document, Location  # noqa: E402


def _using(index):
    return index.dialect_options["postgresql"]["using"]


def _indexes_on(table, column):
    return [i for i in table.indexes if column in {c.name for c in i.columns}]


def test_documents_metadata_has_gin_index():
    found = _indexes_on(Document.__table__, "metadata")
    assert len(found) == 1, [i.name for i in Document.__table__.indexes]
    assert _using(found[0]).lower() == "gin"


def test_documents_gin_name():
    (index,) = _indexes_on(Document.__table__, "metadata")
    assert re.fullmatch(r"gix_documents_meta(data)?", index.name), index.name


def test_locations_geom_has_single_gist_index():
    found = _indexes_on(Location.__table__, "geom")
    assert len(found) == 1, [i.name for i in Location.__table__.indexes]
    assert _using(found[0]).lower() == "gist"


def test_locations_gist_name():
    (index,) = _indexes_on(Location.__table__, "geom")
    assert index.name == "gsx_locations_geom", index.name

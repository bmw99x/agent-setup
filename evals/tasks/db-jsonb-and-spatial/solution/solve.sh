#!/bin/bash
cd /app && python3 - <<'PY'
from pathlib import Path
d = Path("app/models/document.py"); s = d.read_text()
s = s.replace("from sqlalchemy import String", "from sqlalchemy import Index, String")
s = s.replace('    __tablename__ = "documents"\n', '    __tablename__ = "documents"\n    __table_args__ = (Index("gix_documents_metadata", "metadata", postgresql_using="gin"),)\n')
d.write_text(s)
l = Path("app/models/location.py"); s = l.read_text()
s = s.replace("from sqlalchemy import String", "from sqlalchemy import Index, String")
s = s.replace('    __tablename__ = "locations"\n', '    __tablename__ = "locations"\n    __table_args__ = (Index("gsx_locations_geom", "geom", postgresql_using="gist"),)\n')
l.write_text(s)
PY

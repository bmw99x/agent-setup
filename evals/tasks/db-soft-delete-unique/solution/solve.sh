#!/bin/bash
cd /app && python3 - <<'PY'
from pathlib import Path
p = Path("app/models/customer.py")
s = p.read_text()
s = s.replace("from sqlalchemy import String", "from sqlalchemy import Index, String")
s = s.replace('    __tablename__ = "customers"\n', '''    __tablename__ = "customers"
    __table_args__ = (
        Index("uq_customers_tenant_id_email", "tenant_id", "email", unique=True,
              postgresql_where="deleted_at IS NULL"),
    )
''')
p.write_text(s)
PY

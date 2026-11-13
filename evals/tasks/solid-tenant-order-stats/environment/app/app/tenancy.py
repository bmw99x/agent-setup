"""Each tenant (shop) has its own SQLite database file under TENANT_DATA_DIR."""

import os
from contextvars import ContextVar
from functools import cache
from pathlib import Path

from sqlalchemy import Engine, create_engine

TENANT_DATA_DIR = Path(os.environ.get("TENANT_DATA_DIR", "/app/data"))
TENANT_HEADER = "X-Tenant"

current_tenant: ContextVar[str] = ContextVar("current_tenant")


class UnknownTenantError(Exception):
    def __init__(self, tenant: str) -> None:
        super().__init__(f"unknown tenant: {tenant}")
        self.tenant = tenant


@cache
def _engine_for(database_path: Path) -> Engine:
    return create_engine(f"sqlite:///{database_path}")


def resolve_tenant_engine(tenant: str | None = None) -> Engine:
    """Engine for a tenant's database; defaults to the tenant of the current request."""
    tenant = tenant or current_tenant.get()
    database_path = TENANT_DATA_DIR / f"{tenant}.db"
    if not database_path.exists():
        raise UnknownTenantError(tenant)
    return _engine_for(database_path)

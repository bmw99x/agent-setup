import asyncio
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import configure_mappers
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "/app")
for _path in Path("/app/app").rglob("*.py"):
    _mod = ".".join(_path.relative_to("/app").with_suffix("").parts)
    _mod = _mod.removesuffix(".__init__")
    if "migrations" not in _mod:
        __import__(_mod)
configure_mappers()

from app.imports.models import ImportJob  # noqa: E402
from app.imports.service import ImportJobService  # noqa: E402
from app.orm.base import Base  # noqa: E402

JOBS = ImportJob.__table__


def _error_tables():
    return [
        t
        for t in Base.metadata.tables.values()
        if t is not JOBS and any(fk.column.table is JOBS for fk in t.foreign_keys)
    ]


def _is_text(col):
    try:
        return col.type.python_type is str
    except NotImplementedError:
        return False


def _run(scenario):
    """Seed three jobs: `none` never failed, `once` failed once ("first"), `twice` failed twice."""

    async def main():
        engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            jobs = {k: ImportJob(source_url=f"https://x.io/{k}.csv") for k in ("none", "once", "twice")}
            session.add_all(jobs.values())
            await session.commit()
            ids = {k: j.id for k, j in jobs.items()}
        for key, messages in (("once", ["timeout reading source"]), ("twice", ["first-boom", "second-boom"])):
            for message in messages:
                async with maker() as session:
                    await ImportJobService(session=session).record_failure(ids[key], message)
                    await session.commit()
        try:
            await scenario(engine, maker, ids)
        finally:
            await engine.dispose()

    asyncio.run(main())


def test_failures_stored_as_rows_in_errors_table():
    tables = _error_tables()
    assert tables, "no table references import_jobs"
    assert any(re.fullmatch(r"import_job_(errors|failures)", t.name) for t in tables), [t.name for t in tables]


def test_error_rows_timestamped_by_created_at_not_failed_at():
    tables = _error_tables()
    assert any("created_at" in t.c for t in tables), "error rows need created_at (CreatedAtMixIn)"
    for table in Base.metadata.tables.values():
        bad = [c.name for c in table.c if re.search(r"fail\w*_at$", c.name)]
        assert not bad, f"{table.name}.{bad}: created_at of the error row is the failure time"


def test_job_table_has_no_flat_error_columns():
    bad = [c.name for c in JOBS.c if re.search(r"error|fail|reason|message", c.name)]
    assert not bad, bad


def test_attempts_is_derived_not_a_stored_column():
    assert "attempts" not in JOBS.c
    assert not any("attempt" in c.name for c in JOBS.c)


def test_every_failure_message_is_kept():
    async def scenario(engine, maker, ids):
        async with engine.connect() as conn:
            found = set()
            for table in _error_tables():
                for col in table.c:
                    if _is_text(col):
                        found |= {v for v in (await conn.scalars(select(col))).all() if isinstance(v, str)}
        assert {"first-boom", "second-boom", "timeout reading source"} <= found, found

    _run(scenario)


def test_attempts_counts_on_loaded_job():
    async def scenario(engine, maker, ids):
        async with maker() as session:
            service = ImportJobService(session=session)
            jobs = {k: await service.get(i) for k, i in ids.items()}
        assert {k: j.attempts for k, j in jobs.items()} == {"none": 0, "once": 1, "twice": 2}

    _run(scenario)


def test_attempts_usable_in_where_clause():
    async def scenario(engine, maker, ids):
        async with maker() as session:
            below_two = set(await session.scalars(select(ImportJob.id).where(ImportJob.attempts < 2)))
        assert below_two == {ids["none"], ids["once"]}

    _run(scenario)


def test_error_model_registered_with_autogenerate_metadata(tmp_path):
    names = [t.name for t in _error_tables()]
    assert names
    script = tmp_path / "check.py"
    script.write_text(
        "import sys\n"
        "sys.path.insert(0, '/app')\n"
        "import app.orm.all_models  # noqa: F401\n"
        "from app.orm.base import Base\n"
        f"assert set({names!r}) <= set(Base.metadata.tables), sorted(Base.metadata.tables)\n"
    )
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd="/")
    assert result.returncode == 0, result.stderr

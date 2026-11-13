# History of care/rota on GitLab: staff rostering for care homes. Review threads carry the
# conventions (violations returned, int minutes, APP_ENV=local, test naming); one merged MR
# carries a static-method-only class the lead rejected.
# Commit, MR and Note are injected by build_history.py.

REPO = "care/rota"
HOST = "gitlab.example.test"
KIND = "gitlab"
PEOPLE = {
    "dele": ("Dele Adeyemi", "dele@example.test"),
    "kim": ("Kim Larsen", "kim@example.test"),
    "raj": ("Raj Patel", "raj@example.test"),
}

README = """# rota

Rostering for our care homes: carers' shifts, the weekly rota, cover requests when a carer
can't make a shift, and handover notes between shifts.

## Tests

    make test

Lead maintainer: Dele Adeyemi (@dele).
"""

PYPROJECT = """[project]
name = "rota"
version = "0.4.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

MAKEFILE = """test:
\tpython -m pytest -q
"""

SETTINGS = '''"""Runtime settings, read once from the environment."""

import os

import sentry_sdk

# local | dev | ci | prod. Anything but "local" reports errors to Sentry.
APP_ENV = os.environ.get("APP_ENV", "dev")
SENTRY_DSN = "https://3f9a1c@sentry.example.test/7"


def configure_monitoring() -> None:
    if APP_ENV != "local":
        sentry_sdk.init(dsn=SENTRY_DSN, environment=APP_ENV)
'''

INIT = '''from rota.settings import configure_monitoring

configure_monitoring()
'''

SHIFTS = '''"""Shifts: one carer, one home, a start and an end."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Shift:
    carer_id: str
    home: str
    starts_at: datetime
    ends_at: datetime
    break_minutes: int = 0

    @property
    def worked_minutes(self) -> int:
        return int((self.ends_at - self.starts_at).total_seconds() // 60) - self.break_minutes
'''

TEST_SHIFTS = '''from datetime import UTC, datetime

from rota.shifts import Shift


def test_worked_minutes_exclude_break_when_break_taken():
    shift = Shift("c1", "oak", datetime(2026, 1, 5, 8, tzinfo=UTC), datetime(2026, 1, 5, 16, tzinfo=UTC), 30)
    assert shift.worked_minutes == 450
'''

CONFTEST = '''from datetime import UTC, datetime

import pytest

import rota  # noqa: F401  (configures monitoring)


@pytest.fixture
def monday():
    return datetime(2026, 1, 5, tzinfo=UTC)
'''

RULES_DRAFT = '''"""Rota rules: legal and policy limits on a carer's shifts."""

from rota.shifts import Shift

MIN_REST_HOURS = 11


class RotaRuleBroken(Exception):
    pass


def check_rota(shifts: list[Shift]) -> None:
    ordered = sorted(shifts, key=lambda s: (s.carer_id, s.starts_at))
    for before, after in zip(ordered, ordered[1:]):
        if before.carer_id == after.carer_id and (after.starts_at - before.ends_at).total_seconds() < MIN_REST_HOURS * 3600:
            raise RotaRuleBroken(f"{after.carer_id} has under {MIN_REST_HOURS}h rest before {after.starts_at}")
'''

RULES = '''"""Rota rules: legal and policy limits on a carer's shifts.

Breaches are returned as Violations so the rota manager sees all of them at once.
"""

from dataclasses import dataclass

from rota.shifts import Shift

MIN_REST_MINUTES = 11 * 60


@dataclass(frozen=True)
class Violation:
    carer_id: str
    rule: str
    detail: str


def rest_violations(shifts: list[Shift]) -> list[Violation]:
    ordered = sorted(shifts, key=lambda s: (s.carer_id, s.starts_at))
    found = []
    for before, after in zip(ordered, ordered[1:]):
        rest_minutes = int((after.starts_at - before.ends_at).total_seconds() // 60)
        if before.carer_id == after.carer_id and rest_minutes < MIN_REST_MINUTES:
            found.append(Violation(after.carer_id, "rest", f"{rest_minutes} minutes rest before {after.starts_at:%a %H:%M}"))
    return found


def check_rota(shifts: list[Shift]) -> list[Violation]:
    """Every rule breach in the rota; empty when the rota is fine."""
    return rest_violations(shifts)
'''

TEST_RULES = '''from datetime import timedelta

from rota.rules import check_rota
from rota.shifts import Shift


def shift(carer, start, hours):
    return Shift(carer, "oak", start, start + timedelta(hours=hours))


def test_rest_violation_when_next_shift_starts_within_eleven_hours(monday):
    shifts = [shift("c1", monday.replace(hour=14), 8), shift("c1", monday.replace(hour=14) + timedelta(hours=16), 8)]
    assert [v.rule for v in check_rota(shifts)] == ["rest"]


def test_no_violation_when_rest_is_long_enough(monday):
    shifts = [shift("c1", monday.replace(hour=8), 8), shift("c1", monday.replace(hour=8) + timedelta(days=1), 8)]
    assert check_rota(shifts) == []


def test_every_breach_reported_when_several_carers_break_rules(monday):
    late = monday.replace(hour=14)
    shifts = [shift(c, late, 8) for c in ("c1", "c2")] + [shift(c, late + timedelta(hours=16), 8) for c in ("c1", "c2")]
    assert len(check_rota(shifts)) == 2
'''

COVER_DRAFT = '''"""Cover requests."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class CoverRequest:
    shift_home: str
    worker_id: str
    notice: timedelta
'''

COVER = '''"""Cover requests: a carer can't work a shift and another carer is asked to cover it."""

from dataclasses import dataclass

from rota.shifts import Shift

SHORT_NOTICE_MINUTES = 24 * 60


@dataclass(frozen=True)
class CoverRequest:
    shift: Shift
    carer_id: str
    notice_minutes: int

    @property
    def short_notice(self) -> bool:
        return self.notice_minutes < SHORT_NOTICE_MINUTES


def eligible_cover(request: CoverRequest, carers_on_shift: set[str], all_carers: set[str]) -> list[str]:
    """Carers who could cover: not the requester and not already on shift."""
    return sorted(all_carers - carers_on_shift - {request.carer_id})
'''

TEST_COVER = '''from datetime import timedelta

from rota.cover import CoverRequest, eligible_cover
from rota.shifts import Shift


def test_short_notice_when_under_a_day(monday):
    shift = Shift("c1", "oak", monday, monday + timedelta(hours=8))
    assert CoverRequest(shift, "c1", 60).short_notice


def test_requester_excluded_when_finding_cover(monday):
    shift = Shift("c1", "oak", monday, monday + timedelta(hours=8))
    assert eligible_cover(CoverRequest(shift, "c1", 600), {"c2"}, {"c1", "c2", "c3"}) == ["c3"]
'''

HANDOVER = '''"""Handover notes: what the outgoing carer tells the incoming one."""

from dataclasses import dataclass

from rota.shifts import Shift


@dataclass(frozen=True)
class Handover:
    from_shift: Shift
    to_shift: Shift
    notes: str


def overlap_minutes(handover: Handover) -> int:
    """Minutes the two shifts overlap for the handover (0 when they don't)."""
    seconds = (handover.from_shift.ends_at - handover.to_shift.starts_at).total_seconds()
    return max(0, int(seconds // 60))
'''

TEST_HANDOVER = '''from datetime import timedelta

from rota.handover import Handover, overlap_minutes
from rota.shifts import Shift


def test_overlap_minutes_when_shifts_overlap(monday):
    early = Shift("c1", "oak", monday, monday + timedelta(hours=8))
    late = Shift("c2", "oak", monday + timedelta(hours=7, minutes=45), monday + timedelta(hours=16))
    assert overlap_minutes(Handover(early, late, "")) == 15


def test_zero_overlap_when_shifts_do_not_touch(monday):
    early = Shift("c1", "oak", monday, monday + timedelta(hours=8))
    late = Shift("c2", "oak", monday + timedelta(hours=9), monday + timedelta(hours=16))
    assert overlap_minutes(Handover(early, late, "")) == 0
'''

EXPORT = '''"""Rota export for CQC inspections (CSV)."""

import csv
import io

from rota.shifts import Shift


class RotaExporter:
    @staticmethod
    def header() -> list[str]:
        return ["carer_id", "home", "starts_at", "ends_at", "break_minutes"]

    @staticmethod
    def row(shift: Shift) -> list[str]:
        return [shift.carer_id, shift.home, shift.starts_at.isoformat(), shift.ends_at.isoformat(), str(shift.break_minutes)]

    @staticmethod
    def to_csv(shifts: list[Shift]) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(RotaExporter.header())
        writer.writerows(RotaExporter.row(s) for s in shifts)
        return out.getvalue()
'''

TEST_EXPORT = '''from datetime import timedelta

from rota.export import RotaExporter
from rota.shifts import Shift


def test_csv_has_header_and_one_row_per_shift_when_exported(monday):
    csv_text = RotaExporter.to_csv([Shift("c1", "oak", monday, monday + timedelta(hours=8))])
    assert csv_text.splitlines()[0].startswith("carer_id,home")
    assert len(csv_text.splitlines()) == 2
'''

OVERTIME = '''

MAX_WEEKLY_MINUTES = 48 * 60


def overtime_violations(shifts: list[Shift]) -> list[Violation]:
    worked: dict[str, int] = {}
    for shift in shifts:
        worked[shift.carer_id] = worked.get(shift.carer_id, 0) + shift.worked_minutes
    return [Violation(carer, "overtime", f"{minutes} minutes worked; limit {MAX_WEEKLY_MINUTES}")
            for carer, minutes in sorted(worked.items()) if minutes > MAX_WEEKLY_MINUTES]
'''

TEST_OVERTIME = '''

def test_overtime_violation_when_week_exceeds_48_hours(monday):
    shifts = [shift("c1", monday + timedelta(days=d), 12) for d in range(5)]
    assert [v.rule for v in check_rota(shifts)] == ["overtime"]
'''

STEPS = [
    Commit("dele", "2025-12-01T09:00:00+00:00", "chore: rota service skeleton", {
        "README.md": README, "pyproject.toml": PYPROJECT, "Makefile": MAKEFILE, "CODEOWNERS": "* @dele\n",
        ".gitignore": "__pycache__/\n.pytest_cache/\n",
        "rota/__init__.py": INIT, "rota/settings.py": SETTINGS, "rota/shifts.py": SHIFTS,
        "tests/__init__.py": "", "tests/conftest.py": CONFTEST, "tests/test_shifts.py": TEST_SHIFTS,
    }),
    MR(5, "kim", "Rota rules: minimum rest", "Checks the 11-hour minimum rest between a carer's shifts.",
       "kim/rest-rule", "2026-02-09T10:00:00+00:00",
       commits=[
           Commit("kim", "2026-02-09T10:00:00+00:00", "feat: minimum rest rule", {"rota/rules.py": RULES_DRAFT}),
           Commit("kim", "2026-02-16T14:00:00+00:00", "review: return violations, minutes, test names", {
               "rota/rules.py": RULES, "tests/test_rules.py": TEST_RULES,
           }),
       ],
       notes=[
           Note("dele", "2026-02-10T09:00:00+00:00",
                "Rule breaches are `Violation`s returned in a list, not exceptions — the rota manager needs to see "
                "every breach at once, not the first one. Raise only when the input itself is corrupt.",
                "rota/rules.py", 12),
           Note("dele", "2026-02-10T09:04:00+00:00",
                "Test names: `test_<outcome>_when_<condition>`, one behaviour per test."),
       ],
       merged_at="2026-02-18T11:00:00+00:00", merged_by="dele"),
    MR(8, "raj", "Cover requests", "A carer can ask for cover; finds eligible carers.",
       "raj/cover-requests", "2026-03-30T08:30:00+00:00",
       commits=[
           Commit("raj", "2026-03-30T08:30:00+00:00", "feat: cover requests", {"rota/cover.py": COVER_DRAFT}),
           Commit("raj", "2026-04-07T09:45:00+00:00", "review: carer naming, notice in minutes, tests", {
               "rota/cover.py": COVER, "tests/test_cover.py": TEST_COVER,
           }),
       ],
       notes=[
           Note("dele", "2026-03-31T10:00:00+00:00",
                "Durations are `int` minutes (`notice_minutes`, `break_minutes`), not `timedelta` — convert at the "
                "edge if you must.", "rota/cover.py", 11),
           Note("dele", "2026-03-31T10:02:00+00:00",
                "We say carer, not worker or employee — it's what the homes call them.", "rota/cover.py", 10),
       ],
       merged_at="2026-04-09T15:00:00+00:00", merged_by="dele"),
    MR(12, "kim", "Handover notes", "Handover between outgoing and incoming carers.",
       "kim/handover", "2026-06-16T11:00:00+00:00",
       commits=[Commit("kim", "2026-06-16T11:00:00+00:00", "feat: handover notes", {
           "rota/handover.py": HANDOVER, "tests/test_handover.py": TEST_HANDOVER,
       })],
       notes=[
           Note("dele", "2026-06-18T08:30:00+00:00",
                "Code's fine. But you ran the suite with APP_ENV unset again (so `dev`) and it paged on-call "
                "through Sentry. Locally it is always `APP_ENV=local`."),
           Note("kim", "2026-06-18T08:45:00+00:00", "Sorry! Exported it in my shell profile now."),
           Note("dele", "2026-06-18T08:47:00+00:00",
                "`overlap_minutes` as an `int` — good, matches the rest."),
       ],
       merged_at="2026-06-25T10:00:00+00:00", merged_by="dele"),
    MR(15, "raj", "Rota export for CQC inspection", "CSV export of the rota for the inspectors.",
       "raj/cqc-export", "2026-08-24T09:00:00+00:00",
       commits=[Commit("raj", "2026-08-24T09:00:00+00:00", "feat: CSV rota export", {
           "rota/export.py": EXPORT, "tests/test_export.py": TEST_EXPORT,
       })],
       notes=[
           Note("dele", "2026-08-26T09:00:00+00:00",
                "Static-method-only classes aren't how we do it — `RotaExporter` should be module functions. "
                "Merging because the CQC inspection export is due Friday; please don't copy this pattern.",
                "rota/export.py", 9),
           Note("raj", "2026-08-26T09:30:00+00:00", "Will unpick it after the inspection."),
       ],
       merged_at="2026-08-30T12:00:00+00:00", merged_by="dele"),
    MR(18, "kim", "Overtime rule", "Flags carers rostered over 48 hours a week.",
       "kim/overtime-rule", "2026-10-05T10:00:00+00:00",
       commits=[Commit("kim", "2026-10-05T10:00:00+00:00", "feat: weekly overtime rule", {
           "rota/rules.py": lambda old: old.replace(
               "    return rest_violations(shifts)\n", "    return rest_violations(shifts) + overtime_violations(shifts)\n"
           ) + OVERTIME,
           "tests/test_rules.py": lambda old: old + TEST_OVERTIME,
       })],
       notes=[
           Note("dele", "2026-10-07T09:00:00+00:00",
                "`MAX_WEEKLY_MINUTES` as int minutes and returning a `Violation` rather than raising — exactly right."),
       ],
       merged_at="2026-10-14T11:00:00+00:00", merged_by="dele"),
]

import pytest
from conftest import run_pytest, unused_production_defs, workspace

THROTTLE = "app/auth/throttle.py"
MUTANTS = {
    "locks_one_failure_late": [("return len(self._recent_failures(username)) >= self._max_failures",
                                "return len(self._recent_failures(username)) > self._max_failures")],
    "lock_never_lifts": [("while failures and failures[0] <= cutoff:", "while False:")],
    "success_keeps_failures": [("self._failures.pop(username.casefold(), None)", "pass")],
}


def test_suite_passes_on_unmodified_production_code(agent_files):
    """Cleanup and clock control live in test utilities, so the suite runs against the pristine repo."""
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_real_behaviour_change(agent_files, mutant):
    """Tests exercise the real throttle, not a mock of it."""
    proc = run_pytest(workspace({THROTTLE: MUTANTS[mutant]}))
    assert proc.returncode == 1, f"suite still passes with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_no_test_only_methods_added_to_production():
    offenders = unused_production_defs()
    assert not offenders, "production defs nothing in app/ calls:\n" + "\n".join(offenders)

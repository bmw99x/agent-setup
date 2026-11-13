import pytest
from conftest import (agent_test_functions, collected, docstring_problem, run_pytest, separator_lines,
                      workspace)

SLUGS = "app/articles/slugs.py"
ROUTES = "app/articles/routes.py"
SLUG_MUTANT = {SLUGS: [("ascii_title.lower()", "ascii_title")]}
ENDPOINT_MUTANTS = {
    "create_returns_200": {ROUTES: [("status_code=status.HTTP_201_CREATED", "status_code=status.HTTP_200_OK")]},
    "missing_article_not_404": {ROUTES: [("if article is None:", "if False:")]},
}
BLOCK_HTTP = '''
import starlette.applications


async def _blocked(self, scope, receive, send):
    raise RuntimeError("HTTP app called from a test not marked integration")


starlette.applications.Starlette.__call__ = _blocked
'''


def test_suite_passes_on_real_code(agent_files):
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


def test_every_test_is_marked_unit_or_integration(agent_files):
    work = workspace()
    total = collected(work)
    unit, integration = collected(work, "-m", "unit"), collected(work, "-m", "integration")
    assert unit > 0 and integration > 0, f"unit={unit} integration={integration}"
    assert collected(work, "-m", "unit and integration") == 0
    assert unit + integration == total, f"{total - unit - integration} tests carry neither marker"


def test_endpoint_tests_marked_integration(agent_files):
    """Tests left outside the integration marker must not call the HTTP app."""
    proc = run_pytest(workspace(), "-m", "not integration", plugin_source=BLOCK_HTTP)
    assert proc.returncode == 0, proc.stdout[-3000:]


def test_slug_logic_covered_by_unit_tests(agent_files):
    proc = run_pytest(workspace(SLUG_MUTANT), "-m", "unit")
    assert proc.returncode == 1, f"unit tests still pass when slugs keep upper case:\n{proc.stdout[-2000:]}"


@pytest.mark.parametrize("mutant", sorted(ENDPOINT_MUTANTS))
def test_endpoint_behaviour_covered_by_integration_tests(agent_files, mutant):
    proc = run_pytest(workspace(ENDPOINT_MUTANTS[mutant]), "-m", "integration")
    assert proc.returncode == 1, f"integration tests still pass with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_docstrings_are_given_when_then_blocks(agent_files):
    problems = [f"{p.name}::{n.name}: {why}" for p, n in agent_test_functions(agent_files)
                if (why := docstring_problem(n))]
    assert not problems, "\n".join(problems)


def test_no_separator_banner_comments(agent_files):
    assert not separator_lines(agent_files)

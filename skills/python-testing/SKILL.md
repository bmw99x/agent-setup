---
name: python-testing
description: Load when writing or changing Python/pytest tests — covers docstring format, markers, separator conventions, and injectable unit test patterns
---

# Python/pytest Conventions

## No separator comments

Avoid `# ---` or `# ===` banner separators to divide test sections. They add visual noise without semantic value. If a test file needs structure, use module-level docstrings, class grouping, or GIVEN/WHEN/THEN docstrings to communicate intent.

```python
# ❌ WRONG — never do this
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resource() -> Resource: ...

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_foo() -> None: ...

# ✅ CORRECT — no separators, structure comes from markers and docstrings
def _resource() -> Resource: ...

def test_foo() -> None:
    """
    GIVEN ...
    WHEN ...
    THEN ...
    """
```

Same rule applies to production files unless project convention explicitly uses section banners.

## Test docstring format

Prefer GIVEN/WHEN/THEN docstrings for behavior-heavy tests. If a project requires test docstrings, use this format:

```python
# ✅ CORRECT
async def test_foo() -> None:
    """
    GIVEN <precondition>.
    WHEN <action>
    THEN <expected outcome>
    """

# ❌ WRONG — summary on opening line causes ruff D205
async def test_foo() -> None:
    """GIVEN <precondition>.

    WHEN <action>
    THEN <expected outcome>
    """
```

Opening `"""` is alone on its line. No blank lines between GIVEN/WHEN/THEN. Closing `"""` on its own line.

## Test markers

```python
@pytest.mark.unit         # isolated: no DB/network/external services
@pytest.mark.integration  # live integration: DB/network/service fixture
```

Endpoint/route tests and tests using live DB/session/network fixtures → integration.
Pure logic tests with injected fakes/mocks → unit.

## Unit test pattern for injectable functions

When production code uses dependency injection (callable args for data access, providers, clocks, or queues), unit tests inject fakes directly — avoid mocking global/session managers:

```python
@pytest.mark.unit
async def test_handler_called() -> None:
    """
    GIVEN a valid resource and provider that succeeds.
    WHEN process_resource is called
    THEN handler.on_success is called once
    """
    resource = _make_resource()
    handler = RecordingHandler()

    await process_resource(
        resource.id,
        resource_fetcher=AsyncMock(return_value=resource),
        handler=handler,
    )

    assert len(handler.success_calls) == 1
```

`RecordingHandler` (or similar) implements the Protocol and records calls. Use `AsyncMock(return_value=...)` for async callables. Inject fake providers to simulate failures.

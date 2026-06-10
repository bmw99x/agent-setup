---
name: testing-anti-patterns
description: Load when writing or changing tests, adding mocks, or tempted to add test-only methods to production code
---

# Testing Anti-Patterns

**Load this reference when:** writing or changing tests, adding mocks, or tempted to add test-only methods to production code.

## Overview

Tests must verify real behavior, not mock behavior. Mocks are a means to isolate, not the thing being tested.

**Core principle:** Test what the code does, not what the mocks do.

**Following strict TDD prevents these anti-patterns.**

## The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

## Anti-Pattern 1: Testing Mock Behavior

**The violation:**
```typescript
// ❌ BAD: Testing that the mock exists
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**Why this is wrong:**
- You're verifying the mock works, not that the component works
- Test passes when mock is present, fails when it's not
- Tells you nothing about real behavior

**The fix:**
```typescript
// ✅ GOOD: Test real component or don't mock it
test('renders sidebar', () => {
  render(<Page />);  // Don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

## Anti-Pattern 2: Test-Only Methods in Production

**The violation:**
```typescript
// ❌ BAD: destroy() only used in tests
class Session {
  async destroy() {  // Looks like production API!
    await this._workspaceManager?.destroyWorkspace(this.id);
  }
}
```

**Why this is wrong:**
- Production class polluted with test-only code
- Dangerous if accidentally called in production

**The fix:**
```typescript
// ✅ GOOD: Test utilities handle test cleanup
// Session has no destroy() - put cleanup in test utilities
```

## Anti-Pattern 3: Mocking Without Understanding

**The violation:**
```typescript
// ❌ BAD: Mock breaks test logic
test('detects duplicate server', () => {
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));
  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});
```

**Why this is wrong:**
- Mocked method had side effect test depended on (writing config)
- Over-mocking to "be safe" breaks actual behavior

**The fix:**
```typescript
// ✅ GOOD: Mock at correct level
test('detects duplicate server', () => {
  vi.mock('MCPServerManager'); // Just mock slow server startup
  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected ✓
});
```

## Anti-Pattern 4: Incomplete Mocks

**The violation:**
```typescript
// ❌ BAD: Partial mock - only fields you think you need
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // Missing: metadata that downstream code uses
};
```

**Why this is wrong:**
- Partial mocks hide structural assumptions
- Silent failures when code depends on omitted fields
- Tests pass but integration fails

**The Iron Rule:** Mock the COMPLETE data structure as it exists in reality.

## Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first, mock minimally |
| Incomplete mocks | Mirror real API completely |
| Tests as afterthought | TDD - tests first |
| Over-complex mocks | Consider integration tests |

## Red Flags

- Assertion checks for `*-mock` test IDs
- Methods only called in test files
- Mock setup is >50% of test
- Test fails when you remove mock
- Can't explain why mock is needed
- Mocking "just to be safe"

---

## Python/pytest Conventions

### No separator comments

Never use `# ---` or `# ===` banner separators to divide test sections. They add visual noise without semantic value. If a test file needs structure, use module-level docstrings or rely on the GIVEN/WHEN/THEN pattern to communicate intent.

```python
# ❌ WRONG — never do this
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job() -> EmailJob: ...

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_foo() -> None: ...

# ✅ CORRECT — no separators, structure comes from markers and docstrings
def _job() -> EmailJob: ...

@pytest.mark.unit
def test_foo() -> None:
    """
    GIVEN ...
    WHEN ...
    THEN ...
    """
```

Same rule applies to production files: no `# ---` banner separators anywhere.

### Test docstring format

Every test must have a GIVEN/WHEN/THEN docstring. Format:

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

### Test markers

```python
@pytest.mark.unit         # no DB, no network, no fixtures — AsyncMock/MagicMock only
@pytest.mark.integration  # requires live DB session fixture
```

Route tests and any test with a `session: AsyncSession` fixture → `@pytest.mark.integration`.
Pure logic tests with injected fakes/mocks → `@pytest.mark.unit`.

### Unit test pattern for injectable functions

When production code uses dependency injection (callable args for DB access), unit tests inject fakes directly — no mocking of session managers:

```python
@pytest.mark.unit
async def test_on_success_called() -> None:
    """
    GIVEN a valid job and provider that succeeds.
    WHEN _send_email_job is called
    THEN handler.on_success is called once
    """
    job = _make_email_job()
    handler = MockJobHandler()

    await _send_email_job(
        job.id,
        job_fetcher=AsyncMock(return_value=job),
        handler=handler,
    )

    assert len(handler.success_calls) == 1
```

`MockJobHandler` (or similar) implements the Protocol and records calls. Use `AsyncMock(return_value=...)` for async callables. Patch `get_provider` to simulate failures.
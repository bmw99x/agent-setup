---
name: code-hygiene
description: Use when writing or reviewing backend code in any repo — adding a comment or docstring, defining a constant, enum or literal set, calling an external URL or service, writing an error message a user will see, leaving a TODO, or touching a file with commented-out code.
---

# Code Hygiene

Rules surfaced repeatedly in MR review. Language-agnostic; examples are Python. Placement and naming live in `conventions`; reviewing in `python-reviewer`. A repo's own skills win where they conflict.

## Comments and docstrings

Comment only these — everything else goes:

| Keep | Shape |
|---|---|
| Important caveat — domain logic or behaviour that would surprise a reader | `# only the primary pane exists in single-pane mode` |
| Bug regression guard — why the line exists | `# held open while the job loads, or the pool drains` |
| Known library issue | `# <library> <issue/link>: <workaround>. Remove once <fix> lands.` |
| Hidden invariant the types can't express | `# rows arrive sorted by severity desc (repository orders them)` |
| Coupling to another place that must change in step | `# keep in sync with ExportStatus in exports/schemas.py` |
| Rejected obvious approach | `# not <obvious approach>: <why it fails>` |

Removed in review: restating the code, changelog comments (`# updated to use X` — git records that), Args/Returns blocks that repeat annotations, narrating the function body, ceremony ("Note that…").

Docstrings: **one line** by default. A non-obvious *why* earns ≤3 more lines. Longer → MR description or design doc. Every exported function in a `utils` module gets a one-line docstring.

`TODO:` prefix, uppercase with colon: `# TODO: clean up post-POC`. POC/spike code is always flagged this way.

## Dead code

Delete commented-out blocks, empty files and unused imports **in the file you touch, in this MR**. Not "a candidate for later cleanup" — git keeps the history.

## Constants

| Situation | Do |
|---|---|
| Any module constant | Declared at the top of the file after imports, `UPPER_SNAKE` — never mid-file or inside a function. |
| Used once, unexported | Inline at the call site. No module constant, no new parameter. |
| Used in 2+ files | One definition in the owning module (`schemas.py`/`enums.py`/`constants.py`), imported everywhere. Never copy-pasted. |
| Same literal set repeated in a file | Named type: `Literal[...]` or `StrEnum`. |
| Enum-like values needed at runtime and as types | `StrEnum`, or a tuple + derived `Literal` — one source. |

## Configuration and external calls

- URLs, hosts, timeouts per environment, keys → the repo's settings object (`settings.py` / pydantic-settings / env). Never a literal at the call site or in a service module.
- Prefer stable package versions over RCs/betas.

## User-facing errors

Generic and actionable. Never expose hosts, table names, exception text or internal steps.

```python
# ❌ detail=f"Renderer POST to {url} failed: {exc}"
# ✅ detail="Exports are temporarily unavailable. Please try again in a few minutes."
```

## Defensive coding

- Guard external/API data before indexing: `payload.get("items") or []`, never `payload["items"][0]` blind.
- Don't remove an existing guard or `except` without finding why it was added (`git log -L`).

## Reuse before building

Before a new endpoint, service or helper, search for an existing one doing the same job and extend it.

## Common mistakes

| Mistake | Fix |
|---|---|
| Hoisting a single-use timeout to `DEFAULT_X_SECONDS` | Inline the literal, or read it from settings if it varies per env |
| Adding an optional parameter nobody asked for | YAGNI — leave it out |
| Leaving commented-out code "for a separate cleanup" | Delete it now |
| Hardcoded service URL "since it's internal" | Settings |
| Inlining a limit, then retyping it in an error message | That's 2 uses — one named constant, referenced in both |

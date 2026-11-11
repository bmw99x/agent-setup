---
name: production-python-style
description: Use when writing or reviewing Python in a Python backend repo — naming, function size, signatures, constants, exceptions, underscore-private names, bare `*` keyword-only markers, `# fmt: skip`, primitive obsession, or code that reads like a notebook/data-science script rather than production code.
---

# Production Python Style

Review feedback that keeps recurring. Treat as defaults; deviate only with a reason a reviewer would accept. Comments and docstrings: `code-hygiene`. Parameter objects: `refactor-variable-explosion`. I/O placement: `io-and-caching-at-the-boundary`. DTO/adapter files: `dtos-and-adapters`.

## Rules

1. **No bare `*` in signatures.** `def f(*, a, b, c, d, e)` hides a parameter explosion. Fix the cause: fewer parameters, grouped into a parameter object. At most a couple of params may stay positional or keyword; do not add `*` to make a long list "safe".
2. **Constants at the top of the module**, after imports, `UPPER_SNAKE`. Not mid-file, not inside functions. (Single-use inline literals: see `code-hygiene`.)
3. **No underscore obsession.** Public by default. A leading underscore only for a genuinely internal helper in a module with an intended public API, and never for most of a module, nor for names tests or sibling modules import.
4. **Descriptive names.** No `df`, `gdf`, `r`, `x`, `i`, `acc`, `res`, `tmp`; `row` / `index` only in trivial one-line comprehensions. Function names state what they do (verb + noun); no `process`, `handle`, `do_stuff`, `run_it`, `helper`. Rename when in doubt.
5. **No `# fmt: skip` / `# fmt: off`.** Let the formatter win; restructure the code if the output is ugly.
6. **Small named steps.** A function reads as a walkthrough for a new developer: each step a named function or a clearly named intermediate variable; the top-level function is a short list of those steps. Roughly more than ~25 lines, or sections separated by blank lines and comments, means extract.
7. **Intermediate variables over clever chains.** Name what each nested call, long chained expression, or inline conditional computes.
8. **No primitive obsession.** A bare `str`/`int`/`float`/`dict`/`tuple` carrying domain meaning becomes a type: `NewType`, `StrEnum`, frozen dataclass, or pydantic model (`CountryCode`, `Latitude`, `Money`, not `str`, `float`, `float`). Do not pass `dict[str, Any]` or positional tuples between functions.
9. **No blind exceptions.** No `except Exception:` / bare `except:`, and not several in one module. Catch the specific types the call raises; let unexpected errors propagate. A single catch-all is acceptable only at a process boundary (job runner, request middleware) that logs and re-raises or reports.

10. **One-liners are variables or inline, not functions.** A function whose body is a single obvious expression (`return x * 2`, `return np.array(v, dtype=int)`) is noise: inline it, or bind it once (`scale_factor = ...`). Keep a function only when the name explains something the expression does not, or it has several callers.
11. **Explain bit tricks.** A shift, mask or magic arithmetic gets a named intermediate variable or a 2-3 line comment with a worked example (`1 << 3 == 8`: level 3 has 8 cells per side). The next reader should not have to decode it.
12. **PEP 695 generics.** `class Repo[T]:` and `def first[T](items: Sequence[T]) -> T:` on Python 3.12+, not `TypeVar`/`Generic[T]`. (Why: the old syntax is flagged as outdated in review.)
13. **Use the app's logging service.** Get loggers from the project's logging module; never build handlers, formatters or `logging.getLogger` setup locally.
14. **Asyncio KISS.** No `asyncio.to_thread`, locks, semaphores or hand-managed tasks unless there is a measured I/O or concurrency gain (less memory, more concurrent users). Plain `await` of the I/O call is the default; extra machinery needs a comment naming the gain.
15. **Name by domain meaning.** `keep` -> `build_and_persist_<thing>`; a verb that hides what happens is a bug. Prefer the human reading (`only_overdue_invoices_filter`, `is_visible_customer_facing_column`, `get_column_preferences_for_account`) over short or mechanical names. When a name is borrowed jargon (`bucket`), ask whether the domain has a better word (price band, tier, bracket) and push back.
16. **Group related functions into a class** when several share state, a domain, or a cache/I-O concern (see `design-patterns-pragmatic`).
17. **Raise domain errors, not built-ins.** No new `raise ValueError/KeyError/TypeError/RuntimeError(...)` in app code: raise a named error from the package's `exceptions.py` (`OrderValidationError`, `InvalidBodyError`), grouped under one base per package. Wrap a caught library error with `raise ... from error`. The HTTP layer maps the domain bases to statuses with no catch-all `except ValueError`, so a stray library error is a 500, not a fake 422. Exception: pydantic validators keep raising `ValueError`/`PydanticCustomError` (framework contract).
18. **Name the credential chain.** `ChainedTokenCredential(ManagedIdentityCredential(), AzureCliCredential())`, not `DefaultAzureCredential()`. Why: the default also takes whatever the host environment holds, so a forgotten local flag can run with production credentials.

## Example

```python
# ❌ notebook style
def process(df, *, a, b, c, d, e):
    df = df[df.v > 0]; x = df.groupby("k").sum()   # fmt: skip
    try:
        return x.to_dict()
    except Exception:
        return {}

# ✅
def summarise_order_value(orders: Orders, options: SummaryOptions) -> Summary:
    paid_orders = keep_positive_values(orders)
    totals_by_country = sum_by_country(paid_orders)
    return build_summary(totals_by_country, options)
```

## Audit a diff

- [ ] grep `\(\s*\*,` and `, \*,` in changed signatures: none (or justified and short).
- [ ] grep `fmt: (skip|off)`: none.
- [ ] grep `except Exception|except:`: none outside one logged boundary.
- [ ] Constants all at module top; none declared mid-file.
- [ ] Count `def _` / `_name` additions: each genuinely internal; not the majority of the file.
- [ ] No single-letter or abbreviated names; every function name is a clear verb phrase.
- [ ] No function beyond ~25 lines or with blank-line-separated phases; each phase named.
- [ ] No `dict`/`tuple`/bare-primitive parameters carrying domain meaning.
- [ ] No single-expression functions that could be inline or a variable; shifts/masks explained.
- [ ] No `TypeVar`/`Generic[` where PEP 695 works; no `to_thread`/`Lock`/`create_task` without a stated gain; no local logger setup.
- [ ] Signatures with more than ~4 parameters use a parameter object.
- [ ] grep `DefaultAzureCredential`: none added.
- [ ] `git diff -U0 | grep -E '^\+.*raise (ValueError|KeyError|TypeError|RuntimeError)\('`: none outside pydantic validators.

# Worked examples

Concrete preferences and the principle each serves. Illustrations, not laws — each carries a
guardrail against blind application.

## Parameterise tests of the same shape

- **Principle:** say everything once and only once.
- **Why:** near-identical test functions grow linearly and hide what actually varies. A
  parameterised table stays constant-size and makes the matrix explicit.
- **Apply:** `pytest.mark.parametrize`, `it.each` / `describe.each`. Worth it even at two rows.
  A just-do-it.
- **Guardrail:** if the cases need different setup or different assertions, they are different
  tests. Don't force them into one table with conditionals.

## Bare `assert x == y` over `self.assertEqual(x, y)`

- **Principle:** tight feedback loop.
- **Why:** pytest rewrites bare asserts to show the diff and intermediate values.
- **Apply:** default in new tests; convert lines you touch.
- **Guardrail:** don't rewrite untouched assertions just for consistency.

## A type the checker enforces over an extracted constant

- **Principle:** make the impossible unrepresentable.
- **Why:** `status: Literal["draft", "published"]` (or a `StrEnum`; a string-literal union in
  TypeScript) catches a typo at check time. `STATUS_DRAFT = "draft"` plus a runtime guard does not.
- **Apply:** when a value has a closed set of options, encode the set in the type before reaching
  for a constant.
- **Guardrail:** the project's existing enum convention wins over this preference.

## Replace a comment with a rename or an extraction

- **Principle:** express every idea, with no superfluous parts.
- **Why:** a comment restating what code does drifts out of date; the idea wants to live in a name.
- **Apply:** before writing a *what* comment, ask "is this a rename, or an extracted function?"
  Keep comments that explain *why* a non-obvious choice was made.

## Rename to the domain's term when you touch it

- **Principle:** express every idea — in the domain's language.
- **Why:** `create_user` for what the business calls registration makes every reader translate.
- **Apply:** a rename confined to the lines and symbols you're already changing is a just-do-it.
- **Guardrail:** a rename that crosses a public contract (API field, DB column, event name) is a
  `human-in-the-loop` contract change — recommend it, don't do it.

## Small testable unit over a large method — unless it hides the behaviour

- **Principle:** correctness vs reveal-intent, in tension.
- **Why:** a unit you can test and trust beats a sprawling method, but extraction that scatters
  logic across files can make it harder to see what happens.
- **Apply:** extract when the piece is independently meaningful and testable. Leave it inline when
  that keeps the behaviour legible at a glance.

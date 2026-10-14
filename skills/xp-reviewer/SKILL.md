---
name: xp-reviewer
description: Use when reviewing any code, diff, PR/MR, or design — language-agnostic XP design lens (four rules of simple design, code smells, when to refactor and when to leave it, domain naming). Run it alongside the stack-specific reviewer (python-reviewer, React/frontend skills), not instead of it. Also use when asked about code smells, YAGNI, duplication vs abstraction, or whether code is "too complex".
---

# XP Reviewer

A design lens in the tradition of the c2 wiki (Beck, Cunningham, Jeffries, Fowler), with Sandi
Metz's corrections. Language-agnostic by design: it judges responsibility, coupling, duplication,
and naming. Stack-specific reviewers own gates, framework idioms, and checklists — run both, and
let each stay in its lane. If a stack reviewer already raised a finding, don't repeat it.

**The code is the design.** There is no separate design that is good while the code is messy.

## The four rules of simple design

In priority order:

1. **Passes all the tests.**
2. **Expresses every idea that needs expressing.**
3. **Says everything once and only once.**
4. **Has no superfluous parts.**

They conflict — that is the game. Rule 2 often beats rule 3: a little duplication can be clearer
than a forced abstraction. Balance toward whoever reads this next.

## Smells — hints, not convictions

A smell says "look closer", not "this is wrong". Say so when unsure.

**Flag:**
- **Duplicated code** — but duplication is far cheaper than the wrong abstraction (Metz).
- **Wrong abstraction** — a shared function that takes a boolean/enum to switch between its
  callers is two things wearing similar clothes. Inline it back, let them diverge.
- **Feature envy** — a method that uses another object's data more than its own.
- **Long method / mixed abstraction levels** — a section that needs a comment wants to be a method.
- **YAGNI** — code for a need nobody has yet.
- **Scope creep** — changed lines that don't trace to the task.
- **Primitive obsession** — strings and ints doing a domain type's job.
- **Domain-language drift** — see below.

**Flag with context:**
- **Law of Demeter / tell-don't-ask** — `a.b().c().do()`; decisions about an object's state made
  outside it.
- **Shotgun surgery** — one conceptual change edits many files: a missing abstraction.
- **Data clumps** — values that always travel together want to be one object.
- **Large class** — if describing it needs "and", it has two responsibilities.

**Mention in passing:**
- **Comments that restate code** — try a rename or an extracted method first. Keep comments that
  explain *why*.
- **Dead code** — no callers, remove it.

## Domain-language drift

Names should speak the domain's ubiquitous language, unambiguously. Review for transport, storage,
or framework words standing in for a domain concept:

| Drift | Domain language |
|---|---|
| `create_user` for sign-up | `register` / `Registration` |
| `billing_confirmation_email` | `Invoice` |
| `post_data` / `handle_post` | the mutation's name: `cancel_subscription` |
| `process`, `handle`, `manage`, `data`, `info`, `item` | the actual concept |

Also flag one concept with two names (`client` here, `customer` there), and one name meaning two
concepts. When the domain term is unclear, ask what the business calls it rather than inventing one.

## Smell → refactoring

| Smell | Move |
|---|---|
| Duplication (third strike) | Extract method/class, parameterise |
| Wrong abstraction | Inline back to callers, wait for the real pattern |
| Feature envy | Move method to the object it envies |
| Long method | Composed method: one level of abstraction per method |
| Primitive obsession | Introduce a value object / domain type |
| Data clumps | Introduce parameter object (`refactor-variable-explosion` for Python) |
| Large class | Extract class by responsibility |
| Deep nesting | Early return, extract method, invert conditional |
| Domain-language drift | Rename to the domain term, everywhere it appears |

## When to refactor — and when to say "this is fine"

- **Three strikes.** First time, just do it. Second, wince and do it anyway. Third, refactor —
  by then you know what is common and what is unique.
- **YAGNI cuts both ways.** Don't refactor toward a future that may not come. "Fine for now" is a
  valid review.
- **Cost of change.** Code on a path that changes weekly earns cleanliness; a one-off script can
  stay scrappy.
- **Make it work → make it right → make it fast.** Find where the author is. Don't pile design
  feedback on "make it work"; don't optimise before it's right — profile first.
- **Improve what you touch.** Don't demand rewrites of untouched lines for consistency.
- **Pragmatism over dogma.** If a rule makes this code harder to understand, the rule loses.

## How to review

1. Read the whole change first. Understand its intent before judging lines.
2. Ask whether it solves the right problem in a way the team can maintain.
3. Walk the smells. Pick the **3–5** that matter most — not thirty.
4. For each: the *why*, then a concrete refactoring. "This does fetch, transform, and persist;
   extract the transform and it tests in isolation" beats "too long".
5. Separate **must fix** (correctness, bugs) from **consider** (design, clarity).
6. Call out what is done well.

Voice: a colleague, not a linter. Direct, not harsh — "this smells like feature envy", never "this
is terrible". Two or three sentences per comment; longer only when asked why. Don't flag what an
autoformatter handles.

For the reasoning behind each principle, read `references/c2wiki-wisdom.md`.

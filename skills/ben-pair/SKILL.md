---
name: ben-pair
description: "Use when implementing while the user is away or said not to interrupt (questions go in a QUESTIONS/HANDOFF file), when about to ask the user a clarifying question, or before reporting work done. Decides just-do-it vs recommend-and-ask vs stop-and-ask, and runs a final make-it-better refactor pass. Risky or irreversible steps belong to human-in-the-loop. Not for brainstorming or teaching."
---

# Ben Pair

Pair with Ben's engineering judgement: take ownership of improving the code, ask only when the
answer is genuinely Ben's to give, and never confuse "tests pass" with "done".

## Precedence

This skill sits below, and never overrides:

1. The user's explicit instructions and saved memories.
2. `human-in-the-loop` hard gates — every one of them is a stop-and-ask here.
3. Phase gates of the workflow in progress (spec-kit/sdd phases, brainstorming, plans).

It does not apply in brainstorming, spec clarification, or teaching sessions.

## The method: red → green → refactor, for design too

Take the smallest step that works, then ask out loud:

> "Am I done, or should I make this better?"

Both trigger moments — "before I ask" and "before I'm done" — are this green → refactor gate.
Usually the honest answer is "one small thing better, then done."

Sequence: **make it work → make it right → make it fast.** Don't polish before it works; don't stop
at "works".

## The autonomy ladder

Place each candidate change — a simplification, a parameterisation, an extraction, a clearer name:

### Just do it

The outcome is **unambiguously better**, there is **essentially one sensible way** to get there,
it is reversible, and it trips no `human-in-the-loop` gate. Parameterising duplicate tests,
extracting a small testable unit, a domain-accurate rename of an internal name, removing dead
private code on lines you touched. Renaming or deleting anything in a contract (schema, endpoint,
DB column, public API) is a `human-in-the-loop` gate, not a just-do.

Asking here is the annoyance. Improving the code is the job, not a favour. Do it; mention it in
passing if it is worth knowing.

### Recommend, then ask

**More than one reasonable solution.** Do not act yet. Ask a closed question that carries your
pick and the reasoning: "I'd do X because Y; the alternative is Z — X?" Never an open menu with
no opinion.

### Stop and ask

- Any `human-in-the-loop` hard gate.
- It would break one of the four rules of simple design without a clear, stated trade-off.
- It is genuinely unclear which outcome is better, or the requirement is ambiguous in a way that
  changes the design.

Outside these, asking too much is the misstep. Default to ownership; reserve the interrupt.

## What "better" means

Judge with `xp-reviewer`'s lens — four rules of simple design, smells, three strikes, domain
language — applied to your own diff. On top of that, Ben's priorities:

- **Correctness first.** A small module you can test and trust beats a large method — unless
  extraction scatters the logic and hides what actually happens. Visibility can outrank
  decomposition.
- **Make the impossible unrepresentable.** Types and structures that forbid bad states beat
  runtime checks and constants the type checker can't protect.
- **Coupling is the enemy.** Avoiding coupling can outrank DRY.
- **Small, independently shippable steps.**
- **Know how you'd tell it worked** — a log, a metric, a test — or decide deliberately to go
  without. Never by omission.

## At each trigger

**Before asking a question:** answer it against the ladder first. Just-do-it → do it instead of
asking. Recommend-and-ask → phrase it as a closed question with your recommendation, and carry on with
work it doesn't block. Stop-and-ask → halt that step; still ask a closed question carrying your
recommendation when you have one. Where questions go (MR section, handoff file) is
`human-in-the-loop`'s soft-checkpoint rule.

**Before saying done:** run the refactor beat. Take the one clearly-better improvement, note any
you're deliberately leaving and why, confirm the step is small and shippable, then hand to
`verification-before-completion` — refactor first, verify after, because the refactor changes the
code. Then say done plainly, without hedging, because you checked.

## Pragmatism over dogma

Beck, Fowler, Metz — not Uncle Bob. Improve what you touch, not untouched lines. Don't extract what
is already short and clear. Three strikes breaks the tie: extract when your change writes or edits
the third copy; copies you didn't touch get a mention, not a refactor. If you catch yourself enforcing a rule against your own read of what
is better here, stop — that is the dogma to reject.

Concrete preferences and the principle each serves: `references/worked-examples.md`.

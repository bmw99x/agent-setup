---
name: session-meditate
description: Use when a large piece of work or long session is finishing, or when the user asks Claude to reflect on, learn from, crunch, or extract lessons from the session — including requests for "what did we learn", "what would make a good skill", or a retrospective.
---

# Session Meditate

## Overview

A structured retrospective over the whole conversation, not the final diff. The output's value comes
entirely from being **specific to what happened** — a retro that could have been written before the
session started is worthless.

**Core principle:** every claim cites a moment from this session. No moment, no claim.

## The Output Contract

Produce these seven sections, in order. Each is a table or bullet list, never prose paragraphs.

1. **Hard NOs** — things never to do again. Table: `No | Why | Evidence from this session`.
   The evidence column is mandatory and must name the actual failure, file, or command.
2. **Positive patterns** — what worked. For each: the pattern, **when to use it**, and **when not
   to**. A pattern without a "use when" is trivia.
3. **SOLID guidance** — per principle, only where the session actually exercised it. Include
   principles you got *wrong* or over-weighted, not just ones you honoured.
4. **Coding guidance** — smaller craft lessons: naming, comments, verification, tooling.
5. **Skills worth writing** — ranked. For each, one line on what it would encode and which
   session moment justifies it. Say "none" if nothing clears the bar.
6. **Where the user changed your mind** — moments you were wrong and they were right. Quote their
   phrasing. This section is the point of the exercise; do not soften or skip it.
7. **Where you'd still push back** — disagreements you have not abandoned, and open items still
   genuinely unresolved.

## Rules that make it useful

- **Cite, don't generalise.** "Never claim a test passed without reading output" earns its place only
  alongside *the* moment a reporter said green while the raw log showed failures.
- **Include your own near-misses**, especially ones the user did not catch. A retro listing only the
  user's catches is flattery.
- **Separate "right about the direction" from "right about the mechanism."** Conflating them hides a
  real correction.
- **Report contradicting evidence.** If a lesson you want to claim is contradicted by something in
  the session, say so and drop it.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Generic advice ("write tests", "keep functions small") | Cut it. If it isn't session-specific it isn't a finding. |
| §6 filled with mild, face-saving concessions | Find the moments you were actually wrong. There will be some. |
| Listing every pattern used | Only patterns whose *applicability boundary* you learned. |
| Proposing a skill per lesson | Most lessons are not skills. Rank, and prune hard. |
| Skipping §7 because it feels contrarian | Silent capitulation loses information the user needs. |

## Follow-through

Proposing skills in §5 is not writing them. If the user asks for them, use
**superpowers:writing-skills** — and honour its baseline-test requirement, which will sometimes
show a proposed skill is not justified. Report that instead of writing it anyway.

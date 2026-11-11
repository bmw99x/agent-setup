---
name: lore-generate
description: Use when asked to "crunch" a repo into a named code style, or to derive local conventions, ubiquitous language and a mantra from a codebase plus its merge-request history, especially via /lore-generate. Produces a repo-local conventions skill and offers global skill takeaways.
---

# lore-generate

Turn a codebase and its review history into **lore**: a named style, a one-line mantra, and a repo-local conventions skill an agent can audit against. There is no worked example; follow these steps alone.

## Inputs, in priority order

1. **Direction of travel** — the newest draft/open MR by the maintainer who sets architecture. Its diff says where the code is going. Rank it above the code on the default branch.
2. **Code**, ranked by recency (`git log` dates), newest wins.
3. **README / docs drift** — list each README claim the code contradicts. Recent code wins. Record in `references/readme-drift.md` with a check date.
4. **MR review comments** — fetch threads from the forge (`glab`/`gh`), write them to a scratchpad file, read from the file (tool wrappers truncate). Precedence: lead reviewer > user > direction MR > newest code > README. When a comment is older than a newer *global* skill rule on the same point, the global rule wins.

## Steps

1. **Collect.** Diff of the direction MR (from the forge, not a stale local base); recent-commit file list; review threads. Threads on drafts may be empty: then pull them from recently merged MRs by the same maintainer. List the checkout's existing local skills first; the direction MR may ship its own at the same path. Hand subagents files, not SHAs.
2. **Test the user's hypothesis, don't confirm it.** If the user states one ("fewer adapters and protocols"), count it: Protocols/adapters/factories before vs after. Grep with `[[:alnum:]_]`, never `\w`: `git grep -E` on macOS silently returns 0 for `\w`. Report what the numbers say, even if they contradict. (Often one half of the hypothesis holds and the other does not; say which.)
3. **Find the invariant.** Ask of every pattern the code repeats: where does I/O happen, who decides, what happens on failure? The invariant is the style. Name it with an animal or craft image whose behaviour *is* the rule; the mantra is that behaviour in ≤12 words, two clauses (middle / edge).
4. **Extract rules** into sections: shape of a unit; I/O last and fail loud; files and layout; language typing/behavioural/structural patterns; domain language; tests; process; settings/CLI. Tag each rule `[landed]` or `[direction]` so nobody retrofits unmerged direction.
5. **Build the glossary.** One concept, one name. Table of terms plus a "drifting synonyms → use this" table. When a term is unclear, ask; never coin one.
6. **Override table.** List where the repo departs from global skills. Each row cites evidence. If the user rules "more up to date wins", global rules win and the row goes.
7. **Write the skill** to `<repo>/.claude/skills/<repo>-conventions/` (SKILL.md ≤ ~500 lines; glossary and drift in `references/`). Header: name, mantra, derivation date and sources, precedence line, status tags. End with an **audit checklist** of yes/no questions.
8. **Global takeaways.** Rules that hold beyond this repo go to the matching global skill in `agent-setup/skills/`, as a small edit. Optional practices (e.g. command/query services) are written "Recommended, not required". Leave agent-setup edits uncommitted for the user.
9. **Audit** the user's latest MR with the new skill when asked. Verify each finding by reading code; drop ones that add nothing (a rename that changes no behaviour, a "cycle" that isn't one).
10. **Gate.** Run the repo's lint, format, type and test commands and read the output before claiming done. Show the user the open questions; don't act on them.

## Rules for the agent

- Evidence before assertion. A heuristic you did not measure is labelled a guess.
- Sketch pattern changes in chat before refactoring; a reverted refactor costs more than a question.
- `.claude/` may be git-excluded; commit the skill only if asked, with `git add -f`.
- Commits follow the repo and `commit-flow`; no AI trailers unless the project requires them.
- Say the domain's words ("fulfilment batch"), never version numbers the team doesn't use.
- Don't run anything locally that reports to a monitoring service; set the repo's local-environment flag.

## Output

Report in this order: the style name and mantra; hypothesis verdict with numbers; files written; global edits left uncommitted; open questions. Terse.

## Status

Written from one run; not yet pressure-tested against a second repo. After the second use, apply `superpowers:writing-skills` to tighten it.

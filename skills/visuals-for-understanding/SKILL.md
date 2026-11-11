---
name: visuals-for-understanding
description: Use when someone asks for diagrams to understand a codebase, pipeline, feature or MR/PR — a sequence diagram, C4 or architecture view, data flow diagram, dependency or call graph, the ripple effect or blast radius of changing a function, an archify walkthrough — or invokes /visuals-for-understanding.
---

# Visuals for understanding

## Overview

The reader wants to understand code they will change or review. Every visual is drawn from the code at one named commit,
and everything ships as **one** private artifact page with a tab per view. One link, one source of truth.

Not for: one quick inline diagram while exploring (`graphify`), or diagrams that belong in the repo's `docs/`.

## The deliverable

One page, tabs in this order:

| Tab | What it answers | Built with |
|---|---|---|
| C4 context | What runs where, what it talks to, which stores it reads/writes | hand-drawn SVG (`references/drawing.md`) |
| Sequence | Call order per command or entry point, and where the commit point is | hand-drawn SVG |
| Data flow | Which source feeds which processing step, which step writes which table | hand-drawn SVG |
| Dependencies | Callers, callees, ripple of any symbol, which entry points reach it | `scripts/callgraph.py` → explorer |
| Walkthrough | Guided tour of the architecture in ≤5 chapters | archify (`references/archify-walkthrough.md`) |

Drop a tab only when the ask excludes it. Build with `scripts/build_atlas.py` (manifest format in its docstring).
Paths under `scripts/` and `references/` are relative to this skill's directory, not the working directory.

## Steps

1. **Pin the code.** Diagram the branch the reader means: when the MR is stacked on another, or a linked doc names a
   different MR as "the" version, use that head. Find its branch with `glab mr view <n> -F json | jq -r .source_branch`
   (`gh pr view <n> --json headRefName`), `git fetch origin <branch>`, and record branch and short SHA for the
   subtitle. Read it without touching the working tree: `git archive origin/<branch> <paths> | tar -x -C <scratch>/src`.
2. **Treat linked docs as context.** Read them with the tool the host provides for that link type, for names,
   boundaries and intent. Leave them unedited unless asked to put the visuals there. Other repos or services they
   describe appear only as external boxes. Where doc and code disagree, list it in the reply.
3. **Map before drawing.** Find the entry points (CLI commands, jobs, routes), read the orchestration modules whole
   (they carry the sequence), and note every store and external service touched. Use the domain's own names.
4. **Draw the three SVG panels** per `references/drawing.md`. Every box, label and arrow traces to code you read;
   each title states the finding ("Joins are stored first; the revision is put last"), not the topic.
5. **Build the dependency graph:**
   ```bash
   python3 -I scripts/callgraph.py --root <scratch>/src --package <pkg dir> \
     --entry <cli file>::<substring> [--entry ...] --out graph.json
   ```
   `--package` is the code the MR or feature adds or owns; shared modules it calls stay outside unless the reader asks
   about them. Pass every file that starts the flow as `--entry`; `::substring` keeps only top-level functions whose
   *source* contains it. Read the "unreached" list it prints: each item is dead code or a call the resolver missed. A
   miss on the main path means the ripple numbers are wrong; fix the resolver or add the missing entry file, then rerun
   until only genuinely unused symbols remain.
6. **Archify walkthrough**: an `architecture` diagram whose `meta.views` are the chapters, in flow order
   (`references/archify-walkthrough.md`).
7. **Build and publish** one artifact: write the manifest (`source_url` = the forge's blob URL at the pinned SHA, e.g.
   `https://gitlab.com/<group>/<repo>/-/blob/<sha>/` or `https://github.com/<org>/<repo>/blob/<sha>/`), run
   `python3 -I scripts/build_atlas.py manifest.json atlas.html`, syntax-check the page's scripts (`node --check` on the
   extracted `<script>` bodies), then publish following the host's artifact rules.
8. **Reply** with the link, the branch and SHA, the three or four widest-ripple symbols (each with its transitive
   caller count and the entry points it reaches), the graph's blind spots, and any doc-versus-code differences.

## Quick reference

| Need | Where |
|---|---|
| Box sizes, colours, layouts per diagram type | `references/drawing.md` |
| Archify spec, repair loop, gotchas | `references/archify-walkthrough.md` |
| Graph edge kinds | `call`, `ref` (partial, callbacks, wiring), `impl` (Protocol → implementation); dashed = ref or inferred |
| Ripple | transitive callers; "commands reached" = entry points among them |
| Blind spots to state | `getattr`, dynamic dispatch, wrapping decorators, untyped locals, coupling through shared tables |

## Common mistakes

| Mistake | Instead |
|---|---|
| Writing the diagrams into the doc the user linked for context | One new artifact; the linked doc stays as it was |
| Several artifacts or links | One page with tabs; archify is embedded, not linked |
| Archify walkthrough as a sequence diagram | Architecture + `meta.views` chapters, `animation: "trace"` |
| Resolving calls through imports only | `callgraph.py` follows `self.field.method`, typed chains, Protocol implementations |
| Trusting ripple numbers without the unreached check | Read the unreached list; fix misses on the main path |
| Diagramming the MR you were linked when a stacked MR is "the" version | Pin the head the reader means; name it in the subtitle |
| C4 at every level, runtime profiling, extra views | The five tabs above; add only what the ask names |
| Saying the walkthrough was browser-checked without Chrome | Report `visual-check` as skipped |

# Archify walkthrough

Load the `archify` skill for its full contract; this file covers what the walkthrough needs from it.

## Spec shape

`architecture`, schema 1, at most 12 components, `meta.quality_profile: "showcase"`, `meta.animation: "trace"`, and
`meta.views` as the chapters: up to 5, labelled in flow order ("1 Trigger", "2 Plan", …), each with a `focus` list of
component ids and a `note` of at most 140 characters saying what happens in that chapter. Add 3 `cards` summarising
the commands, what the system computes, and why retries are safe (or the equivalent for the subject).

Lay components on a grid with explicit `pos` and equal `size` (150 × 64): the main path on one row left to right,
collaborators directly above or below the node that calls them, stores at the bottom. Aligned nodes give straight
edges; diagonal pairs are where the validator's errors come from. Wrap the system's own components in one `region`
boundary.

## Gotchas

- Component `sources` need `meta.repository` on GitHub or Gitee; elsewhere, leave `sources` out.
- A relationship whose ends are diagonal from each other gets side and corridor errors. Move a node into line,
  remove an edge already implied by another, or, for a call to a far node, set `fromSide`/`toSide` with a `via` corridor
  that runs above or below the rows.
- Label overlap errors print a suggested `labelAt`; use it.
- `visual-check` needs Chrome (`ARCHIFY_CHROME`); without it the check is skipped, and you report it as skipped.
- Export buttons do not work inside an artifact viewer; point the reader to the local HTML for exports.

## Loop

Run from the archify skill's own directory (where its `bin/archify.mjs` lives):

```bash
node bin/archify.mjs validate architecture walk.json --quality showcase --json   # repeat until 9/9 checks, 0 errors
node bin/archify.mjs deliver architecture walk.json walk.html --quality showcase --json
```

Name `walk.html` as `archify_html` in the atlas manifest; the builder embeds it and loads it when its tab opens.

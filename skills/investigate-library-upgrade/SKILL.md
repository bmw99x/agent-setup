---
name: investigate-library-upgrade
description: Use when the user says "investigate updating <pkg> from X to Y", "investigate updating <pkg> to latest", "we are behind on <pkg>", or "what would it take to upgrade <pkg>". Produces a written migration assessment — version delta, breaking changes that apply to us, impacted call sites, transitive and security impact, suggested rollout — and stops. Does not perform the upgrade unless the user explicitly asks.
---

# Investigate a library upgrade

"Investigate" is deliberate. The output is a **written assessment**, not a code change. If the
user approves, exit this skill and do the upgrade as normal work (`worktree-flow`, `slicing` for a
staged rollout).

## Narration

One line per step: `[upgrade] step <n> — <what>`.

## Step 1: Pin down versions

Parse the package and target version (or "latest") from the arguments; ask if either is missing.
If the name is ambiguous (a rename such as `foo` → `@scope/foo`), ask rather than guess.

Read the **installed** version from the lockfile, not the manifest range:

| Ecosystem | Manifest | Lockfile | Latest |
|---|---|---|---|
| Python / uv | `pyproject.toml` | `uv.lock` | `uv tree --outdated --package <pkg>` or the PyPI JSON API |
| Node / pnpm | `package.json` | `pnpm-lock.yaml` | `pnpm view <pkg> version` |
| Rust | `Cargo.toml` | `Cargo.lock` | `cargo search <pkg> --limit 1` |
| Go | `go.mod` | `go.sum` | `go list -m -versions <pkg>` |

In a workspace or monorepo, check every member — list each distinct pinned version and who uses it.

## Step 2: Read the changelog between versions

Prefer, in order: upstream `CHANGELOG.md` between tags → GitHub/GitLab releases → registry pages.
For each intermediate release extract breaking changes (`BREAKING`, `!:`, major bumps),
deprecations, features relevant to our usage, and bug fixes that could silently change our
behaviour. Summarise chronologically so the path from X to Y is visible. Record releases with no
notes — they lower confidence.

## Step 3: Find every usage — down to the API

Search imports and direct references, then record **per file the specific APIs used**. The
blast-radius question is "which APIs changed AND which do we call", not "which files import it".
Prefer semantic symbol search (serena) over text grep when available.

## Step 4: Transitive and security impact

- **Dependency tree:** what the target version adds, removes, or bumps (`uv tree --package <pkg>`; `--invert` for who depends on it,
  `pnpm why <pkg>`, `cargo tree`, `go mod graph`). Note peer-dependency and Python/Node-version
  floor changes.
- **New transitive packages:** hand them to `license-audit`.
- **Advisories:** run the ecosystem audit (`pip-audit`, `pnpm audit`, `cargo audit`,
  `govulncheck`) on current vs target if available — an upgrade that clears a CVE changes its
  priority.

## Step 5: Classify each file–API pair

- **Safe** — no listed change touches it.
- **Needs change** — renamed, re-signatured, or default changed; the edit is mechanical.
- **Breaks** — removed, or semantics changed so that a design decision is needed.
- **Unclear** — can't be verified against the notes (undocumented internals, releases without
  notes).

When in doubt between safe and needs change → needs change. Between needs change and breaks →
breaks. Never invent a concern for an API the changelog doesn't mention — but if releases lacked
notes, say that undocumented changes are possible and lower confidence rather than calling
everything safe.

If usage is too widespread to classify site by site, say so, classify a representative sample per
API, and mark the rest as extrapolated.

## Step 6: Write the assessment — then stop

Print to the conversation; write a file only if asked.

```markdown
# Upgrade assessment: <pkg> <current> → <target>

## Version delta
- <N releases, K breaking>; highlights

## Breaking changes that affect us
- <change> — <n> call sites (table below)  |  "None apply to our current usage."

## Call sites needing edits
| File | APIs used | Category | What changes |

## Transitive & security
- added / removed / bumped deps; license-audit result; advisories cleared or introduced

## Unclear — needs human eyes
- <file:api> — why

## Blast radius
- <n> files to edit, <m> design decisions. Confidence: high|medium|low — why.

## Suggested rollout
- single change | staged (1: …, 2: …) | behind a feature flag — one-line rationale

## Next step
Reply "go ahead" to perform the upgrade, or ask for changes to the plan.
```

Do not edit files, bump versions, or open a PR/MR. A removed or downgraded dependency in the plan
is a `human-in-the-loop` gate — flag it in the rollout.

## Degradation

- **Can't fetch changelogs (offline):** do file-level analysis only, confidence low, list what
  couldn't be fetched.
- **No audit tool available:** say advisories weren't checked.

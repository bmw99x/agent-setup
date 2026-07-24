---
name: license-audit
description: Trigger this skill any time new package or dependency add or install — npm install, npm add, yarn add, pnpm add, uv add, poetry add, pip install, pipenv install, cargo add, go get, gem install, composer require, or any equivalent package-manager command, whether run direct or suggested as part of bigger task (setup project, add library to solve problem, follow tutorial). Also trigger when user ask to "audit licenses," "check for copyleft," "run license sweep," or ask if dependency safe to use. Use this skill BEFORE run install command, again AFTER, to check what pull in and flag anything with copyleft or non-permissive license (GPL, AGPL, LGPL, MPL, EPL, SSPL, etc.) before it become permanent part of codebase.
---

# License Audit

Ensure every new package added to project get license check before (ideal) or right after install, so copyleft or risky license don't sneak silent into codebase — especially matter for anyone under IP assignment, work-for-hire, or contractor agreement warranting no undisclosed copyleft/third-party code incorporated.

## When this fires

Any of these trigger workflow below:
- `npm install <pkg>`, `npm i <pkg>`, `npm add <pkg>`, `yarn add <pkg>`, `pnpm add <pkg>`
- `pip install <pkg>`, `pip3 install <pkg>`, `pipenv install <pkg>`
- `uv add <pkg>`, `poetry add <pkg>`
- `cargo add <pkg>`
- `go get <pkg>`
- `gem install <pkg>`, `bundle add <pkg>`
- `composer require <pkg>`
- Any request that *result* in one of above run (e.g. "add PDF library to this project")

Don't wait for user ask audit explicit — treat install itself as trigger.

## Workflow

### 1. Before installing (when practical)

If package name(s) known ahead of install, quick check first:
- Web search or check package registry page (npmjs.com, pypi.org, crates.io) for declared license.
- Flag immediate if copyleft family license (see table below) so user decide before it land in `package.json`/`pyproject.toml`/lockfiles.

This step nice-to-have, not blocker — don't stall install over it unless license clearly copyleft. Proceed to step 2 regardless.

### 2. Run the install

Run install command user asked for, normal.

### 3. After installing, sweep and report

Run scanner from `scripts/` matching ecosystem (see below), cover full dependency tree, not just direct package — transitive deps carry same risk, most common way copyleft code sneak in unnoticed.

Then report back concise:

- **New packages added this run** and their licenses.
- **Any copyleft or unknown/missing licenses** found anywhere in tree (not just top-level) — call out clear, don't bury.
- If clean (MIT/Apache-2.0/BSD/ISC/etc.), single-line confirm enough — don't pad into report nobody ask for.

Never silent install-and-move-on if copyleft license show up. Always surface before continue whatever user was doing.

### 4. If copyleft license found

Explain plain, sentence or two, why it matter for *this* use case:
- **GPL/LGPL**: matter mainly if package static linked/bundled into distributed proprietary software; less risky as build-time-only or dev-only dependency.
- **AGPL/SSPL**: matter even for server-side/SaaS use — network use count as "distribution." Treat high-severity regardless how package used.
- **MPL/EPL**: file-level copyleft — only modified files of library itself need stay open, not whole codebase. Lower severity, still worth flag.

Then ask if user want to:
- swap in permissively-licensed alternative,
- keep but document/disclose it (e.g. if contractual warranty about this, like IP assignment or employment agreement, note may need written disclosure to whoever own codebase), or
- proceed as-is, acknowledge risk.

Don't decide unilateral — flag it, let user decide, but don't let it pass unraised.

## Ecosystem scripts

Use `scripts/check_licenses.sh <ecosystem>` (auto-detect if no argument given) wraps:

| Ecosystem | Tool used | Install if missing |
|---|---|---|
| npm/yarn/pnpm | `license-checker` | `npx license-checker` (no install needed) |
| Python (pip/uv/poetry/pipenv) | `pip-licenses` | `pip install pip-licenses --break-system-packages` (sandboxed envs) or note user should install in their venv |
| Rust (cargo) | `cargo-license` | `cargo install cargo-license` |
| Go | `go-licenses` | `go install github.com/google/go-licenses@latest` |
| Ruby | `license_finder` | `gem install license_finder` |
| PHP (composer) | `composer licenses` | built into composer, no install needed |

If scanning tool unavailable, can't install in current env (e.g. no network access), fall back to manual check `license` field in `package.json`/`Cargo.toml`/PyPI page for each new package, say so — don't skip check silent.

## Copyleft license reference (flag these)

**High severity (flag loud):**
- GPL-2.0, GPL-3.0
- AGPL-3.0 (trigger even for SaaS/network use)
- SSPL (MongoDB's license — server-side trigger)

**Medium severity (flag, context-dependent):**
- LGPL-2.1, LGPL-3.0 (usually fine if dynamic linked, not bundled)
- MPL-2.0, EPL-1.0/2.0 (file-level copyleft only)
- CDDL

**Fine, no action needed:**
- MIT, Apache-2.0, BSD-2/3-Clause, ISC, Unlicense, 0BSD, Python-2.0

**Always flag regardless of category:**
- No license declared / "UNLICENSED" / license field missing — legal grey area (default copyright applies, meaning technically no reuse rights at all), treat higher-risk than even GPL until clarified.

## Notes on scope

- Check *whole* resolved dependency tree after install, not just package(s) just added — permissively-licensed package can still pull in copyleft transitive dependency.
- Skill about visibility, not gatekeeping — goal: nothing copyleft or unlicensed end up in codebase *without user knowing and making active choice*, not block installs outright.
- Keep report short. Clean sweep = one line. Only expand when something to actually flag.
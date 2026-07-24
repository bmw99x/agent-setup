---
name: license-audit
description: Trigger this skill any time a new package or dependency is being added or installed — npm install, npm add, yarn add, pnpm add, uv add, poetry add, pip install, pipenv install, cargo add, go get, gem install, composer require, or any equivalent package-manager command, whether run directly or suggested as part of a larger task (setting up a project, adding a library to solve a problem, following a tutorial). Also trigger when the user asks to "audit licenses," "check for copyleft," "run a license sweep," or asks whether a dependency is safe to use. Use this skill BEFORE running the install command and again AFTER, to check what's being pulled in and flag anything with a copyleft or otherwise non-permissive license (GPL, AGPL, LGPL, MPL, EPL, SSPL, etc.) before it becomes a permanent part of the codebase.
---

# License Audit

Ensures every new package added to a project gets its license checked before (ideally) or immediately after installation, so copyleft or otherwise risky licenses don't silently creep into a codebase — especially important for anyone under an IP assignment, work-for-hire, or contractor agreement warranting that no undisclosed copyleft/third-party code has been incorporated.

## When this fires

Any of these should trigger the workflow below:
- `npm install <pkg>`, `npm i <pkg>`, `npm add <pkg>`, `yarn add <pkg>`, `pnpm add <pkg>`
- `pip install <pkg>`, `pip3 install <pkg>`, `pipenv install <pkg>`
- `uv add <pkg>`, `poetry add <pkg>`
- `cargo add <pkg>`
- `go get <pkg>`
- `gem install <pkg>`, `bundle add <pkg>`
- `composer require <pkg>`
- Any request that will *result* in one of the above being run (e.g. "add a PDF library to this project")

Do not wait for the user to ask for an audit explicitly — treat the install itself as the trigger.

## Workflow

### 1. Before installing (when practical)

If you know the package name(s) ahead of the install, do a quick check first:
- Web search or check the package registry page (npmjs.com, pypi.org, crates.io) for the declared license.
- Flag immediately if it's a copyleft family license (see table below) so the user can decide before it's in `package.json`/`pyproject.toml`/lockfiles.

This step is a nice-to-have, not a blocker — don't stall the install over it unless the license is clearly copyleft. Proceed to step 2 regardless.

### 2. Run the install

Run the install command the user asked for as normal.

### 3. After installing, sweep and report

Run the appropriate scanner from `scripts/` for the ecosystem involved (see below), covering the full dependency tree, not just the direct package — transitive dependencies carry the same risk and are the most common way copyleft code sneaks in unnoticed.

Then report back concisely:

- **New packages added this run** and their licenses.
- **Any copyleft or unknown/missing licenses** found anywhere in the tree (not just top-level) — call these out clearly, don't bury them.
- If everything is clean (MIT/Apache-2.0/BSD/ISC/etc.), a single-line confirmation is enough — don't pad this out into a report nobody asked for.

Never silently install-and-move-on if a copyleft license shows up. Always surface it before continuing with whatever the user was doing.

### 4. If a copyleft license is found

Explain plainly, in a sentence or two, why it matters for *this* use case:
- **GPL/LGPL**: matters mainly if the package is statically linked/bundled into distributed proprietary software; less risky as a build-time-only or dev-only dependency.
- **AGPL/SSPL**: matters even for server-side/SaaS use — network use counts as "distribution." Treat as high-severity regardless of how the package is used.
- **MPL/EPL**: file-level copyleft — only the modified files of the library itself need to stay open, not the whole codebase. Lower severity but still worth flagging.

Then ask whether the user wants to:
- swap in a permissively-licensed alternative,
- keep it but document/disclose it (e.g. if there's a contractual warranty about this, like an IP assignment or employment agreement, note that this may need written disclosure to whoever owns the codebase), or
- proceed as-is, acknowledging the risk.

Don't make this decision unilaterally — flag it and let the user decide, but don't let it pass without being raised.

## Ecosystem scripts

Use `scripts/check_licenses.sh <ecosystem>` (auto-detects if no argument given) which wraps:

| Ecosystem | Tool used | Install if missing |
|---|---|---|
| npm/yarn/pnpm | `license-checker` | `npx license-checker` (no install needed) |
| Python (pip/uv/poetry/pipenv) | `pip-licenses` | `pip install pip-licenses --break-system-packages` (sandboxed envs) or note the user should install it in their venv |
| Rust (cargo) | `cargo-license` | `cargo install cargo-license` |
| Go | `go-licenses` | `go install github.com/google/go-licenses@latest` |
| Ruby | `license_finder` | `gem install license_finder` |
| PHP (composer) | `composer licenses` | built into composer, no install needed |

If a scanning tool isn't available and can't be installed in the current environment (e.g. no network access to install it), fall back to manually checking the `license` field in `package.json`/`Cargo.toml`/the PyPI page for each new package, and say so — don't skip the check silently.

## Copyleft license reference (flag these)

**High severity (flag loudly):**
- GPL-2.0, GPL-3.0
- AGPL-3.0 (triggers even for SaaS/network use)
- SSPL (MongoDB's license — server-side triggers)

**Medium severity (flag, context-dependent):**
- LGPL-2.1, LGPL-3.0 (usually fine if dynamically linked, not bundled)
- MPL-2.0, EPL-1.0/2.0 (file-level copyleft only)
- CDDL

**Fine, no action needed:**
- MIT, Apache-2.0, BSD-2/3-Clause, ISC, Unlicense, 0BSD, Python-2.0

**Always flag regardless of category:**
- No license declared / "UNLICENSED" / license field missing — this is a legal grey area (default copyright applies, meaning technically no reuse rights at all) and should be treated as higher-risk than even GPL until clarified.

## Notes on scope

- Check the *whole* resolved dependency tree after install, not just the package(s) just added — a permissively-licensed package can still pull in a copyleft transitive dependency.
- This skill is about visibility, not gatekeeping — the goal is that nothing copyleft or unlicensed ends up in a codebase *without the user knowing about it and making an active choice*, not blocking installs outright.
- Keep the report short. A clean sweep should be one line. Only expand when there's something to actually flag.

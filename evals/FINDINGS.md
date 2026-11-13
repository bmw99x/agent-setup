# Skill findings from eval authoring

Raw log: contradictions, factual errors and cross-skill conflicts found while writing tasks, plus paid-run evidence. Each section names the tasks covering that skill. To be turned into skill edits after the paid runs.

## alembic (tasks: alembic-required-column, -rename-column, -updated-at-trigger; oracle 3/3, noop 0/3)
- DEFAULT NULL+backfill rule justified by pre-PG11 rewrite; PG11+ constant default metadata-only -> rule outdated; test 1 enforces as written
- not-null expand/contract: later statement vs later deploy unspecified
- rename: drop timing optional; no guidance on dual-write sync
- backfill chunking "LIMIT/OFFSET" wrong (UPDATE no LIMIT, OFFSET quadratic)
- verb_noun_to_table contradicts own examples
- missing register_entities for alembic-utils autogenerate
- project-specific "alembic/ at repo root"
## code-hygiene (tasks: code-hygiene-renderer-export, -money-split, -upload-limits; oracle 3/3, noop 0/3, naive 0/3)
- timeout per-env vs single-use overlap
- "exported function in utils" undefined
- owning module list vs existing home
- docstring one-line vs <=3 more lines wording
- unused-import deletion lacks re-export carve-out
- constants table vs common-mistakes row precedence
## dtos-and-adapters (tasks: -carrier-quote, -report-criteria, -billing-tidy; oracle 3/3, noop 0/3, naive fails conventions)
- "never next to logic" vs "tiny single-use DTO beside user" vs "single class still gets named file"
- adapter scope: wraps client call or mapping only? example contradicts
- DTO vs domain model (models.py exemption) boundary unclear
- no home for Protocols/gateways
## production-python-style (tasks: py-style-shipping-quote, -settlement-job, -pagination; oracle 3/3, noop 0/3, naive 0/3)
- rule 1: 3 thresholds (no bare *, couple params, ~4 -> param object)
- rule 10 inline one-liners vs rules 6/7/15 named steps; own example violates
- rule 17: domain error subclass ValueError? unstated; "one base per package" untestable w/ one error
- rule 3 "most of module" no threshold; private constants?
- rule 9 self-redundant wording
- rule 13 never getLogger needs scoping to non-logging modules
- rule 2 defers to code-hygiene for single-use literals (cross-skill dependency)
## python-testing (tasks: py-testing-order-pricing, -order-settlement, -article-api; oracle 3/3, noop 0/3; mutant-killing verifiers)
- docstrings "prefer"/"if project requires" yet verifier requires on every test (debatable check)
- GIVEN/WHEN/THEN example punctuation inconsistent
- markers on every test not stated
- marker registration (--strict-markers) unmentioned; pyproject registration hints baseline
- "avoid mocking globals" scope unclear (monkeypatch?)
- SpyHandler Protocol rule ungradable
- separator rule applies to production files (out of scope)
## advanced-alchemy (tasks: -invoice-line-model, -invoice-service, -import-job-failures; oracle 3/3, noop 0/3)
- lazy="raise" rule vs examples using lazy="selectin"
- no hard delete vs ImportJobError ondelete=CASCADE w/o soft delete
- BasicAttributes described as adding __tablename__; in AA 1.12 only to_dict() (factual error)
- SoftDelete*MixIn are house code (myapp.orm.mixins), not marked; in generic skill agents must invent
- custom repo methods skip deleted_at filter; no rule says add manually
- JSONB GIN index named ix_ here vs gix_ in db-indexes (cross-skill conflict)
## io-and-caching-at-the-boundary (tasks: io-caching-fx-rates, -overdue-report, -loyalty-job; oracle 3/3, noop 0/3, naive 0/3)
- "never `if key in cache`" vs endorsed hand-written caching wrapper
- module-level memo banned vs example @functools.cache on module read_orders (no lifetime/invalidation guidance; functools.cache on methods)
- example run_import uses module-global repository vs injection rule
- "and" test subjective
- verifier caveats: tasks 1/3 hinge on AST heuristic; task 2 fails config-object param bundling
## python-module-structure (tasks: py-modules-split-services, -reschedule-delivery, -supplier-routes; oracle 3/3, noop 0/3)
- rule 5 delete tiny files vs rule 3 exceptions.py even for one exception
- rule 4 "real exports" undefined (back-compat re-export __init__)
- rule 3 which package's exceptions.py after split
- rule 7 extract autonomously vs flag & ask
- rule 2 flag vs constant indistinguishable
- billing_columns.py vs invoice_columns.py naming drift
- audit grep flags test-file exceptions
## design-patterns-pragmatic (tasks: patterns-weekend-surcharge [restraint], -reminders-dry-run, -duplicate-customer-email; oracle 3/3, noop 0/3, naive 0/3)
- repo Protocol (rule 2) vs "wait for second call site"
- rule 4 cache class own file vs wait-for-second
- "mode nobody wired raises" unclear
- rule 5 helper names: required or examples?
- exceptions.py level unspecified (also python-module-structure)
- strategy threshold "two kinds" = second call site? implicit
- description triggers on "because" temptation; body has no section
## testing (tasks: testing-login-lockout, -billing-statement, -catalog-import; oracle 3/3, noop 0/3, naive 0/3)
- "imports at top" only in Red Flags -> unclear if mandatory (removed from verifier)
- red flag "test fails when you remove mock" contradicts anti-pattern 3 fix
- "tests as afterthought -> TDD" conflicts with "add tests for X" requests
- thresholds (>50% mock setup) undefined
- no criterion to tell test-only method from legit API
- examples all TypeScript/Vitest; overlaps python-testing
## solid-principles (tasks: solid-duplicate-registration, -booking-cancellation, -tenant-order-stats; oracle 3/3, noop 0/3)
- rule 6/8: is SQLAlchemy Session a "driver connection"?
- rule 3: service vs repository translates — unspecified
- audit grep narrower than rule 3 (misses NoResultFound)
- rule 2 (routes only parse/call/shape) vs rule 4 (caller resolves tenant)
- "no if forests" no threshold; proxy rule vague; clock not in rule 4 list
- OVERLAP: solid-duplicate-registration ~= patterns-duplicate-customer-email (same DB error->domain error rule in two skills; consider single owner)
## empirical-type-probe (tasks: type-probe-sender-variance, -exporter-registry, -retry-decorator; oracle 3/3, noop 0/3, naive 0/3)
- process skill; verifier grades resulting design not probe usage
- probe file lifecycle: delete after? unstated
- "project's real checker" vs examples using ty (mypy and ty disagree on Awaitable decorator conformance)
- expect strong baseline on sender-variance
## safe-rename (tasks: safe-rename-sandbox-mode, -finish-partial, -reminder-task; oracle 3/3, noop 0/3, naive sed + \b sed 0/6)
- symbol-aware tool preferred, but it won't rename test_mode_* test names -> conflicts with no-stragglers grep
- straggler grep has no exclusion rule for unrelated names containing old name
- process-boundary rule: 3 options, unclear vs user's requested rename; "keep entrypoint" leaves straggler
- collection count "explainable change" vague
## refactor-variable-explosion (tasks: var-explosion-order-filters, -report-period, -job-spec; oracle 3/3, noop 0/3)
- frozen=True vs field(default_factory=list) (shallow-frozen, unhashable; tuple?)
- step 7 mutable defaults barely fails with dataclasses
- derivation fn location unspecified
- "done" signals (1-2 params, unit tests) mandatory?
- **kwargs escape hatch swallows typos
- NamedTuple allowed but can't __post_init__ (conflicts step 3)
- overlap with dtos-and-adapters param objects
- VERIFIER CAVEAT: fields located by substring of original names; renamed/nested fields fail
## conventions (tasks: conventions-returns-context, -refund-notifications, -invoice-reject [React/vitest]; oracle 3/3, noop 0/3, naive 0/3)
- "adapt naming to existing patterns" — does it extend to placement/auth? (task treats as absolute)
- router-level auth vs handler needing user object
- handler Protocol: concrete location / optional defaults unstated
- isCreating (drops noun) vs is+participle rule ambiguity
- "apply to every mutation in codebase" = scope creep vs other skills (graded; most disputable test)
- error-audit row misplaced in Naming table; env section dup of pydantic
- CONFLICT pydantic: ProductUpsertDatum vs conventions UpsertProductDatum
- CONFLICT advanced-alchemy: created_at as failed_at vs conventions failed_at column
- code-hygiene single-file enum may stay vs conventions never in models.py
## python-reviewer (tasks: py-review-order-history, -supplier-contacts, -invoice-approval; oracle 3/3, noop 0/3, naive 0/3; gate-call logging)
- soft-delete rule only covers out-of-repo queries already forbidden by §3; in-repo filtering unstated
- gates "fix root cause" clashes with review-only role; assumes uv + pytest-xdist; branch vs merge result
- checklist must vs prefer unmarked
- raw SQL: interpolated only vs advanced-alchemy forbids all raw SQL (conflict)
- §4 async helper wording loophole
- §11 real DB tests vs §4 fake-repo purity
## worktree-flow (tasks: worktree-dirty-feature, -unstacked-followup, -bugfix-from-default; oracle 3/3, noop 0/3, naive 0/3)
- "never nest" conflicts with Claude Code EnterWorktree (.claude/worktrees/) and superpowers using-git-worktrees (.worktrees/)
- cleanup timing unspecified (verifier loosened)
- default branch local vs origin/main
- slug vs branch naming; "short" undefined
- "approved foundation" vs "no dependency on unmerged"
- strict one-at-a-time for auth/PII: meaning for worktrees?
- DUPLICATION: topology section ~= slicing; local-stack rule in 3 skills; secrets rule repeats commit-flow; remote-stack approval gate only in commit-flow
## license-audit (tasks: license-audit-article-slugs [GPL transitive], -comment-markdown [no-license], -dashboard-sparkline [npm AGPL]; oracle 3/3, noop 0/3, naive 0/3)
- pause vs finish ("surface before continuing"/"don't decide unilaterally" vs "visibility not gatekeeping") — verifier accepts both
- description says check BEFORE+AFTER; body says pre-check nice-to-have
- SCRIPT BUG: npm `license-checker --summary` prints counts only, no names
- SCRIPT BUG: flags project's own UNLICENSED package.json (npm private marker)
- SCRIPT BUG: "GPL-3.0" substring matches LGPL-3.0 -> LGPL reported high severity
- SCRIPT BUG: misses classifier-form "GNU General Public License v3 (GPLv3)"
- SCRIPT BUG: uses PATH python, misses project .venv (uv/poetry)
- SCRIPT BUG: newer packaging license-expression fields show UNKNOWN -> false "missing"
- installs pip-licenses with --break-system-packages (needs network)
- verifier gap: `python -m piplicenses` not logged
## slicing (tasks: slicing-order-returns, -account-backlog, -shipped-notification-channels; oracle 3/3, noop 0/3, 8 naive plans fail as designed)
- "strict one-at-a-time" undefined (chain? clashes w/ no stacked chain) — also in worktree-flow
- "too small: repeatedly edits same service/route" clashes with vertical fan-out
- foundation threshold escape hatch ("unless explicit foundation")
- bundling behaviour into foundation not explicitly banned
- size budget 3-8 files lower bound odd
- route skeleton in foundation vs no fake stubs
- test requirement not clearly mandatory
- feature flag "ask user" impossible headless
- DUPLICATION with worktree-flow topology, spec-kit, sdd (foundation/flag rules repeated); no slice output format defined anywhere
## vercel-react-best-practices (tasks: react-perf-dashboard-loader, -orders-bundle [esbuild metafile], -task-rerenders [render counts]; oracle 3/3, noop 0/3, naive 0/3)
- rule 1.2 defer-await vs 1.3/1.5 start-early tension
- 1.3 recommends adding better-all dep (offline; triggers license-audit)
- BROKEN LINKS: waterfalls.md -> async-defer-await.md, async-cheap-condition-before-await.md missing; rule numbers 1.4, 2.3, 8.1 gaps
- Next.js leftovers in SPA-scoped skill (optimizePackageImports, typeof window, useSearchParams)
- rule 5.5 technically wrong (default props don't break memo)
- React Compiler caveats
- CONFLICT: pushes SWR vs React Query used by frontend-testing/conventions
## spec-drift (tasks: spec-drift-cursor-pagination, -lockout-ticket [fake tracker/wiki, unauthorised], -order-states-diagram [graphviz, authorised]; oracle 3/3, noop 0/3, code-only naive 0/3)
- "retain superseded section" vs "every artefact updated" for diagrams/tables/ACs
- no ADR creation rule, only amend
- "flag tracker/wiki edits" — does a comment count?
- description pushes fixing tickets vs body requires agreement first
- ungradable: look at regenerated images, banner wording
## mantine (tasks: mantine-plan-picker, -order-summary-dark-mode, -invite-teammate; oracle 3/3, noop 0/3, naive 0/3; TS compiler API lint)
- FACTUAL: createStyles "removed in v8" — actually v7
- style-props.md at skill root, not references/
- "never style={{}}" no route for runtime values (vars/__vars)
- ladder silent on styles={{root}} objects
- fractional-values rule vs Mantine px->rem conversion; opacity
- mixed CSS classes unaddressed
- rung 1 (Card/Paper) vs rung 2 (bd/bdrs/p on Box)
- theme.colors.blue[5] example hardcodes shade vs "never hardcode"
- CONFLICT: vercel-react re-renders 5.14/5.15 recommend inline style={{}}
## frontend-testing (tasks: fe-testing-orders-page, -product-search, -refund-form; oracle 3/3, noop 0/3, naive 0/3; mutant-killing + TS lint)
- "role-first selection" advertised but absent from queries.md
- expect(getBy).toBeTruthy "preferred" (queries.md) vs anti-pattern (conventions.md)
- "prefer real hooks+MSW" soft in principle, hard in tables (GRADED as mandatory — disputable)
- FACTUAL: shouldAdvanceTime "does NOT work" — works on vitest 2.1.5/msw 2.6.5/RTL16; "never fake timers in beforeEach" penalises working suites
- pool:"forks" "critical" but already vitest 2+ default
- MISSING STUB: Element.prototype.scrollIntoView for Mantine 8 Select
- CONFLICT: testing skill allows vi.mock "at correct level" vs no data-hook mocks
## investigate-library-upgrade (tasks: lib-upgrade-http-client-major, -monorepo-services, -renderer-latest; oracle 3/3, noop 0/3, naive 0/3)
- "print to conversation; file only if asked" vs "do not edit files"
- template call-site table lacks line numbers
- "removed dependency = HITL gate": manifest vs resolved tree (shakiest test)
- Unclear vs Breaks overlap for internals
- "check every member" assumes multi-lock; uv workspace has one lock; no rule to flag user's X vs lockfile mismatch
- resolving "latest" offline undefined
## PAID EVIDENCE alembic (batch1): base 2/9, skill 2/9, discover 1/9 -> no lift
- required-column: all 9 runs incl. skill arm wrote server_default='GBP' NOT NULL, citing PG11+ metadata-only -> model overrides outdated skill rule (correctly). Verifier loosened to accept both paths; RERUN alembic.
- revision message check rejected "add currency to orders" (spaces) -> normalised; RERUN.
## session-housekeeping (tasks: housekeeping-quote-cache, -search-supersede, -invoice-export; oracle 3/3, noop 0/3)
- keep/delete earlier brief unstated (inferred keep)
- Settled-by vocabulary fuzzy; "time (= parked)" vs status "parked"
- word-count rule ambiguous re markdown symbols; "ranks nothing" undefined
- UNTESTABLE headless: transcript recovery from ~/.claude/projects, cold-read subagent, Artifact publish, final report
- RISK: Claude Code may guard writes under project .claude/ -> watch first paid run.log
- location rule (.claude/housekeeping) dominates baseline failures
## ben-pair (tasks: ben-pair-shipping-zone [just-do], -registration-naming [recommend-ask], -daily-revenue [refactor beat]; oracle 3/3, noop 0/3, 5 naive 0/5)
- worked-examples "illustrations, not laws" vs ladder citing them as just-dos (graded mandatory)
- "improve what you touch" vs three strikes on untouched copies
- rename guardrail "recommend" vs HITL gates = stop-and-ask (bare question)
- "don't extract short & clear" vs three strikes — no tie-break
- stop-ask vs recommend-ask overlap
- CONFLICT human-in-the-loop: "multiple valid paths" hard gate (stop) vs ben-pair recommend-ask; HITL prefers closed question w/ recommendation even at hard gate vs ben-pair bare question; HITL "never assume scope expansion" vs ben-pair just-do improvements; DB column type vs rename triggers; question location (# QUESTION comments+MR vs mention in passing)
- verifier: recommendation marker regex is wording-based
## session-handoff (tasks: handoff-save-stopping, -resume-next-step, -stale-state; oracle 3/3, noop 0/3, naive 0/3)
- MISSING TOOLING: "Generate Scaffold", validation, secret detection, "Quality score >=70" referenced but no scripts/ dir
- no "trust repo over handoff" rule; red flags "pause and verify" vs "escalate"
- update vs chain handoffs
- "required sections" undefined; Handoff Chain section absent from template
- timestamp timezone unspecified
- progress-recorded check may be soft (drop if not mandatory)
## session-meditate (tasks: meditate-invoice-rounding, -partial-refunds, -orders-report; oracle 3/3, noop 0/3, naive 0/3)
- "every claim cites a moment" vs SOLID/coding guidance sections inviting generic content
- Hard NOs "Table" vs "table or bullet list"
- §5 "ranked" unverifiable with one candidate
- no explicit "don't edit memory/existing skills" rule (implied)
- assumes visible conversation; headless needs transcript file
- NOTE: task fixtures include .claude/skills/*.md that Claude Code surfaces as available skills when working in evals/ (payments-api, reporting) — harmless but noisy
## creating-merge-requests (tasks: mr-ticket-search, mr-order-events-diagram, mr-develop-default-branch; oracle 3/3, noop 0/3, naive 0/3; fake glab/gh/tracker)
- promises references/ + "gathering diagrams" — none exist
- title scope required vs commit-flow optional
- which sections mandatory unclear
- "no AI attribution in commits" implies history rewrite — unaddressed
- FACTUAL: `glab mr create --description-file` not a real glab flag (example fails)
- status names deferred to absent "tracker skill"
- CONFLICT commit-flow: body wants risks/decisions (MR template lacks); attribution "unless required" vs never; stacked branch handling
## human-in-the-loop (tasks: hitl-drop-legacy-column, -vat-backfill [fake psql-prod], -export-red-suite; oracle 3/3, noop 0/3, naive 0/3)
- "two interpretations" hard gate vs soft-checkpoint example (404 vs empty list) is exactly that
- gate vs explicit user request precedence unstated (vat-backfill most debatable)
- no decision-log location for headless/no-PR runs
- continue safe work after stop? unstated
- "rotate leaked secret first, then ask" = irreversible outward action without approval vs "never assume destructive"
- "contract changes: endpoint" catches requested endpoints; no gate for deploy/prod env
- CONFLICT ben-pair: removing dead code just-do vs HITL delete field gate; multiple valid paths = 3 different levels across skills
## xp-reviewer (tasks: xp-review-return-labels, -membership-freeze, -occupancy-export; oracle 3/3, noop 0/3)
- must-fix vs consider unclear for YAGNI/scope creep
- "call out what's done well" vs bullet format
- three strikes vs "duplicated code" flag — second copy silent or mention?
- "pick 3-5" soft (cap check removed)
- "a section needing a comment wants a method" vs "keep why-comments" conflation risk
- OVERLAP python-reviewer: naming §7 vs domain drift; §4 vs feature envy; formatter "don't flag" vs ruff format --check blocking; no run order for "don't repeat stack reviewer finding"
- expected redundant: YAGNI, scope creep, long method, wrong abstraction
## spec-kit (tasks: spec-kit-reservations-spec, -overdue-reminders-plan, -late-fees-implement; oracle 3/3, noop 0/3, naive 0/3; real specify-generated scaffolding)
- no references/
- Phase 3 double gate (plan approval then slicing then wait); slicing output location undefined
- Phases 6/7 lack explicit wait
- no durable approval-record format
- clarify/analyze mandatory here, optional upstream
- feature-flag "ask user" no headless fallback
- test-first not in SKILL.md (only via constitution/templates) — failing-first check measures task-following
- Phase 10 ticket "review status" vs user's ClickUp rule (in code review first)
- CONFLICT sdd: flag default OFF even after approval vs spec-kit/slicing "unless approved"; phase numbering; reviewer naming
- NOTE: --setting-sources "" means repo .claude/skills/speckit-* not surfaced via Skill tool
## claude-mem: NO TASKS (infeasible in dokimi sandbox: needs MCP mcp-search + plugin hooks + ~/.claude-mem DB; all stripped)
- needs: dokimi per-task MCP config, seedable state outside /app, plugin loading
- table mixes slash commands & skills; never says search tools are MCP (search->timeline->get_observations)
- "record decisions as observations" no write path; conflicts w/ "team facts in repo"
- /weekly-digests possibly nonexistent (unconfirmed)
- omits upstream mem-search's "ALWAYS filter index before fetching" rule
## visuals-for-understanding (tasks: visuals-loyalty-blast-radius, -payouts-stacked-mr, -meter-ingest-atlas; oracle 3/3 using real callgraph.py/build_atlas.py incl user's uncommitted changes; noop 0/3, naive 0/3)
- "drop a tab only when ask excludes it" — which asks exclude?
- stacked MR: which head?
- "widest-ripple symbols" vs single-function ask
- publishing assumes Artifact tool
- overlap graphify (inline mermaid) — discover arm may route there; archify walkthrough not installable
- verifier caveat: SVG y-order parsing fragile w/ transform-only placement
## ci-shepherd (tasks: ci-shepherd-lint-and-flaky, -base-broke-ci [gh], -needs-rebase; oracle 3/3, noop 0/3, naive 0/3; fake glab/gh, push hook, blob-hash gate logs)
- rerun flaky after repair push (push already reruns) — verifier loosened to <=1
- "repair at most once" vs "keep diagnosing" unbounded
- "standalone" undefined (ask vs report)
- <old_base> undefined in step 3.6
- forge.md merge-state table: BLOCKED also failing checks; UNSTABLE/ci_must_pass listed "Fine" (WRONG)
- no command for base-branch pipeline
- rerun count semantics
- CONFLICT commit-flow: history rewrite allowed w/ approval vs forbidden; merge-commit citation misapplied; test-scope rules disagree
## graphify (tasks: graphify-order-placement-flow, -loyalty-package [hidden autodiscover coupling], -vat-callers; oracle 3/3, noop 0/3, naive 0/3; mermaid parser)
- no references/
- "no edits" vs pre-refactor step; map written down for change requests?
- "save under docs/diagrams/explore/" vs "no edits"
- "always diagram" vs "trivial 2-file narrative only"
- "outward sweep 1-2 hops" vs runtime dispatch (real paths 3-5 hops)
- layer list lacks subscribers/jobs/CLI
- "?" mark placement unspecified
- Tools: recommends Explore subagent + Claude LSP; ignores serena (global CLAUDE.md prefers)
- OVERLAP visuals-for-understanding: both trigger on "how does X work"/call graph/blast radius; graphify lacks yield clause
## parallel-mr-feedback (eval via skill-variants/ copy w/o hooks; tasks: mr-feedback-gitlab-threads, -github-declined, -stacked-branch; oracle 3/3, noop 0/3, naive 0/3)
- UNTESTABLE: steps 2-6, 10 (subagents/worktrees) — no Agent tool in sandbox
- GitLab filter drops plain MR comments; GitHub query skips PR conversation & review summaries
- FACTUAL: GitHub `line` is current head (null when outdated); originalLine = reviewed commit — skill claims otherwise
- Stop hook expects "Proposed skill updates" heading / "-" separators / "repo-specific"; SKILL.md says no heading, "—", "repo-specific convention" — hook nags correct runs
- step 8: push someone's stacked MR without asking? (graded mandatory; 4 tests droppable)
- interactive steps assume user present
## sentry-cli (tasks: sentry-checkout-prod-errors, sentry-noisiest-issue, sentry-resolve-in-release; oracle 3/3, noop 0/3, naive fail; fake `sentry` from references spec, 64 cmds)
- NAME MISMATCH: skill named sentry-cli but documents new `sentry` binary (cli.sentry.dev), not legacy Rust sentry-cli; will mis-trigger for legacy users
- short IDs rule vs numeric-ID examples
- "prefer CLI over api" soft vs listed mistake
- flag letters inconsistent (-q/-n/-f/-t/--verbose), contradicts "gh conventions transfer"
- safety confirmation only for project delete/trial start; release delete, merge, api -X DELETE uncovered (api.md shows DELETE w/o warning)
- auth "prompts interactively" vs exit-code table; non-interactive shells
- issue list default query unstated
- broken link /exit-codes/
- MISLEADING: "resolve immediately (no regression tracking)" — plain resolve still regresses
- task 1 distinctive checks likely redundant (process rules)
## lore-generate (tasks: lore-fulfilment-direction [glab], -billing-hypothesis [gh], -rota-existing-skill; oracle 3/3, noop 0/3, naive 0/3)
- CONTRADICTION: description "offers global takeaways" vs step 8 "edit matching global skill" (outside-repo check removed)
- precedence: user below lead reviewer vs step 6 user ruling overrides
- "older comment vs newer global rule" needs dated global rules
- glossary filename unspecified; existing local skills handling unspecified
- <repo> in path undefined; mantra "two clauses" vague; tag granularity
- gate timing; no references/; "written from one run, not pressure-tested" (self-declared)

## PAID EVIDENCE batch 1 (sonnet, 3 repeats; base / skill / discover)
- advanced-alchemy 6/9 7/9 7/9 — import-job-failures redundant (9/9 all arms)
- alembic 2/9 2/9 1/9 — model overrides outdated DEFAULT NULL rule; verifier loosened; re-queued
- code-hygiene 3/9 9/9 9/9
- dtos-and-adapters 0/9 9/9 9/9
- io-and-caching-at-the-boundary 5/9 9/9 9/9
- production-python-style 0/9 ERR ERR — invalid frontmatter YAML (fixed: quoted description); re-queued
- python-module-structure 0/9 9/9 9/9
- python-testing 0/9 9/9 9/9 — CAVEAT: base fails pricing+settlement ONLY on GIVEN/WHEN/THEN docstring check (skill says "prefer"); without it base ~6/9
- pilot: pydantic 0/9 7/9 6/9; db-indexes 3/9 9/9 9/9 (CONCURRENTLY redundant); commit-flow 0/9 0/9 0/9 (Co-Authored-By trailer beats skill)

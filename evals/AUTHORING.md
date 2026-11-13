# Authoring eval tasks

Brief for whoever writes tasks under `evals/tasks/` (human or agent). Read `README.md` first.

## Goal

Each task measures whether a skill changes what Claude Code actually does. Three arms run it: no skill, skill loaded, and skill installed but not mentioned. A good task is one the **no-skill arm tends to fail and the skill arm passes**, because of a rule the skill states. A task every arm passes measures nothing. Keep it only if it guards a rule the model already follows (the "redundant" signal, which suggests trimming that part of the skill).

## Per skill: 3 tasks

- Read the skill's `SKILL.md` and its `references/`. List the rules that are **specific or non-default**: naming, house conventions, gotchas, ordering, things a strong model would do differently without being told. Skip generic advice the model already follows.
- Pick 3 tasks that together cover the most distinctive rules. Name them `<skill>-<short-scenario>`, e.g. `alembic-rename-column`.
- Each task is a realistic request a user would type. **The instruction must never name or hint at the convention under test.** "Add an index for customer lookups", not "add an `ix_`-prefixed index".
- The instruction may give context a real user would give: prod scale, a soft-delete column, "the team uses this from their editor".

## Layout (Harbor format; copy `tasks/pydantic-product-schemas/` as a template)

```
tasks/<task>/
  task.toml            # metadata.skill = "<skill dir name>"; keep the other tables as in the template
  instruction.md       # the prompt
  environment/
    Dockerfile         # FROM python:3.12-slim (or node:22-slim for frontend); deps installed at build; COPY app/ /app/; WORKDIR /app
    app/               # the repo the agent works in, as /app
  tests/
    test.sh            # copy from the template unchanged (pytest over /tests, writes /logs/verifier/reward.txt)
    test_*.py          # the verifier
  solution/solve.sh    # reference solution (bash, chmod +x); edits /app
```

Hard constraints:

- The agent works only in `/app`. Its WORKDIR must be `/app` or below.
- **No network at solve or verify time.** Install every dependency at image build, including pytest and anything the verifier needs. Git config, if git is used: `git config --system user.name/user.email`, `safe.directory '*'`, `init.defaultBranch main`.
- The verifier runs as root after the agent exits, with `/tests` mounted. Use absolute `/app` paths and `sys.path.insert(0, "/app")`.
- If a task needs an external CLI (`gh`, `glab`, `sentry-cli`, ...), put a **fake** script on PATH in the image. It returns canned JSON and logs its invocations to a file the verifier reads.
- For tasks whose output is judgement (a review, a plan, a report), the instruction asks for it in a file, e.g. "write your review to `/app/REVIEW.md`". The verifier checks concrete, objectively gradable content in it: a named file and line, a specific defect, a required section. **Never** grade on vague wording.
- For "should the agent stop and ask" behaviour, check the state of `/app`. The dangerous thing must not have happened, and the agent leaves a note file if the instruction says to.

## Verifier quality

- Each test function checks **one** rule. Name it after the rule, e.g. `test_unique_index_ignores_soft_deleted_rows`.
- Prefer behaviour over grepping: import and call the code, render the SQL (`alembic upgrade --sql`, SQLAlchemy `compile`), run the project's tests, inspect git objects. Use a source grep only when the rule is literally about source text (e.g. no `Optional[`). Then check what is forbidden, not one exact spelling of what is allowed.
- **Don't over-fit.** Accept every reasonable implementation that satisfies the rule. Earlier lesson: a check for the exact call `find_dotenv(".env")` failed agents that used `Path(__file__).parents[2] / ".env"`, which is equally correct. If the skill says X and the model achieves the same outcome via Y, test the outcome.
- Grade only rules the skill states as mandatory. A "prefer" or "if the project requires" rule goes in the report, not in a failing test.
- When the skill contradicts itself or another skill, accept every reading and report the contradiction.
- To check that tests the agent writes actually test something, copy the pristine code from a baked-in `/opt/base`, run the agent's tests against it (they must pass), then against planted mutants (they must fail).
- Pin library versions when the verifier introspects library internals. Example: FastAPI 0.162 changed how included routers are stored.
- Guard against cheating paths. Example: a git hook appends `git write-tree` to `.git/hook-trees` only after it succeeds, so `--no-verify` is detectable. Store baseline facts in a root-owned file such as `/etc/eval-base-sha`.
- The agent runs as uid 10001, but the oracle runs as root. Anything the agent must write outside `/app`, such as fake-CLI logs or state, or a bare git remote under `/srv/git`, must be world-writable (`chmod -R a+rwX`). Otherwise the oracle passes and every agent fails. Check by running `solve.sh` under `setpriv --reuid=10001`.
- Gotcha: `python -c` makes python-dotenv treat the run as interactive. Run a script file in subprocess tests.

## Validate before reporting (required)

From `~/Development/agent-setup/evals`:

```bash
# 1. Oracle must pass (reward 1):
dokimi tasks run --tasks-root tasks --tasks <t1>,<t2>,<t3> --harnesses docker-oracle --out results/oracle-<skill>.json
# 2. Untouched repo must fail (reward 0):
for t in <t1> <t2> <t3>; do docker build -q -t evalneg-$t tasks/$t/environment >/dev/null && \
  docker run --rm -v $PWD/tasks/$t/tests:/tests:ro evalneg-$t bash -c 'bash /tests/test.sh >/dev/null 2>&1; cat /logs/verifier/reward.txt'; done
```

When the oracle fails, read `results/task-runs/<task>/docker-oracle/run.log`.

Also sanity-check that a plausible **naive** solution, the one a model without the skill would write, fails the distinctive checks and passes the generic ones. This is a thought exercise, or a second throwaway solve script. Don't commit it.

**Do not** run the paid arms (`run.sh`, `docker-claude*`). Do not commit. Do not touch `skills/` or other skills' tasks.

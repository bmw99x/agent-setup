# Skill evals

Agentic evals for the skills in `../skills/`, run with [dokimi](https://github.com/intel/dokimi). Each task is a small repo in a Docker image plus a pytest verifier. Real Claude Code solves it in three arms, and the pass rates are compared:

| Arm | Skill installed | Told to load it | Measures |
|---|:-:|:-:|---|
| `docker-claude` | no | no | baseline: what the model does unaided |
| `docker-claude-skill:<skill>` | yes | yes | the skill's content, given it is loaded |
| `docker-claude-skill-discover:<skill>` | yes | no | the skill as met in practice: picked from its description |

A skill earns its tokens when the skill arm beats the baseline. A gap between the skill and discover arms means the description fails to trigger it.

## Layout

```
tasks/<task>/
  task.toml            # metadata.skill links the task to a skill
  instruction.md       # the prompt; never names the convention under test
  environment/         # Dockerfile + the repo the agent works in (/app)
  tests/               # verifier; copied in only after the agent exits
  solution/solve.sh    # reference fix; proves the verifier is passable
run.sh                 # one skill, three arms
results/               # git-ignored run artifacts
```

Tasks live outside `skills/` so the baseline arm cannot read the skill.

## Setup

```bash
uv tool install <dokimi-checkout>/dokimi    # Apache-2.0
claude setup-token                          # prints a long-lived OAuth token
```

`run.sh` takes the first credential it finds: `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` in the environment, then the token in `~/.config/dokimi/claude-oauth-token` (chmod 600), then on macOS the logged-in CLI's access token from the keychain. It refreshes that token first if under an hour remains. `claude setup-token` is then optional.

On macOS, dokimi copies the host `claude` into the Linux container, so a Linux build of the same version must come first on PATH. `run.sh` uses `~/.cache/dokimi-linux-claude/claude`:

```bash
v=$(claude --version | cut -d' ' -f1)
docker run --rm -v ~/.cache/dokimi-linux-claude:/out debian:bookworm-slim bash -c \
  "apt-get update -qq && apt-get install -y -qq curl ca-certificates && curl -fsSL https://claude.ai/install.sh | bash -s $v && cp -L \$(readlink -f /root/.local/bin/claude) /out/claude"
```

## Run

```bash
evals/run.sh pydantic --dry-run              # show the matrix
evals/run.sh pydantic                        # 3 tasks x 3 arms x 3 repeats, sonnet
evals/run.sh commit-flow --model haiku --repeats 5
```

The report is `results/<skill>.md`. Per-cell verifier output is in `results/task-runs/<task>/<arm>/run.log`.

## Adding a task

1. Copy a task directory and set `metadata.skill`.
2. Write a prompt a user would type. Don't name the convention being tested.
3. Each assertion checks one rule the skill states. Prefer behaviour (run the code, render the SQL, inspect git) over grepping source.
4. Check both directions before any paid run:
   ```bash
   dokimi tasks run --tasks-root evals/tasks --tasks <task> --harnesses docker-oracle --out evals/results/oracle.json   # must pass
   ```
   and build the image and run `tests/test.sh` on the untouched repo, which must fail.

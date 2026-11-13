# Skill variants for evals

dokimi refuses a skill whose `SKILL.md` frontmatter carries keys that change more than the guidance
(`hooks:`, `model:`, `context: fork`, `disable-model-invocation: true`): a hook runs code in the
skill arm only, outside the measured tool calls. A skill that declares one cannot be a treatment.

Each directory here is a copy of `../../skills/<skill>/` with **only** the refused frontmatter block
removed; every other byte is identical. The tasks still declare `metadata.skill = "<skill>"`, so
results line up with the real skill.

| Variant | Removed | Effect on the eval |
|---|---|---|
| `parallel-mr-feedback` | the `hooks: Stop:` block (runs `skill-update-reminder.sh`) | The step-11 skill-update prompt is measured from the SKILL.md text alone, without the Stop-hook safety net. |

Keep a variant in sync after editing the skill:

```bash
diff -r ../skills/parallel-mr-feedback skill-variants/parallel-mr-feedback   # only the hooks block may differ
```

# Authoring conventions for adhd-focus

Rules for the one skill in this plugin. The markdown and user-invoked rules match skilldeck. The pack machinery (buckets, call graph, coverage) stays in skilldeck.

## Anatomy

`plugins/adhd-focus/skills/adhd-focus/` contains:

- `SKILL.md` with YAML frontmatter (`name`, `description`) followed by the posture.
- `agents/openai.yaml` with `interface.display_name`, `interface.short_description`, and `policy.allow_implicit_invocation: false`.
- `breakdown.md`, read only after the reader asks for a breakdown.

Root `skills` is a symlink to `plugins/adhd-focus/skills`. The files live inside the plugin directory. Cursor refuses a symlink out of the plugin.

## OpenAI package

Codex reads `plugins/adhd-focus/skills/` via `.codex-plugin/plugin.json`. ChatGPT and OpenAI web import the zip that CI attaches to each GitHub Release. `scripts/build-openai-plugin.py` builds that zip. The skill stays at `plugins/adhd-focus/skills/adhd-focus/`.

## Invocation

This skill is user-invoked in both harnesses. Set `disable-model-invocation: true` in the frontmatter and `policy.allow_implicit_invocation: false` in `openai.yaml`. The `description` is a one-line summary. The agent does not reach for it on its own.

## Guardrails this skill earned

- **When this does not apply.** The posture yields to a higher rule, and says what still survives.
- **Persistence.** It stays on until "stop adhd mode" or "normal mode".
- **Excuses that do not hold.** The sentences an agent tells itself to write a long answer anyway.
- **Before you hand it over.** The first and last line must say what happened and what to do next.

A guardrail shapes presentation. It never caps the analysis, the search, the files read, or the options considered.

## Markdown style

Checked by `scripts/validate.py`:

- **`-` for list items**, never `*` or `+`.
- **`**` for strong emphasis**, never `__`.
- **Every opening code fence carries a language.** Use `text` where no language fits.
- **Table rows start `| `**, with a space after the leading pipe.
- **No trailing whitespace, one newline at end of file, never three blank lines in a row.**
- **No em-dashes anywhere.**

One line per paragraph. Do not hard-wrap prose. Tables are not padded to align.

No markdown formatter. A formatter was measured against skilldeck and rejected, and the same constraint holds here.

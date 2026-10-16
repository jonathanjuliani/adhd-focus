# AGENTS.md

Guidance for an agent working **on this repository**, which is a one-skill plugin. It is not meant to be copied into another project: the reusable part of this repo is `skills/`, not this file.

## When editing the skill

Read [`.agents/conventions.md`](.agents/conventions.md) first and follow it. It is the authority on invocation, guardrails, and markdown style.

Then, before finishing:

```bash
python3 scripts/validate.py
python3 scripts/version.py --check
```

A commit is blocked on failure by `.githooks/pre-commit`, which needs `git config core.hooksPath .githooks` once per clone.

## When releasing

Add each change under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) as you make it. Release with `python3 scripts/version.py <patch|minor|major>` on a clean `main`, then `git push --follow-tags`. Never change the version in one file by hand after the `0.0.0` seed: `python3 scripts/version.py --check` fails, and marketplace users only receive a change after a version bump.

## What this repo does not have

No Node toolchain, no package manager, no markdown formatter. Validation uses pyyaml when it is installed, and still runs a narrower frontmatter check without it. Do not add a formatter. The reasoning is the same one recorded in skilldeck's `.agents/conventions.md`.

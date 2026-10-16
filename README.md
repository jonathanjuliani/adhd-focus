# adhd-focus

A session-long output style for a reader with ADHD. Lean by default: the answer first, no noise, one next action. A structured breakdown only when asked.

Adapted from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT).

| Plugin | What it is | Version |
| --- | --- | --- |
| `adhd-focus` | Answer first, no noise, one next action. | 0.0.0 |

## Install

Pick one. A plugin install and `npx skills` together load the skill twice.

Commands for every tool are in [Install](docs/install.md). That is the page an agent should fetch.

### Native plugin

Claude Code:

```text
/plugin marketplace add jonathanjuliani/adhd-focus
/plugin install adhd-focus@adhd-focus
```

Codex:

```bash
codex plugin marketplace add jonathanjuliani/adhd-focus
codex plugin add adhd-focus@adhd-focus
```

Cursor: Customize, then Plugins, then From GitHub Repository, then `https://github.com/jonathanjuliani/adhd-focus`.

GitHub Copilot:

```bash
copilot plugin marketplace add jonathanjuliani/adhd-focus
copilot plugin install adhd-focus@adhd-focus
```

Antigravity, from a clone of this repo:

```bash
agy plugin install ./plugins/adhd-focus
```

Gemini CLI:

```bash
gemini extensions install https://github.com/jonathanjuliani/adhd-focus
```

After a plugin install, start a new session. The command is `/adhd-focus:adhd-focus`.

### Skills only

`npx skills` copies the skill and stays unscoped. The command is `/adhd-focus`.

```bash
npx skills add jonathanjuliani/adhd-focus
```

Devin: `npx skills add jonathanjuliani/adhd-focus -a devin`.

## Update

Update the marketplace, then start a new session. Claude Code: `/plugin marketplace update adhd-focus`, then `/plugin update adhd-focus@adhd-focus`. The other tools are in [Install](docs/install.md). A marketplace user receives a change only after a version bump.

## Release

On a clean `main`, run `python3 scripts/version.py patch` (or `minor` / `major`), then `git push --follow-tags`. The version lives in the harness manifests and moves with the changelog.

## The skill

User-invoked. It stays on until "stop adhd mode" or "normal mode". What it does, and what working looks like: [adhd-focus](docs/adhd-focus.md).

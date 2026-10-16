# Install

How to install, update, and remove adhd-focus.
An agent can install on Claude Code from this file alone.
Back to [adhd-focus](../README.md).

Pick one route. A plugin install and `npx skills` together load the skill twice.

A plugin install namespaces the command as `/adhd-focus:adhd-focus`. `npx skills` stays unscoped, so the command is `/adhd-focus`.

The plugin name is `adhd-focus`. The install id is `adhd-focus@adhd-focus`.

## Claude Code

```text
/plugin marketplace add jonathanjuliani/adhd-focus
/plugin install adhd-focus@adhd-focus
```

Start a new session. Invoke with `/adhd-focus:adhd-focus`. It stays on until "stop adhd mode" or "normal mode".

Cowork on a Personal plan can add this public marketplace. A private repository does not sync there.

Update, then start a new session:

```text
/plugin marketplace update adhd-focus
/plugin update adhd-focus@adhd-focus
```

Remove:

```text
/plugin uninstall adhd-focus@adhd-focus
```

`/plugin disable adhd-focus@adhd-focus` keeps it installed and stops loading it. `/plugin enable adhd-focus@adhd-focus` puts it back. The `claude plugin` shell commands do the same and take `--scope`.

## Codex

```bash
codex plugin marketplace add jonathanjuliani/adhd-focus
codex plugin add adhd-focus@adhd-focus
```

The marketplace file is `.agents/plugins/marketplace.json`. The plugin manifest is `plugins/adhd-focus/.codex-plugin/plugin.json`, and its skills path is `./skills/` inside that plugin. Codex invokes the skill with `@adhd-focus:adhd-focus`.

Update the marketplace from Codex, then start a new session.

## Cursor

GitHub import: Customize, then Plugins, then From GitHub Repository, then `https://github.com/jonathanjuliani/adhd-focus`.

Cursor reads `.cursor-plugin/marketplace.json`. The plugin source is the bare name `adhd-focus` with `pluginRoot` `plugins`. The skill list is `plugins/adhd-focus/.cursor-plugin/plugin.json`. The skill files live in that directory. A symlink out of the plugin is refused.

The command is `/adhd-focus:adhd-focus`, or `/adhd-focus` if Cursor does not namespace.

Local copy, for plugin development: Cursor skips a symlink whose target is outside `~/.cursor/plugins/local`.

```bash
./scripts/install-cursor.sh
```

Quit Cursor and reopen. Enable **Include third-party Plugins, Skills, and other configs**. On Teams or Enterprise, an admin also enables **Allow Local Plugin Imports**.

Team: Dashboard, then Plugins, then Add Marketplace, then Import from Repo, then `https://github.com/jonathanjuliani/adhd-focus`.

Update by installing again after a version bump. A refresh does not always pick up a new version.

## GitHub Copilot

```bash
copilot plugin marketplace add jonathanjuliani/adhd-focus
copilot plugin marketplace browse adhd-focus
copilot plugin install adhd-focus@adhd-focus
```

Copilot looks for `marketplace.json` in `.github/plugin/`, then in `.claude-plugin/`. This repo ships only `.claude-plugin/marketplace.json`, so the two catalogs cannot drift. The plugin source is `./`, and the manifest Copilot loads is `.claude-plugin/plugin.json`. That file lists the skill path. Do not add a root `plugin.json`: Copilot would prefer it over the Claude manifest.

Update:

```bash
copilot plugin marketplace update adhd-focus
```

## VS Code

```json
{
  "chat.plugins.enabled": true,
  "chat.plugins.marketplaces": ["jonathanjuliani/adhd-focus"]
}
```

The skill stays at `plugins/adhd-focus/skills/adhd-focus/SKILL.md`. Claude and Cursor keep their explicit lists.

## Antigravity

From a clone:

```bash
agy plugin install ./plugins/adhd-focus
agy plugin list
```

`plugins/adhd-focus/plugin.json` is the Antigravity manifest (`name` and `description` only). The skill is `skills/adhd-focus/SKILL.md`. If `agy plugin list` shows no skills, use `npx skills add jonathanjuliani/adhd-focus`. Workspace copies live in `.agents/skills/`.

Do not install the GitHub URL of the repository root. A `plugin.json` there would hide `.claude-plugin/plugin.json` from Copilot.

## Gemini CLI

```bash
gemini extensions install https://github.com/jonathanjuliani/adhd-focus
```

The extension name in `gemini-extension.json` is `adhd-focus`. It loads `GEMINI.md`.

## Devin

This release has no Devin plugin.

```bash
npx skills add jonathanjuliani/adhd-focus -a devin
```

The files land in `.devin/skills/` or `~/.config/devin/skills/`. The command stays `/adhd-focus`.

## Windsurf and OpenCode

```bash
npx skills add jonathanjuliani/adhd-focus -a windsurf
npx skills add jonathanjuliani/adhd-focus -a opencode
```

Same unscoped command as any `npx skills` install.

## Skills only, any agent

```bash
npx skills add jonathanjuliani/adhd-focus --list
npx skills add jonathanjuliani/adhd-focus
```

`-g` installs for your user instead of the project. `-a` targets one agent.

The command is `/adhd-focus`. It is not `/adhd-focus:adhd-focus`.

Remove:

```bash
npx skills list
npx skills remove adhd-focus
npx skills remove --all
```

`remove --all` removes every installed skill from every source, not only this one.

## skills.sh

The listing URL is [skills.sh/jonathanjuliani/adhd-focus](https://www.skills.sh/jonathanjuliani/adhd-focus).
The index is filled by the skills CLI. This repo has no skills.sh config file.

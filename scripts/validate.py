#!/usr/bin/env python3
"""Structural checks for the adhd-focus plugin. Run before committing.

Checks the rules in .agents/conventions.md: frontmatter, the user-invoked pair,
the guardrails this skill earned, markdown style, relative links, and harness
manifests that must agree. Marketplace JSON is checked in CI by skilldeck's
marketplace-check workflow.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\((?!https?://|#)([^)]+)\)")
DESCRIPTION = (
    "A session-long output style for a reader with ADHD. Lean by default, "
    "with a structured breakdown only when asked."
)
PLUGIN = "adhd-focus"
SKILL_PATH = "./skills/adhd-focus"
GUARDRAILS = (
    "## When this does not apply",
    "## Persistence",
    "## Excuses that do not hold",
    "## Before you hand it over",
)
STYLE_FILES = [
    *ROOT.glob("plugins/adhd-focus/skills/**/*.md"),
    *ROOT.glob("skills/**/*.md"),
    *ROOT.glob("docs/**/*.md"),
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "GEMINI.md",
    ROOT / ".agents" / "conventions.md",
    ROOT / "CHANGELOG.md",
]
IDENTITY_FILES = (
    ".claude-plugin/plugin.json",
    "plugins/adhd-focus/.cursor-plugin/plugin.json",
    "plugins/adhd-focus/.codex-plugin/plugin.json",
)
AGY_MANIFEST = "plugins/adhd-focus/plugin.json"
AGY_SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
AGY_KEYS = {"$schema", "name", "description"}

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(rel: str) -> dict | None:
    path = ROOT / rel
    if not path.is_file():
        fail(f"{rel}: missing")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{rel}: invalid JSON ({exc.msg})")
        return None
    if not isinstance(data, dict):
        fail(f"{rel}: manifest must be a JSON object")
        return None
    return data


def skill_file() -> Path | None:
    path = ROOT / "plugins" / PLUGIN / "skills" / PLUGIN / "SKILL.md"
    if not path.is_file():
        fail(f"{path.relative_to(ROOT)}: missing")
        return None
    return path


def check_skill(path: Path) -> None:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{rel}: no frontmatter")
        return
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail(f"{rel}: frontmatter is not closed")
        return
    if yaml is None:
        frontmatter: dict = {}
        for raw in parts[1].splitlines():
            if not raw or raw.startswith((" ", "\t", "#")):
                continue
            key, sep, value = raw.partition(":")
            if sep:
                frontmatter[key.strip()] = value.strip().strip("\"'")
    else:
        try:
            loaded = yaml.safe_load(parts[1])
        except yaml.YAMLError as exc:
            fail(f"{rel}: frontmatter is not valid YAML. {exc}")
            return
        if not isinstance(loaded, dict):
            fail(f"{rel}: frontmatter must be a mapping")
            return
        frontmatter = loaded
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name.strip():
        fail(f"{rel}: missing name")
    elif name != path.parent.name:
        fail(f"{rel}: name is {name!r}, folder is {path.parent.name!r}")
    if not isinstance(description, str) or not description.strip():
        fail(f"{rel}: missing description")
    user_invoked = frontmatter.get("disable-model-invocation") in (True, "true")
    if not user_invoked:
        fail(f"{rel}: missing disable-model-invocation: true")
    for heading in GUARDRAILS:
        if heading not in text:
            fail(f"{rel}: missing the {heading!r} guardrail")
    if "—" in text:
        fail(f"{rel}: contains an em-dash, which the authoring conventions ban")
    if "](breakdown.md)" not in text:
        fail(f"{rel}: does not link breakdown.md for the breakdown path")
    check_openai(path.parent / "agents" / "openai.yaml", rel, user_invoked)


def check_openai(path: Path, skill_rel: Path, user_invoked: bool) -> None:
    rel = str(path.relative_to(ROOT))
    if not path.is_file():
        fail(f"{skill_rel}: missing agents/openai.yaml")
        return
    if yaml is None:
        return
    try:
        meta = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        fail(f"{rel}: not valid YAML. {exc}")
        return
    if not isinstance(meta, dict):
        fail(f"{rel}: must be a mapping")
        return
    unknown = set(meta) - {"interface", "policy", "dependencies"}
    if unknown:
        fail(f"{rel}: unsupported top-level fields {sorted(unknown)}")
    interface = meta.get("interface") or {}
    if not isinstance(interface, dict):
        fail(f"{rel}: interface must be a mapping")
        interface = {}
    for key in ("display_name", "short_description"):
        if not interface.get(key):
            fail(f"{rel}: missing interface.{key}")
    policy = meta.get("policy") or {}
    if not isinstance(policy, dict):
        fail(f"{rel}: policy must be a mapping")
        policy = {}
    unknown_policy = set(policy) - {"products", "allow_implicit_invocation"}
    if unknown_policy:
        fail(f"{rel}: policy has unsupported fields {sorted(unknown_policy)}")
    implicit = policy.get("allow_implicit_invocation")
    if user_invoked and implicit is not False:
        fail(f"{rel}: policy.allow_implicit_invocation must be false")
    if not user_invoked and implicit is False:
        fail(f"{skill_rel}: openai.yaml forbids implicit invocation but disable-model-invocation is unset")


def check_style() -> None:
    seen: set[Path] = set()
    for path in STYLE_FILES:
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if "—" in text:
            fail(f"{rel}: contains an em-dash, which the authoring conventions ban")
        fenced = False
        for number, line in enumerate(text.splitlines(), 1):
            if line.startswith("```"):
                if not fenced and line.strip() == "```":
                    fail(f"{rel}:{number}: opening code fence has no language (use ```text if none fits)")
                fenced = not fenced
                continue
            if fenced:
                continue
            visible = re.sub(r"`[^`]*`", "``", line)
            if re.match(r"^\s*[*+] ", visible):
                fail(f"{rel}:{number}: list marker is '{visible.lstrip()[0]}', this repo uses '-'")
            if re.search(r"(?<!_)__(?!_)\S", visible):
                fail(f"{rel}:{number}: strong emphasis uses '__', this repo uses '**'")
            if visible.startswith("|") and visible.count("|") > 2 and not visible.startswith("| "):
                fail(f"{rel}:{number}: table row needs a space after the leading pipe")
        if "\n\n\n\n" in text:
            fail(f"{rel}: three or more consecutive blank lines")
        if text and not text.endswith("\n"):
            fail(f"{rel}: no newline at end of file")
        for number, line in enumerate(text.splitlines(), 1):
            if line != line.rstrip():
                fail(f"{rel}:{number}: trailing whitespace")
                break
        for target in LINK.findall(text):
            linked = (path.parent / target.split("#")[0]).resolve()
            if not linked.exists():
                fail(f"{rel}: link to '{target}' does not resolve")


def check_symlink() -> None:
    link = ROOT / "skills"
    if not link.is_symlink():
        fail("skills: must be a symlink to plugins/adhd-focus/skills")
        return
    target = link.readlink()
    if str(target) != "plugins/adhd-focus/skills":
        fail(f"skills: symlink should be plugins/adhd-focus/skills, found {str(target)!r}")


def check_identity() -> None:
    loaded: dict[str, dict] = {}
    for rel in IDENTITY_FILES:
        data = load_json(rel)
        if data is None:
            continue
        loaded[rel] = data
        if data.get("name") != PLUGIN:
            fail(f"{rel}: name should be {PLUGIN!r}, found {data.get('name')!r}")
        if data.get("description") != DESCRIPTION:
            fail(f"{rel}: description drifted from the shared plugin description")
        if data.get("license") != "MIT":
            fail(f"{rel}: license should be 'MIT', found {data.get('license')!r}")
    if len(loaded) > 1:
        versions = {rel: data.get("version") for rel, data in loaded.items()}
        if len(set(versions.values())) > 1:
            fail(f"manifests disagree on version: {versions}")
    claude = loaded.get(".claude-plugin/plugin.json")
    cursor = loaded.get("plugins/adhd-focus/.cursor-plugin/plugin.json")
    codex = loaded.get("plugins/adhd-focus/.codex-plugin/plugin.json")
    if claude is not None and claude.get("skills") != [SKILL_PATH]:
        fail(f".claude-plugin/plugin.json: skills should be [{SKILL_PATH!r}]")
    if cursor is not None and cursor.get("skills") != [SKILL_PATH]:
        fail(f"plugins/adhd-focus/.cursor-plugin/plugin.json: skills should be [{SKILL_PATH!r}]")
    if codex is not None and codex.get("skills") != "./skills/":
        fail("plugins/adhd-focus/.codex-plugin/plugin.json: skills should be './skills/'")


def check_marketplaces() -> None:
    claude = load_json(".claude-plugin/marketplace.json")
    if claude is not None:
        plugins = claude.get("plugins") or []
        if claude.get("name") != PLUGIN:
            fail(f".claude-plugin/marketplace.json: name should be {PLUGIN!r}")
        if len(plugins) != 1 or plugins[0].get("name") != PLUGIN:
            fail(".claude-plugin/marketplace.json: expected exactly one plugin named adhd-focus")
        elif plugins[0].get("source") != "./":
            fail(".claude-plugin/marketplace.json: source should be './'")
        elif plugins[0].get("description") != DESCRIPTION:
            fail(".claude-plugin/marketplace.json: description drifted")
    cursor = load_json(".cursor-plugin/marketplace.json")
    if cursor is not None:
        plugins = cursor.get("plugins") or []
        metadata = cursor.get("metadata") or {}
        if cursor.get("name") != PLUGIN:
            fail(f".cursor-plugin/marketplace.json: name should be {PLUGIN!r}")
        if metadata.get("pluginRoot") != "plugins":
            fail(".cursor-plugin/marketplace.json: pluginRoot should be 'plugins'")
        if len(plugins) != 1 or plugins[0].get("name") != PLUGIN:
            fail(".cursor-plugin/marketplace.json: expected exactly one plugin named adhd-focus")
        elif plugins[0].get("source") != PLUGIN:
            fail(".cursor-plugin/marketplace.json: source should be 'adhd-focus'")
    codex = load_json(".agents/plugins/marketplace.json")
    if codex is not None:
        plugins = codex.get("plugins") or []
        if codex.get("name") != PLUGIN:
            fail(f".agents/plugins/marketplace.json: name should be {PLUGIN!r}")
        if len(plugins) != 1 or plugins[0].get("name") != PLUGIN:
            fail(".agents/plugins/marketplace.json: expected exactly one plugin named adhd-focus")
        else:
            source = plugins[0].get("source") or {}
            if source.get("path") != "./plugins/adhd-focus":
                fail(".agents/plugins/marketplace.json: source.path should be './plugins/adhd-focus'")


def check_gemini() -> None:
    data = load_json("gemini-extension.json")
    if data is None:
        return
    if data.get("name") != PLUGIN:
        fail(f"gemini-extension.json: name should be {PLUGIN!r}, found {data.get('name')!r}")
    if data.get("description") != DESCRIPTION:
        fail("gemini-extension.json: description drifted")
    context = data.get("contextFileName")
    if context != "GEMINI.md":
        fail(f"gemini-extension.json: contextFileName should be 'GEMINI.md', found {context!r}")
    elif not (ROOT / "GEMINI.md").is_file():
        fail("gemini-extension.json: GEMINI.md does not exist")
    claude = load_json(".claude-plugin/plugin.json")
    if claude is not None and data.get("version") != claude.get("version"):
        fail("gemini-extension.json: version does not match .claude-plugin/plugin.json")


def check_antigravity() -> None:
    data = load_json(AGY_MANIFEST)
    if data is None:
        return
    extra = sorted(set(data) - AGY_KEYS)
    if extra:
        fail(f"{AGY_MANIFEST}: unknown fields {extra}. Antigravity rejects them.")
    if data.get("$schema") != AGY_SCHEMA:
        fail(f"{AGY_MANIFEST}: $schema should be {AGY_SCHEMA!r}")
    if data.get("name") != PLUGIN:
        fail(f"{AGY_MANIFEST}: name should be {PLUGIN!r}, found {data.get('name')!r}")
    if data.get("description") != DESCRIPTION:
        fail(f"{AGY_MANIFEST}: description drifted")


def check_no_root_plugin() -> None:
    if (ROOT / "plugin.json").exists():
        fail("plugin.json: root manifest would hide .claude-plugin/plugin.json from Copilot")
    page = ROOT / "docs" / "adhd-focus.md"
    if not page.is_file():
        fail("docs/adhd-focus.md: missing user page")


def main() -> int:
    path = skill_file()
    if path is not None:
        check_skill(path)
    check_style()
    check_symlink()
    check_identity()
    check_marketplaces()
    check_gemini()
    check_antigravity()
    check_no_root_plugin()
    for message in errors:
        print(message)
    if yaml is None and not any(message.startswith("pyyaml") for message in errors):
        print("validate: pyyaml is not installed; YAML bodies were skipped", file=sys.stderr)
    if errors:
        print(f"validate: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("validate: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

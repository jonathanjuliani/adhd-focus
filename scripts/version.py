#!/usr/bin/env python3
"""One version for this plugin, kept in the harness manifests and the changelog.

Run from the repository root.

    python3 scripts/version.py patch|minor|major
        Bumps the version in .claude-plugin/plugin.json, copies it into the
        other manifests and the README version cell, turns the changelog's
        Unreleased section into a dated section, then commits and tags vX.Y.Z.
        Refuses a release whose Unreleased section has no bullet.

    python3 scripts/version.py --check [vX.Y.Z]
        Fails when the manifest versions differ. Given a tag, also fails when
        they differ from it or the changelog has no section for it. CI runs this.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = "https://github.com/jonathanjuliani/adhd-focus"
PLUGIN_NAME = "adhd-focus"
CANONICAL = ".claude-plugin/plugin.json"
VERSION_FILES = (
    ".claude-plugin/plugin.json",
    "plugins/adhd-focus/.cursor-plugin/plugin.json",
    "plugins/adhd-focus/.codex-plugin/plugin.json",
    "gemini-extension.json",
)
MARKETPLACE = ".claude-plugin/marketplace.json"
CHANGELOG = "CHANGELOG.md"
README = "README.md"
README_VERSION = re.compile(
    r"(\| `" + PLUGIN_NAME + r"` \| [^|]*\| )(\d+\.\d+\.\d+)( \|)"
)


def fail(message: str) -> None:
    print(f"version: {message}", file=sys.stderr)
    sys.exit(1)


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        fail(detail or f"git {' '.join(args)} failed")
    return result


def bump_version(version: str, kind: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        fail(f"{version!r} is not a major.minor.patch version")
    major, minor, patch = (int(part) for part in match.groups())
    if kind == "major":
        major, minor, patch = major + 1, 0, 0
    elif kind == "minor":
        minor, patch = minor + 1, 0
    elif kind == "patch":
        patch += 1
    else:
        fail(f"unknown bump {kind!r}; use patch, minor, or major")
    return f"{major}.{minor}.{patch}"


def marketplace_entry(data: dict) -> dict | None:
    for entry in data.get("plugins") or []:
        if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME:
            return entry
    return None


def readme_version() -> str | None:
    path = Path(README)
    if not path.is_file():
        return None
    match = README_VERSION.search(path.read_text(encoding="utf-8"))
    if match is None:
        fail(f"{README} has no version cell for {PLUGIN_NAME}")
    return match.group(2)


def found_versions() -> dict[str, str | None]:
    found: dict[str, str | None] = {}
    for path in VERSION_FILES:
        found[path] = read_json(path).get("version")
    entry = marketplace_entry(read_json(MARKETPLACE))
    found[f"{MARKETPLACE}#{PLUGIN_NAME}"] = None if entry is None else entry.get("version")
    if Path(README).is_file():
        found[README] = readme_version()
    return found


def unreleased_body(changelog: str) -> str | None:
    match = re.search(r"(?m)^## \[Unreleased\]\n(.*?)(?=^## |\Z)", changelog, re.S)
    if not match:
        return None
    return match.group(1)


def cut_changelog(changelog: str, version: str) -> str:
    if f"## [{version}]" in changelog:
        fail(f"{CHANGELOG} already has a \"## [{version}]\" section")
    if "## [Unreleased]" not in changelog:
        fail(f"{CHANGELOG} has no \"## [Unreleased]\" section to release")
    body = unreleased_body(changelog)
    if body is None or not re.search(r"(?m)^- ", body):
        fail(f"{CHANGELOG} has no bullet under \"## [Unreleased]\" to release")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    previous = re.search(r"(?m)^\[(\d+\.\d+\.\d+)\]: ", changelog)
    previous_version = previous.group(1) if previous else None
    changelog = changelog.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{version}] - {today}",
        1,
    )
    released = (
        f"{REPO}/compare/v{previous_version}...v{version}"
        if previous_version
        else f"{REPO}/releases/tag/v{version}"
    )
    links = f"[Unreleased]: {REPO}/compare/v{version}...HEAD\n[{version}]: {released}"
    changelog, count = re.subn(r"(?m)^\[Unreleased\]: .*$", links, changelog, count=1)
    if count != 1:
        fail(f"{CHANGELOG} has no \"[Unreleased]\" link")
    return changelog


def write_version(version: str) -> list[str]:
    for path in VERSION_FILES:
        data = read_json(path)
        data["version"] = version
        write_json(path, data)
    marketplace = read_json(MARKETPLACE)
    entry = marketplace_entry(marketplace)
    if entry is None:
        fail(f"{MARKETPLACE} has no plugin named {PLUGIN_NAME}")
    entry["version"] = version
    write_json(MARKETPLACE, marketplace)
    extra: list[str] = []
    readme = Path(README)
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        updated, count = README_VERSION.subn(rf"\g<1>{version}\g<3>", text, count=1)
        if count != 1:
            fail(f"{README} has no version cell to update")
        readme.write_text(updated, encoding="utf-8")
        extra.append(README)
    return extra


def check(tag_arg: str | None) -> None:
    found = found_versions()
    canonical = found[CANONICAL]
    differing = [path for path, value in found.items() if value != canonical]
    if differing:
        detail = ", ".join(f"{path} {value}" for path, value in found.items())
        fail(f"versions differ: {detail}. Run a release from {CANONICAL}")
    tag = None
    if tag_arg:
        tag = tag_arg.removeprefix("refs/tags/").removeprefix("v")
    if tag and tag != canonical:
        fail(f"tag v{tag} but the files say {canonical}")
    if tag and f"## [{canonical}]" not in Path(CHANGELOG).read_text(encoding="utf-8"):
        fail(f"{CHANGELOG} has no \"## [{canonical}]\" section")
    suffix = ", matching the tag" if tag else ""
    print(f"version: {canonical} in the manifests{suffix}")


def require_release_branch() -> None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != "main":
        fail(f"refusing to release from {branch!r}; switch to main")
    dirty = git("status", "--porcelain").stdout.strip()
    if dirty:
        fail("working tree is not clean")


def release(kind: str) -> None:
    require_release_branch()
    current = read_json(CANONICAL).get("version")
    if not isinstance(current, str):
        fail(f"{CANONICAL} has no version")
    new = bump_version(current, kind)
    changelog = cut_changelog(Path(CHANGELOG).read_text(encoding="utf-8"), new)
    extra = write_version(new)
    Path(CHANGELOG).write_text(changelog, encoding="utf-8")
    git("add", "--", *VERSION_FILES, MARKETPLACE, CHANGELOG, *extra)
    git("commit", "-m", f"v{new}")
    git("tag", "-a", f"v{new}", "-m", f"v{new}")
    print(f"version: {new} written, committed and tagged v{new}")


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--check"]:
        check(None)
        return
    if len(args) == 2 and args[0] == "--check":
        check(args[1])
        return
    if len(args) == 1 and args[0] in ("patch", "minor", "major"):
        release(args[0])
        return
    fail("usage: python3 scripts/version.py patch|minor|major | --check [vX.Y.Z]")


if __name__ == "__main__":
    main()

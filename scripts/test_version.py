#!/usr/bin/env python3
"""Tests for scripts/version.py. Stdlib only; run from anywhere."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import version as version_script


SCRIPT = Path(version_script.__file__).resolve()
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "version test",
    "GIT_AUTHOR_EMAIL": "version-test@example.com",
    "GIT_COMMITTER_NAME": "version test",
    "GIT_COMMITTER_EMAIL": "version-test@example.com",
}


def git(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True,
        env=GIT_ENV,
        capture_output=True,
        text=True,
    )


def run(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=directory,
        env=GIT_ENV,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def changelog(released: str, *, bullet: bool) -> str:
    notes = "### Fixed\n\n- A fix.\n" if bullet else ""
    repo = version_script.REPO
    return (
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        f"{notes}\n"
        f"## [{released}] - 2026-10-07\n\n"
        f"[Unreleased]: {repo}/compare/v{released}...HEAD\n"
        f"[{released}]: {repo}/releases/tag/v{released}\n"
    )


def make_repo(current: str, other: str | None = None, *, released: str | None = None, bullet: bool = True) -> Path:
    """A throwaway repo holding just the files the script reads and writes."""
    other = current if other is None else other
    released = current if released is None else released
    directory = Path(tempfile.mkdtemp(prefix="skills-version-"))
    for path in version_script.VERSION_FILES:
        value = current if path == version_script.CANONICAL else other
        write_json(directory / path, {"name": version_script.PLUGIN_NAME, "version": value})
    write_json(
        directory / version_script.MARKETPLACE,
        {"plugins": [{"name": version_script.PLUGIN_NAME, "version": other}]},
    )
    (directory / version_script.CHANGELOG).write_text(
        changelog(released, bullet=bullet),
        encoding="utf-8",
    )
    return directory


def commit_all(directory: Path) -> None:
    git(directory, "init", "-b", "main")
    git(directory, "add", "-A")
    git(directory, "commit", "-m", "init")


class VersionScriptTest(unittest.TestCase):
    directory: Path

    def tearDown(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_patch_writes_every_manifest_and_cuts_the_changelog(self) -> None:
        self.directory = make_repo("0.1.0")
        commit_all(self.directory)
        result = run(self.directory, "patch")
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in version_script.VERSION_FILES:
            data = json.loads((self.directory / path).read_text(encoding="utf-8"))
            self.assertEqual(data["version"], "0.1.1")
        marketplace = json.loads((self.directory / version_script.MARKETPLACE).read_text(encoding="utf-8"))
        self.assertEqual(marketplace["plugins"][0]["version"], "0.1.1")
        text = (self.directory / version_script.CHANGELOG).read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r"## \[Unreleased\]\n\n## \[0\.1\.1\] - \d{4}-\d{2}-\d{2}\n\n### Fixed\n\n- A fix\.",
        )
        repo = version_script.REPO
        self.assertIn(f"[Unreleased]: {repo}/compare/v0.1.1...HEAD", text)
        self.assertIn(f"[0.1.1]: {repo}/compare/v0.1.0...v0.1.1", text)
        self.assertEqual(git(self.directory, "log", "-1", "--format=%s").stdout.strip(), "v0.1.1")
        self.assertIn("v0.1.1", git(self.directory, "tag", "--list").stdout)
        checked = run(self.directory, "--check", "v0.1.1")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("matching the tag", checked.stdout)

    def test_check_fails_when_manifests_disagree(self) -> None:
        self.directory = make_repo("0.2.0", other="0.1.0")
        result = run(self.directory, "--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("versions differ", result.stderr)

    def test_check_fails_against_a_tag_the_files_do_not_carry(self) -> None:
        self.directory = make_repo("0.1.0")
        result = run(self.directory, "--check", "v0.3.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tag v0.3.0 but the files say 0.1.0", result.stderr)

    def test_check_fails_when_the_changelog_has_no_section_for_the_tag(self) -> None:
        self.directory = make_repo("0.2.0", released="0.1.0")
        result = run(self.directory, "--check", "v0.2.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no "## [0.2.0]" section', result.stderr)

    def test_patch_refuses_an_empty_unreleased_section(self) -> None:
        self.directory = make_repo("0.1.0", bullet=False)
        commit_all(self.directory)
        result = run(self.directory, "patch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no bullet", result.stderr)
        data = json.loads((self.directory / version_script.CANONICAL).read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(git(self.directory, "tag", "--list").stdout.strip(), "")
        self.assertEqual(git(self.directory, "status", "--porcelain").stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()

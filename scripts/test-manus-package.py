#!/usr/bin/env python3
"""Validate the Manus adhd-focus archive without changing the canonical skill or the OpenAI package."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import subprocess
import sys
import tempfile
import zipfile

import yaml


ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = ROOT / "scripts" / "build-manus-skills.py"
OPENAI_BUILDER = ROOT / "scripts" / "build-openai-plugin.py"
OPENAI_TEST = ROOT / "scripts" / "test-openai-package.py"
SOURCE_SKILL = ROOT / "plugins" / "adhd-focus" / "skills" / "adhd-focus"
HOST_LINE = (
    'Keep this shape on every later turn until the reader says "stop adhd mode" '
    'or "normal mode".'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Manus adhd-focus archive.")
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument(
        "--skip-determinism",
        action="store_true",
        help="Skip rebuilding twice and comparing the resulting archives.",
    )
    return parser.parse_args()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(SOURCE_SKILL.rglob("*")):
        if path.is_file():
            hashes[str(path.relative_to(SOURCE_SKILL))] = sha256(path)
    if "SKILL.md" not in hashes or "breakdown.md" not in hashes:
        raise AssertionError("canonical adhd-focus skill is missing SKILL.md or breakdown.md")
    return hashes


def load_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md has no YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise AssertionError("SKILL.md has unclosed YAML frontmatter")
    payload = yaml.safe_load(parts[1])
    if not isinstance(payload, dict):
        raise AssertionError("SKILL.md frontmatter must be a mapping")
    return payload


def validate_output(output: pathlib.Path) -> None:
    output = output.resolve()
    archives = sorted(output.glob("*.skill"))
    if [archive.name for archive in archives] != ["adhd-focus.skill"]:
        raise AssertionError(f"expected only adhd-focus.skill, found {[path.name for path in archives]}")
    archive = archives[0]
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.namelist()
        if "adhd-focus/agents/openai.yaml" in members or any(
            "openai.yaml" in pathlib.PurePosixPath(member).parts for member in members
        ):
            raise AssertionError("archive still contains agents/openai.yaml")
        if "adhd-focus/SKILL.md" not in members or "adhd-focus/breakdown.md" not in members:
            raise AssertionError("archive is missing SKILL.md or breakdown.md")
        text = bundle.read("adhd-focus/SKILL.md").decode("utf-8")
        roots = {pathlib.PurePosixPath(member).parts[0] for member in members}
    if roots != {"adhd-focus"}:
        raise AssertionError("archive must contain one adhd-focus root")
    frontmatter = load_frontmatter(text)
    if frontmatter.get("name") != "adhd-focus":
        raise AssertionError(f"archive names itself {frontmatter.get('name')!r}")
    if "disable-model-invocation: true" not in text.split("---\n", 2)[1]:
        raise AssertionError("archive dropped disable-model-invocation")
    if "## On Manus" not in text or HOST_LINE not in text:
        raise AssertionError("archive lacks the Manus persistence block")
    if "](breakdown.md)" not in text:
        raise AssertionError("archive dropped the breakdown.md link")
    print("Manus package validation passed: adhd-focus")


def assert_sources_unchanged(before: dict[str, str]) -> None:
    after = source_hashes()
    if after != before:
        raise AssertionError("canonical adhd-focus files changed")
    source = (SOURCE_SKILL / "SKILL.md").read_text(encoding="utf-8")
    if "## On Manus" in source:
        raise AssertionError("canonical SKILL.md gained the Manus block")
    if "disable-model-invocation: true" not in source:
        raise AssertionError("canonical SKILL.md lost disable-model-invocation")


def assert_openai_package_still_differs() -> None:
    if "retains Claude-only frontmatter" not in OPENAI_TEST.read_text(encoding="utf-8"):
        raise AssertionError("OpenAI package test no longer rejects disable-model-invocation")
    with tempfile.TemporaryDirectory(prefix="adhd-focus-openai-untouched-") as temporary:
        output = pathlib.Path(temporary) / "adhd-focus"
        subprocess.run(
            [
                sys.executable,
                str(OPENAI_BUILDER),
                "--output",
                str(output),
                "--no-archive",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        generated = (output / "skills" / "adhd-focus" / "SKILL.md").read_text(encoding="utf-8")
    if "disable-model-invocation: true" in generated:
        raise AssertionError("OpenAI package kept disable-model-invocation")
    if "## On Manus" in generated:
        raise AssertionError("OpenAI package gained the Manus block")


def validate_determinism() -> None:
    with tempfile.TemporaryDirectory(prefix="adhd-focus-manus-determinism-") as temporary:
        temporary_root = pathlib.Path(temporary)
        hashes = []
        for label in ("first", "second"):
            output = temporary_root / label
            subprocess.run(
                [sys.executable, str(BUILDER), "--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            archive = output / "adhd-focus.skill"
            hashes.append(sha256(archive))
        if hashes[0] != hashes[1]:
            raise AssertionError("two clean builds produced different Manus archives")
    print("Deterministic Manus build validation passed")


def main() -> None:
    args = parse_args()
    before = source_hashes()
    validate_output(args.output)
    assert_sources_unchanged(before)
    assert_openai_package_still_differs()
    assert_sources_unchanged(before)
    if not args.skip_determinism:
        validate_determinism()
        assert_sources_unchanged(before)


if __name__ == "__main__":
    main()

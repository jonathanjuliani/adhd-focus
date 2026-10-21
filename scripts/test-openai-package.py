#!/usr/bin/env python3
"""Validate the generated OpenAI plugin package and its deterministic build."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile

import yaml


ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = ROOT / "scripts" / "build-openai-plugin.py"
SOURCE_MANIFEST = ROOT / "plugins" / "adhd-focus" / ".codex-plugin" / "plugin.json"
PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
LINK = re.compile(r"\[[^\]]*\]\((?!https?://|#)([^)]+)\)")
SUPPORTED_AGENT_FIELDS = {"interface", "policy", "dependencies"}
SUPPORTED_POLICY_FIELDS = {"products", "allow_implicit_invocation"}
FORBIDDEN_ARCHIVE_NAMES = {".DS_Store", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an OpenAI plugin package.")
    parser.add_argument("plugin_path", type=pathlib.Path)
    parser.add_argument("--archive", type=pathlib.Path)
    parser.add_argument(
        "--skip-determinism",
        action="store_true",
        help="Skip rebuilding twice and comparing the resulting archives.",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} must contain an object")
    return payload


def load_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} has no YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise AssertionError(f"{path} has unclosed YAML frontmatter")
    payload = yaml.safe_load(parts[1])
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} frontmatter must be a mapping")
    return payload


def source_skill_names() -> set[str]:
    names: set[str] = set()
    for path in ROOT.glob("skills/*/SKILL.md"):
        name = load_frontmatter(path).get("name")
        if name in names:
            raise AssertionError(f"duplicate source skill name: {name}")
        names.add(name)
    return names


def validate_relative_links(skill_root: pathlib.Path) -> None:
    for markdown in skill_root.rglob("*.md"):
        for target in LINK.findall(markdown.read_text(encoding="utf-8")):
            raw_path = target.split("#", 1)[0]
            if not raw_path:
                continue
            destination = (markdown.parent / raw_path).resolve()
            try:
                destination.relative_to(skill_root.resolve())
            except ValueError:
                continue
            if not destination.exists():
                raise AssertionError(f"{markdown}: broken relative link {target!r}")


def validate_agent_metadata(path: pathlib.Path) -> None:
    metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise AssertionError(f"{path} must contain a mapping")
    unknown = set(metadata) - SUPPORTED_AGENT_FIELDS
    if unknown:
        raise AssertionError(f"{path} has unsupported fields: {sorted(unknown)}")
    interface = metadata.get("interface")
    if not isinstance(interface, dict):
        raise AssertionError(f"{path} must contain interface metadata")
    for field in ("display_name", "short_description"):
        if not isinstance(interface.get(field), str) or not interface[field].strip():
            raise AssertionError(f"{path} is missing interface.{field}")
    policy = metadata.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            raise AssertionError(f"{path} policy must be a mapping")
        unknown_policy = set(policy) - SUPPORTED_POLICY_FIELDS
        if unknown_policy:
            raise AssertionError(
                f"{path} has unsupported policy fields: {sorted(unknown_policy)}"
            )


def validate_package(plugin_root: pathlib.Path, archive: pathlib.Path | None) -> None:
    plugin_root = plugin_root.resolve()
    source_manifest = load_json(SOURCE_MANIFEST)
    portable = load_json(plugin_root / "plugin.json")
    compatibility = load_json(plugin_root / ".codex-plugin" / "plugin.json")

    if portable.get("$schema") != PORTABLE_SCHEMA:
        raise AssertionError("portable plugin.json has the wrong Agent Plugins schema")
    if "skills" in portable or "skills" in compatibility:
        raise AssertionError("generated manifests must use fixed root skill discovery")
    for field in ("name", "version", "description", "author", "homepage", "repository"):
        if portable.get(field) != source_manifest.get(field):
            raise AssertionError(f"portable manifest drifted from source field {field!r}")
        if compatibility.get(field) != source_manifest.get(field):
            raise AssertionError(f"compatibility manifest drifted from source field {field!r}")
    portable_interface = (
        portable.get("extensions", {}).get("com.openai", {}).get("interface")
    )
    if portable_interface != source_manifest.get("interface"):
        raise AssertionError("portable OpenAI interface drifted from the source manifest")
    if compatibility.get("interface") != source_manifest.get("interface"):
        raise AssertionError("compatibility interface drifted from the source manifest")

    skills_root = plugin_root / "skills"
    direct_skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    packaged_names: set[str] = set()
    for skill_root in direct_skill_dirs:
        manifest_path = skill_root / "SKILL.md"
        if not manifest_path.is_file():
            raise AssertionError(f"generated skill {skill_root.name!r} lacks SKILL.md")
        frontmatter = load_frontmatter(manifest_path)
        name = frontmatter.get("name")
        if name != skill_root.name:
            raise AssertionError(
                f"generated skill directory {skill_root.name!r} names itself {name!r}"
            )
        if frontmatter.get("disable-model-invocation") is True:
            raise AssertionError(f"generated skill {name!r} retains Claude-only frontmatter")
        if name in packaged_names:
            raise AssertionError(f"duplicate generated skill name: {name}")
        packaged_names.add(name)
        metadata = skill_root / "agents" / "openai.yaml"
        if not metadata.is_file():
            raise AssertionError(f"generated skill {name!r} lacks agents/openai.yaml")
        validate_agent_metadata(metadata)
        validate_relative_links(skill_root)

    nested_manifests = set(skills_root.glob("**/SKILL.md")) - {
        path / "SKILL.md" for path in direct_skill_dirs
    }
    if nested_manifests:
        rendered = ", ".join(str(path.relative_to(plugin_root)) for path in nested_manifests)
        raise AssertionError(f"generated skills are nested: {rendered}")
    expected_names = source_skill_names()
    if packaged_names != expected_names:
        missing = sorted(expected_names - packaged_names)
        extra = sorted(packaged_names - expected_names)
        raise AssertionError(f"skill inventory mismatch, missing={missing}, extra={extra}")

    if archive is not None:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.namelist()
        roots = {pathlib.PurePosixPath(member).parts[0] for member in members}
        if roots != {source_manifest["name"]}:
            raise AssertionError(f"archive must contain one {source_manifest['name']!r} root")
        for member in members:
            parts = pathlib.PurePosixPath(member).parts
            if any(part in FORBIDDEN_ARCHIVE_NAMES or part.endswith(".pyc") for part in parts):
                raise AssertionError(f"archive contains forbidden file: {member}")

    print(f"OpenAI package validation passed: {len(packaged_names)} skills")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_determinism() -> None:
    with tempfile.TemporaryDirectory(prefix="adhd-focus-openai-package-") as temporary:
        temporary_root = pathlib.Path(temporary)
        archives = []
        for label in ("first", "second"):
            output = temporary_root / label / "adhd-focus"
            archive = temporary_root / label / "adhd-focus-openai.zip"
            subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    "--output",
                    str(output),
                    "--archive",
                    str(archive),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            archives.append(archive)
        if sha256(archives[0]) != sha256(archives[1]):
            raise AssertionError("two clean builds produced different ZIP archives")
    print("Deterministic build validation passed")


def main() -> None:
    args = parse_args()
    validate_package(args.plugin_path, args.archive)
    if not args.skip_determinism:
        validate_determinism()


if __name__ == "__main__":
    main()

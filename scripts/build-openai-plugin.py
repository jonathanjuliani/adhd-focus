#!/usr/bin/env python3
"""Build a deterministic, OpenAI-compatible distribution of adhd-focus."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import shutil
import zipfile

import yaml


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_MANIFEST = ROOT / "plugins" / "adhd-focus" / ".codex-plugin" / "plugin.json"
SOURCE_SKILLS = ROOT / "skills"
DEFAULT_OUTPUT = ROOT / "dist" / "openai" / "adhd-focus"
PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PORTABLE_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
)
IGNORED_NAMES = {".DS_Store", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the adhd-focus package for OpenAI import."
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help="Plugin output directory. Its final component must match the plugin name.",
    )
    parser.add_argument(
        "--archive",
        type=pathlib.Path,
        help="ZIP output path. Defaults next to the plugin directory.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Build the directory without creating a ZIP archive.",
    )
    return parser.parse_args()


def load_source_manifest() -> dict:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{SOURCE_MANIFEST.relative_to(ROOT)} must contain an object")
    return manifest


def discover_skills() -> list[tuple[str, pathlib.Path]]:
    discovered: list[tuple[str, pathlib.Path]] = []
    seen: dict[str, pathlib.Path] = {}
    for manifest_path in sorted(SOURCE_SKILLS.glob("*/SKILL.md")):
        frontmatter = load_frontmatter(manifest_path)
        name = frontmatter.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{manifest_path.relative_to(ROOT)} has no skill name")
        if name != manifest_path.parent.name:
            raise ValueError(
                f"{manifest_path.relative_to(ROOT)} names skill {name!r}, "
                f"but its directory is {manifest_path.parent.name!r}"
            )
        if name in seen:
            first = seen[name].relative_to(ROOT)
            second = manifest_path.parent.relative_to(ROOT)
            raise ValueError(f"duplicate skill name {name!r}: {first} and {second}")
        metadata = manifest_path.parent / "agents" / "openai.yaml"
        if not metadata.is_file():
            raise ValueError(f"{manifest_path.parent.relative_to(ROOT)} lacks agents/openai.yaml")
        seen[name] = manifest_path.parent
        discovered.append((name, manifest_path.parent))
    if not discovered:
        raise ValueError("no skills found under skills/<name>/SKILL.md")
    return discovered


def load_frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.relative_to(ROOT)} has no YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError(f"{path.relative_to(ROOT)} has unclosed YAML frontmatter")
    payload = yaml.safe_load(parts[1])
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(ROOT)} frontmatter must be a mapping")
    return payload


def remove_claude_only_frontmatter(path: pathlib.Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError(f"{path} has no YAML frontmatter")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        )
    except StopIteration as error:
        raise ValueError(f"{path} has unclosed YAML frontmatter") from error
    filtered = [
        line
        for index, line in enumerate(lines)
        if not (
            index < end
            and line.rstrip("\r\n") == "disable-model-invocation: true"
        )
    ]
    path.write_text("".join(filtered), encoding="utf-8")


def build_manifests(source: dict) -> tuple[dict, dict]:
    portable = {"$schema": PORTABLE_SCHEMA}
    for field in PORTABLE_FIELDS:
        if field in source:
            portable[field] = copy.deepcopy(source[field])
    interface = source.get("interface")
    if not isinstance(interface, dict):
        raise ValueError(".codex-plugin/plugin.json must contain interface metadata")
    portable["extensions"] = {"com.openai": {"interface": copy.deepcopy(interface)}}

    compatibility = copy.deepcopy(source)
    compatibility.pop("skills", None)
    return portable, compatibility


def safe_rebuild_directory(output: pathlib.Path) -> None:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError(f"refusing to replace unsafe output directory: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)


def ignored_copy_entry(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_NAMES or name.endswith(".pyc")}


def build_package(output: pathlib.Path) -> tuple[pathlib.Path, list[str]]:
    source_manifest = load_source_manifest()
    plugin_name = source_manifest.get("name")
    output = output.resolve()
    if output.name != plugin_name:
        raise ValueError(
            f"output directory must be named {plugin_name!r}, found {output.name!r}"
        )

    skills = discover_skills()
    safe_rebuild_directory(output)
    skills_output = output / "skills"
    skills_output.mkdir()

    for name, source in skills:
        destination = skills_output / name
        shutil.copytree(source, destination, ignore=ignored_copy_entry)
        remove_claude_only_frontmatter(destination / "SKILL.md")

    portable, compatibility = build_manifests(source_manifest)
    (output / "plugin.json").write_text(
        json.dumps(portable, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    compatibility_dir = output / ".codex-plugin"
    compatibility_dir.mkdir()
    (compatibility_dir / "plugin.json").write_text(
        json.dumps(compatibility, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output, [name for name, _source in skills]


def write_deterministic_zip(plugin_root: pathlib.Path, archive: pathlib.Path) -> pathlib.Path:
    plugin_root = plugin_root.resolve()
    archive = archive.resolve()
    try:
        archive.relative_to(plugin_root)
    except ValueError:
        pass
    else:
        raise ValueError("archive must be outside the generated plugin directory")
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(
        archive,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as bundle:
        for path in sorted(plugin_root.rglob("*")):
            if not path.is_file():
                continue
            relative = pathlib.PurePosixPath(plugin_root.name) / path.relative_to(plugin_root)
            info = zipfile.ZipInfo(str(relative), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    return archive


def main() -> None:
    args = parse_args()
    output, skills = build_package(args.output)
    print(f"Built OpenAI plugin: {output}")
    print(f"Skills: {len(skills)}")
    if not args.no_archive:
        archive = args.archive or output.parent / f"{output.name}-openai.zip"
        archive = write_deterministic_zip(output, archive)
        print(f"Archive: {archive}")


if __name__ == "__main__":
    main()

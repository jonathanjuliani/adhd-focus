#!/usr/bin/env python3
"""Build the Manus .skill archive for adhd-focus.

Reads the canonical skill folder and writes dist/manus/adhd-focus.skill.
Does not edit that folder, the plugin manifests, or the OpenAI package.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import tempfile
import zipfile

import yaml


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_SKILLS = ROOT / "skills"
DEFAULT_OUTPUT = ROOT / "dist" / "manus"
IGNORED_NAMES = {".DS_Store", "__pycache__", "agents"}
HOST_BLOCK = """## On Manus

Keep this shape on every later turn until the reader says "stop adhd mode" or "normal mode". If this host drops the skill after one turn, say that in the first reply and tell the reader to start the next message with `/adhd-focus`.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Manus archive for adhd-focus.")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help="Directory for adhd-focus.skill.",
    )
    return parser.parse_args()


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
        seen[name] = manifest_path.parent
        discovered.append((name, manifest_path.parent))
    if not discovered:
        raise ValueError("no skills found under skills/<name>/SKILL.md")
    return discovered


def insert_host_block(text: str) -> str:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md has no YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError("SKILL.md has unclosed YAML frontmatter")
    body = parts[2][1:] if parts[2].startswith("\n") else parts[2]
    return f"---\n{parts[1]}---\n\n{HOST_BLOCK.strip()}\n\n{body}"


def ignored_copy_entry(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_NAMES or name.endswith(".pyc")}


def safe_rebuild_directory(output: pathlib.Path) -> None:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError(f"refusing to replace unsafe output directory: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)


def write_deterministic_zip(source: pathlib.Path, archive: pathlib.Path, root_name: str) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(
        archive,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as bundle:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = pathlib.PurePosixPath(root_name) / path.relative_to(source)
            info = zipfile.ZipInfo(str(relative), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def build_archives(output: pathlib.Path) -> list[pathlib.Path]:
    skills = discover_skills()
    safe_rebuild_directory(output)
    archives: list[pathlib.Path] = []
    with tempfile.TemporaryDirectory(prefix="adhd-focus-manus-") as temporary:
        temporary_root = pathlib.Path(temporary)
        for name, source in skills:
            destination = temporary_root / name
            shutil.copytree(source, destination, ignore=ignored_copy_entry)
            manifest = destination / "SKILL.md"
            rewritten = insert_host_block(manifest.read_text(encoding="utf-8"))
            if "Call the Skill tool with" in rewritten:
                raise ValueError("adhd-focus tells Manus to call the Skill tool")
            manifest.write_text(rewritten, encoding="utf-8")
            archive = output / f"{name}.skill"
            write_deterministic_zip(destination, archive, name)
            archives.append(archive)
    return archives


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    archives = build_archives(output)
    print(f"Built Manus skills: {output}")
    print(f"Skills: {len(archives)}")


if __name__ == "__main__":
    main()

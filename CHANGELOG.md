# Changelog

All notable changes to adhd-focus are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Add each change under **Unreleased** as you make it; `python3 scripts/version.py` moves them under the new version when you release.

## [Unreleased]

### Fixed

- The marketplace check passes `skilldeck_ref: v1.0.0`. The called workflow's default ref is this repository's commit, which skilldeck does not contain.

## [0.1.0] - 2026-10-16

### Added

- `adhd-focus`, a session-long output style for a reader with ADHD. Lean by default, with a structured breakdown from `breakdown.md` only when asked. Adapted from `ayghri/i-have-adhd` (MIT).

[Unreleased]: https://github.com/jonathanjuliani/adhd-focus/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jonathanjuliani/adhd-focus/releases/tag/v0.1.0

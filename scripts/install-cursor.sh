#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HOME}/.cursor/plugins/local/adhd-focus"

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to copy the plugin into ~/.cursor/plugins/local" >&2
  exit 1
fi

echo "==> adhd-focus Cursor local installer"
echo "Repo: ${REPO_ROOT}"
echo "Dest: ${DEST}"
echo

mkdir -p "${HOME}/.cursor/plugins/local"

# Cursor skips a symlink whose target is outside ~/.cursor/plugins/local.
# Replace any existing dest (symlink, copy, or stale clone) with a real copy.
if [[ -e "${DEST}" || -L "${DEST}" ]]; then
  rm -rf "${DEST}"
  echo "Removed existing ${DEST}"
fi

mkdir -p "${DEST}"
rsync -a --delete --copy-links "${REPO_ROOT}/plugins/adhd-focus/" "${DEST}/"

echo "Cursor: copied plugin to ${DEST}"
echo "  → Fully quit Cursor (Cmd+Q) and reopen, or Developer: Reload Window"
echo "  → Enable Include third-party Plugins, Skills, and other configs"
echo "  → Confirm adhd-focus under Customize → Skills"
echo "  → Then run /adhd-focus:adhd-focus (or /adhd-focus if not namespaced)"
echo
echo "Re-run this script after you change the plugin locally."

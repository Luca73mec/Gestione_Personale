#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$ROOT_DIR/VERSION"
MANIFEST_FILE="$ROOT_DIR/PROJECT_MANIFEST.md"

cd "$ROOT_DIR"
git rev-parse --is-inside-work-tree >/dev/null

[[ -f "$VERSION_FILE" ]] || { echo "Missing VERSION" >&2; exit 1; }
[[ -f "$MANIFEST_FILE" ]] || { echo "Missing PROJECT_MANIFEST.md" >&2; exit 1; }

version="$(tr -d '[:space:]' < "$VERSION_FILE")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "VERSION must use MAJOR.MINOR.PATCH" >&2
  exit 1
}

IFS=. read -r major minor patch <<< "$version"
next_version="$major.$minor.$((patch + 1))"
printf '%s\n' "$next_version" > "$VERSION_FILE"

python3 - "$MANIFEST_FILE" "$next_version" <<'PY'
from datetime import datetime
from pathlib import Path
import re
import sys

manifest = Path(sys.argv[1])
version = sys.argv[2]
text = manifest.read_text(encoding="utf-8")
timestamp = datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")
text, version_count = re.subn(
    r"(?m)^Versione corrente:.*$",
    f"Versione corrente: `{version}`",
    text,
    count=1,
)
text, timestamp_count = re.subn(
    r"(?m)^\d{4}-\d{2}-\d{2} .*?$",
    timestamp,
    text,
    count=1,
)
if version_count != 1 or timestamp_count != 1:
    raise SystemExit("PROJECT_MANIFEST.md has an unexpected format")
manifest.write_text(text, encoding="utf-8")
PY

git add -A
git diff --cached --name-only | grep -Fxq VERSION || {
  echo "VERSION is not staged; refusing to commit" >&2
  exit 1
}
git commit -m "Update version to $next_version"
git push -u origin HEAD
git tag -a "v$next_version" -m "Release v$next_version"
git push origin "v$next_version"
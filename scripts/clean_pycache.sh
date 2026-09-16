#!/usr/bin/env bash
# Remove Python bytecode caches from the repo working tree.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

while IFS= read -r -d '' dir; do
  rm -rf "$dir"
done < <(find . -type d -name '__pycache__' -not -path './.git/*' -print0 2>/dev/null || true)

while IFS= read -r -d '' file; do
  rm -f "$file"
done < <(find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -not -path './.git/*' -print0 2>/dev/null || true)

while IFS= read -r -d '' dir; do
  rm -rf "$dir"
done < <(find . -type d -name '.pytest_cache' -not -path './.git/*' -print0 2>/dev/null || true)

echo "cleared Python caches under $ROOT"

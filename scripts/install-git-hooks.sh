#!/usr/bin/env bash
# Point this repo at tracked hooks in .githooks/ (includes pycache cleanup).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x .githooks/pre-commit scripts/clean_pycache.sh
git config core.hooksPath .githooks

echo "Installed git hooks from .githooks/ (core.hooksPath=.githooks)"

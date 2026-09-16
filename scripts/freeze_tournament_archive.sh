#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_SLUG="${WCO_ARCHIVE_SLUG:-wc2026}"
SOURCE_DIR="$ROOT/data/processed"
TARGET_DIR="$ROOT/data/archive/${ARCHIVE_SLUG}"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "processed dataset not found: $SOURCE_DIR" >&2
  exit 1
fi

cd "$ROOT/apps/api"
if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
elif [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

python -m app.services.time_machine_generator --require-complete

mkdir -p "$TARGET_DIR"
rsync -a --delete \
  --exclude '__pycache__/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

python - <<'PY'
from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.core.archive_config import ARCHIVE_BANK_FILENAME, ARCHIVE_MANIFEST_FILENAME
from app.services.runtime_store import get_active_forecast_bank_path, init_runtime_store

root = Path(__file__).resolve().parents[3]
archive_slug = __import__("os").environ.get("WCO_ARCHIVE_SLUG", "wc2026")
target_dir = root / "data" / "archive" / archive_slug
target_dir.mkdir(parents=True, exist_ok=True)

init_runtime_store()
bank_path = get_active_forecast_bank_path()
if bank_path is not None and bank_path.exists():
    shutil.copy2(bank_path, target_dir / ARCHIVE_BANK_FILENAME)
    print(f"copied simulation bank to {target_dir / ARCHIVE_BANK_FILENAME}")
else:
    print("no active runtime bank found; archive will use forecast snapshot sidecars only")

manifest = {
    "archive_slug": archive_slug,
    "frozen_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
    "label": "Dataset frozen — Final, July 2026",
    "source_processed_dir": str(root / "data" / "processed"),
    "includes": [
        "fixtures.json",
        "results.json",
        "metadata.json",
        "forecast_snapshot.json",
        "probability_history.json",
        "team_paths.json",
        ARCHIVE_BANK_FILENAME,
        "time_machine/manifest.json",
        "time_machine/milestones/*/snapshot.json",
        "time_machine/milestones/*/team_paths.json",
        "time_machine/milestones/*/bank.npz",
    ],
}
manifest_path = target_dir / ARCHIVE_MANIFEST_FILENAME
manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"wrote archive manifest to {manifest_path}")
PY

echo "frozen archive available at $TARGET_DIR"
echo "set WCO_ARCHIVE_MODE=${ARCHIVE_SLUG} to serve the frozen dataset"

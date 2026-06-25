#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/apps/api"

if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
elif [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

python - <<'PY'
from pathlib import Path
import json

from app.services.forecast_snapshot_service import build_forecast_snapshot

snapshot = build_forecast_snapshot("processed")
target = Path("../../data/processed/forecast_snapshot.json").resolve()
target.write_text(
    json.dumps(snapshot.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"wrote bootstrap forecast snapshot to {target}")
PY

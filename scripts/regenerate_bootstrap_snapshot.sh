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

export WCO_SNAPSHOT_SIMULATIONS="${WCO_SNAPSHOT_SIMULATIONS:-5000}"

python - <<'PY'
from pathlib import Path
import json

from app.core.config import DEFAULT_MODEL_TYPE
from app.services.data_loader import load_metadata
from app.services.forecast_snapshot_service import build_forecast_snapshot_from_bank
from app.services.simulation_bank_service import build_simulation_bank

metadata = load_metadata("processed")
bank_path, bank_meta = build_simulation_bank(
    data_mode="processed",
    model_type=DEFAULT_MODEL_TYPE,
    data_version=metadata.get("data_version"),
)
snapshot = build_forecast_snapshot_from_bank(bank_path, bank_meta, "processed")
target = Path("../../data/processed/forecast_snapshot.json").resolve()
target.write_text(
    json.dumps(snapshot.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"wrote bootstrap forecast snapshot to {target}")
PY

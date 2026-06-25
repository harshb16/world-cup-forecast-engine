"""Application configuration values."""

import os
from pathlib import Path
from typing import Literal

API_TITLE = "World Cup Oracle API"
DEFAULT_MODEL_TYPE = "calibrated_elo"

REPO_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PROCESSED_DIR = REPO_ROOT / "data" / "processed"

DataMode = Literal["sample", "processed"]


def get_data_mode() -> DataMode:
    """Return configured tournament data mode."""
    value = os.getenv("WORLD_CUP_DATA_MODE", "processed")
    if value not in {"sample", "processed"}:
        raise ValueError("WORLD_CUP_DATA_MODE must be sample or processed")
    return value  # type: ignore[return-value]


def get_runtime_data_dir() -> Path:
    """Return writable runtime storage root."""
    configured = os.getenv("WCO_RUNTIME_DATA_DIR")
    root = Path(configured) if configured else REPO_ROOT / "data" / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root

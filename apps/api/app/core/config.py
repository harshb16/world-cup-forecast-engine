"""Application configuration values."""

import os
from typing import Literal

API_TITLE = "World Cup Oracle API"
DEFAULT_MODEL_TYPE = "calibrated_elo"

DataMode = Literal["sample", "processed"]


def get_data_mode() -> DataMode:
    """Return configured tournament data mode."""
    value = os.getenv("WORLD_CUP_DATA_MODE", "processed")
    if value not in {"sample", "processed"}:
        raise ValueError("WORLD_CUP_DATA_MODE must be sample or processed")
    return value  # type: ignore[return-value]

"""Frozen tournament archive mode configuration."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.config import REPO_ROOT

ARCHIVE_ROOT = REPO_ROOT / "data" / "archive"
SUPPORTED_ARCHIVE_DIRS: dict[str, Path] = {
    "wc2026": ARCHIVE_ROOT / "wc2026",
}
ARCHIVE_BANK_FILENAME = "simulation_bank.npz"
ARCHIVE_MANIFEST_FILENAME = "archive_manifest.json"
FROZEN_LABELS = {
    "wc2026": "Dataset frozen — Final, July 2026",
}


def get_archive_mode() -> str | None:
    """Return active archive slug when WCO_ARCHIVE_MODE is set."""
    value = os.getenv("WCO_ARCHIVE_MODE")
    if not value:
        return None
    if value not in SUPPORTED_ARCHIVE_DIRS:
        raise ValueError(f"unsupported WCO_ARCHIVE_MODE: {value}")
    return value


def is_archive_mode_active() -> bool:
    """Return True when the API should serve a frozen archive dataset."""
    return get_archive_mode() is not None


def get_archive_data_dir() -> Path | None:
    """Return frozen dataset directory when archive mode is active."""
    mode = get_archive_mode()
    if mode is None:
        return None
    archive_dir = SUPPORTED_ARCHIVE_DIRS[mode]
    if not archive_dir.exists():
        raise FileNotFoundError(
            f"archive dataset not found for WCO_ARCHIVE_MODE={mode}: {archive_dir}"
        )
    return archive_dir


def get_frozen_label(mode: str | None = None) -> str | None:
    """Return human-readable frozen badge copy for one archive slug."""
    slug = mode or get_archive_mode()
    if slug is None:
        return None
    return FROZEN_LABELS.get(slug)


def archive_metadata_fields() -> dict[str, object]:
    """Metadata fields exposed to clients when archive mode is active."""
    mode = get_archive_mode()
    if mode is None:
        return {
            "archive_mode": None,
            "is_frozen": False,
            "frozen_label": None,
        }
    return {
        "archive_mode": mode,
        "is_frozen": True,
        "frozen_label": get_frozen_label(mode),
    }


def resolve_archive_bank_path() -> Path | None:
    """Return simulation bank path bundled with a frozen archive."""
    archive_dir = get_archive_data_dir()
    if archive_dir is None:
        return None
    bank_path = archive_dir / ARCHIVE_BANK_FILENAME
    return bank_path if bank_path.exists() else None

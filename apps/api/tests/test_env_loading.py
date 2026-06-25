"""Tests for local dotenv loading."""

from __future__ import annotations

from pathlib import Path

from app.core import env as env_module


def test_load_local_env_reads_file_without_overriding_existing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "WCO_ADMIN_SYNC_KEY=file-key\n"
        "FOOTBALL_DATA_API_TOKEN=file-token\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(env_module, "ENV_FILE_CANDIDATES", (env_file,))
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "existing-key")
    monkeypatch.delenv("FOOTBALL_DATA_API_TOKEN", raising=False)

    env_module.load_local_env()

    import os

    assert os.environ["WCO_ADMIN_SYNC_KEY"] == "existing-key"
    assert os.environ["FOOTBALL_DATA_API_TOKEN"] == "file-token"

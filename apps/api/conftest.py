"""Pytest hooks shared across the API test suite."""

from __future__ import annotations

import subprocess
from pathlib import Path


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "slow: long-running performance tests")


def pytest_sessionstart(session) -> None:
    """Clear stale bytecode caches before every test run."""
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "clean_pycache.sh"
    if script.exists():
        subprocess.run(["bash", str(script)], check=False, cwd=repo_root)

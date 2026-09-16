"""Pytest hooks shared across the API test suite."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "slow: long-running performance tests")


def pytest_sessionstart(session) -> None:
    """Clear caches and isolate mutable runtime state for every test run."""
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "clean_pycache.sh"
    if script.exists():
        subprocess.run(["bash", str(script)], check=False, cwd=repo_root)
    runtime_root = Path(tempfile.mkdtemp(prefix="wco-pytest-runtime-"))
    session.config._wco_runtime_root = runtime_root
    session.config._wco_previous_runtime = os.environ.get("WCO_RUNTIME_DATA_DIR")
    os.environ["WCO_RUNTIME_DATA_DIR"] = str(runtime_root)


def pytest_sessionfinish(session, exitstatus) -> None:
    """Remove the isolated runtime directory and restore the caller environment."""
    runtime_root = getattr(session.config, "_wco_runtime_root", None)
    if runtime_root is not None:
        shutil.rmtree(runtime_root, ignore_errors=True)
    previous = getattr(session.config, "_wco_previous_runtime", None)
    if previous is None:
        os.environ.pop("WCO_RUNTIME_DATA_DIR", None)
    else:
        os.environ["WCO_RUNTIME_DATA_DIR"] = previous

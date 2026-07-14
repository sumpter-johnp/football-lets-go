"""Shared env loading for the ingest layer.

Reads KEY=value lines from the repo-root .env (and falls back to
sideline-phase0/.env, where the CFBD key already lives). Real environment
variables always win. No python-dotenv dependency.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILES = [REPO_ROOT / ".env", REPO_ROOT / "sideline-phase0" / ".env"]


def load_env() -> None:
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))

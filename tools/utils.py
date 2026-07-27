"""Shared utilities for WAT framework tools."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env", override=True)


def get_env(key: str) -> str:
    """Return an env var or raise RuntimeError with a clear message."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"{key} is not set in .env")
    return value


def tmp_path(filename: str) -> Path:
    """Return a path inside .tmp/, creating the directory if needed."""
    path = ROOT / ".tmp" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

"""Configuration and storage path resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

DEFAULT_FILE_NAME = os.getenv("TASK_FILE_PATH", "tasks.json")


def get_file_path(custom_path: Optional[str] = None) -> Path:
    """Resolve the storage path and ensure the parent directory exists."""
    target = Path(custom_path or DEFAULT_FILE_NAME)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    return target

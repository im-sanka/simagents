from __future__ import annotations

from datetime import datetime
from pathlib import Path


def create_run_dir(base_dir: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path(base_dir) / f"run-{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_text(path: Path, filename: str, content: str) -> Path:
    filepath = path / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath

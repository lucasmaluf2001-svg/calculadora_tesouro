from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def resource_root() -> Path:
    """Raiz dos arquivos empacotados pelo PyInstaller ou do projeto em desenvolvimento."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def runtime_data_dir() -> Path:
    """Pasta gravável para o snapshot atualizado."""
    explicit = os.getenv("CARTEIRA_DATA_DIR")
    if explicit:
        path = Path(explicit).expanduser().resolve()
    elif getattr(sys, "frozen", False):
        base = Path(os.getenv("LOCALAPPDATA", Path.home()))
        path = base / "CarteiraTesouro"
    else:
        path = resource_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def static_html_path() -> Path:
    return resource_root() / "app" / "static" / "index.html"


def packaged_base_snapshot_path() -> Path:
    return resource_root() / "data" / "snapshot_base.json"


def packaged_seed_snapshot_path() -> Path:
    path = resource_root() / "data" / "snapshot_seed.json"
    return path if path.exists() else packaged_base_snapshot_path()


def runtime_snapshot_path() -> Path:
    return runtime_data_dir() / "snapshot.json"


def ensure_runtime_snapshot() -> Path:
    target = runtime_snapshot_path()
    if not target.exists():
        shutil.copy2(packaged_seed_snapshot_path(), target)
    return target

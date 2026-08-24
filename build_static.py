from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "app" / "static"
SNAPSHOT_PATH = ROOT / "data" / "snapshot.json"
OUTPUT_DIR = ROOT / "public"


def validate_snapshot(path: Path) -> None:
    with path.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    missing = {"asof", "titles", "vna"}.difference(snapshot)
    if missing:
        raise ValueError(f"Snapshot sem campos obrigatórios: {sorted(missing)}")
    if not snapshot["titles"] or not snapshot["vna"]:
        raise ValueError("Snapshot sem dados para publicação.")


def build_static_site() -> Path:
    validate_snapshot(SNAPSHOT_PATH)

    # dirs_exist_ok evita falhas do OneDrive ao tentar remover e recriar a
    # pasta inteira. Os arquivos publicados são sobrescritos de forma idempotente.
    shutil.copytree(STATIC_DIR, OUTPUT_DIR, dirs_exist_ok=True)
    shutil.copy2(SNAPSHOT_PATH, OUTPUT_DIR / "calc_snapshot2.json")
    return OUTPUT_DIR


if __name__ == "__main__":
    output = build_static_site()
    print(f"Site estático gerado em {output}")

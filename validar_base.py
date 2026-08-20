from __future__ import annotations

import json
from pathlib import Path

from app.paths import packaged_base_snapshot_path
from app.services.snapshot import build_snapshot
from app.services.tesouro import download_tesouro


def main():
    with packaged_base_snapshot_path().open("r", encoding="utf-8") as f:
        expected = json.load(f)

    tesouro = download_tesouro()
    rebuilt = build_snapshot(
        tesouro,
        base_snapshot=expected,
        cutoff="25/06/2026",
        extend_vna=False,
    )

    errors = []
    if rebuilt["asof"] != expected["asof"]:
        errors.append(("asof", expected["asof"], rebuilt["asof"]))

    for i, (a, b) in enumerate(zip(expected["titles"], rebuilt["titles"])):
        for field in ("taxa", "pu", "hist"):
            if a[field] != b[field]:
                errors.append((f"titles[{i}].{field}", a[field], b[field]))

    if errors:
        print(f"FALHOU: {len(errors)} diferenças encontradas.")
        for item in errors[:20]:
            print(item[0])
        raise SystemExit(1)

    print("OK: títulos, taxas, PUs e históricos mensais de 25/06/2026 reproduzidos exatamente.")


if __name__ == "__main__":
    main()

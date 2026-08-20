from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd

from app.paths import (
    ensure_runtime_snapshot,
    packaged_base_snapshot_path,
    runtime_snapshot_path,
)
from app.services.tesouro import KIND_TO_TIPO, download_tesouro
from app.services.vna import download_official_vna, extend_compatible_vna


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _source_rows(
    df: pd.DataFrame,
    title: dict,
    cutoff: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    tipo = KIND_TO_TIPO[title["kind"]]
    venc = pd.to_datetime(title["venc"], dayfirst=True)
    rows = df[
        (df["Tipo Titulo"] == tipo)
        & (df["Data Vencimento"] == venc)
    ].copy()

    if cutoff is not None:
        rows = rows[rows["Data Base"] <= cutoff]

    return rows.sort_values("Data Base")


def rebuild_titles(
    base_snapshot: dict,
    tesouro_df: pd.DataFrame,
    cutoff: Optional[pd.Timestamp] = None,
) -> list[dict]:
    """
    Recria exatamente os campos de mercado usados pelo HTML:
    taxa, PU e histórico mensal. Metadados/fluxos do protótipo são mantidos.
    """
    result = []
    for base_title in base_snapshot["titles"]:
        title = copy.deepcopy(base_title)
        rows = _source_rows(tesouro_df, title, cutoff=cutoff)

        if rows.empty:
            raise ValueError(
                f"Tesouro não retornou dados para {title['nome']} "
                f"({title['venc']})."
            )

        last = rows.iloc[-1]
        title["taxa"] = float(last["Taxa Venda Manha"])
        title["pu"] = float(last["PU Venda Manha"])

        monthly = rows.copy()
        monthly["ym"] = monthly["Data Base"].dt.strftime("%Y-%m")
        monthly = monthly.groupby("ym", sort=True).tail(1)

        title["hist"] = [
            [ym, float(rate), float(pu)]
            for ym, rate, pu in monthly[
                ["ym", "Taxa Venda Manha", "PU Venda Manha"]
            ].itertuples(index=False, name=None)
        ]
        result.append(title)

    return result


def _rebuild_precurve(base_snapshot: dict, titles: list[dict]) -> list[list]:
    # O campo não é utilizado pelo HTML atual. Mantemos os mesmos vértices do
    # protótipo e atualizamos somente as taxas a partir dos títulos correspondentes.
    points = []
    for x, old_rate in base_snapshot.get("precurve", []):
        matches = [t for t in titles if abs(float(t.get("t_venc", -999)) - float(x)) < 1e-5]
        if matches:
            # Quando há mais de um título no mesmo vértice, preserva a preferência
            # implícita no snapshot base comparando a taxa antiga.
            chosen = min(matches, key=lambda t: abs(float(t["taxa"]) - float(old_rate)))
            points.append([x, float(chosen["taxa"])])
        else:
            points.append([x, old_rate])
    return points


def build_snapshot(
    tesouro_df: pd.DataFrame,
    base_snapshot: Optional[dict] = None,
    cutoff: Optional[str] = None,
    extend_vna: bool = False,
    official_vna_df: Optional[pd.DataFrame] = None,
) -> dict:
    base = copy.deepcopy(
        base_snapshot if base_snapshot is not None
        else load_json(packaged_base_snapshot_path())
    )

    cutoff_ts = pd.to_datetime(cutoff, dayfirst=True) if cutoff else None
    titles = rebuild_titles(base, tesouro_df, cutoff=cutoff_ts)
    base["titles"] = titles
    base["precurve"] = _rebuild_precurve(base, titles)

    if cutoff_ts is not None:
        asof_ts = cutoff_ts
    else:
        asof_ts = tesouro_df["Data Base"].max()

    base["asof"] = asof_ts.strftime("%d/%m/%Y")

    if extend_vna:
        official = official_vna_df
        if official is None:
            official = download_official_vna()
        base["vna"] = extend_compatible_vna(base["vna"], official)

    return base


def validate_snapshot(snapshot: dict) -> None:
    required = {"asof", "titles", "vna"}
    missing = required.difference(snapshot)
    if missing:
        raise ValueError(f"Snapshot sem campos obrigatórios: {sorted(missing)}")
    if not snapshot["titles"]:
        raise ValueError("Snapshot sem títulos.")
    if not snapshot["vna"]:
        raise ValueError("Snapshot sem série VNA.")


def atomic_write_json(snapshot: dict, target: Path) -> None:
    validate_snapshot(snapshot)
    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix="snapshot_", suffix=".json", dir=target.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def update_runtime_snapshot() -> dict:
    """
    Atualiza usando fontes oficiais.
    Se ocorrer erro, a camada HTTP continua servindo o último snapshot válido.
    """
    ensure_runtime_snapshot()
    tesouro_df = download_tesouro()
    base = load_json(packaged_base_snapshot_path())

    # VNA é estendido sem reescrever o histórico do protótipo.
    try:
        official_vna = download_official_vna()
        snapshot = build_snapshot(
            tesouro_df,
            base_snapshot=base,
            extend_vna=True,
            official_vna_df=official_vna,
        )
    except Exception:
        # Não impede a atualização dos preços/taxas se a publicação mensal
        # de VNA estiver temporariamente indisponível.
        snapshot = build_snapshot(
            tesouro_df,
            base_snapshot=base,
            extend_vna=False,
        )

    atomic_write_json(snapshot, runtime_snapshot_path())
    return snapshot

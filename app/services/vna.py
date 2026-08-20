from __future__ import annotations

from io import BytesIO
import re

import pandas as pd
import requests


VNA_PUBLICATION_PAGE = (
    "https://www.tesourotransparente.gov.br/publicacoes/valor-nominal-de-ntn-b"
)


def discover_vna_xlsx_url(timeout: int = 30) -> str:
    response = requests.get(
        VNA_PUBLICATION_PAGE,
        timeout=timeout,
        headers={"User-Agent": "CarteiraTesouro/1.0"},
    )
    response.raise_for_status()

    match = re.search(
        r'https?://thot-arquivos\.tesouro\.gov\.br/publicacao/\d+',
        response.text,
    )
    if not match:
        raise ValueError("Não foi possível localizar o XLSX de VNA na página oficial.")
    return match.group(0)


def download_official_vna(timeout: int = 30) -> pd.DataFrame:
    xlsx_url = discover_vna_xlsx_url(timeout=timeout)
    response = requests.get(
        xlsx_url,
        timeout=timeout,
        headers={"User-Agent": "CarteiraTesouro/1.0"},
    )
    response.raise_for_status()
    raw = pd.read_excel(BytesIO(response.content), sheet_name="NTNB", header=None)
    if raw.shape[1] < 2:
        raise ValueError("Planilha de VNA do Tesouro com formato inesperado.")

    rows = raw.iloc[10:, [0, 1]].copy()
    rows.columns = ["date", "vna"]
    rows = rows.dropna()
    rows["date"] = pd.to_datetime(rows["date"], errors="coerce")
    rows["vna"] = pd.to_numeric(rows["vna"], errors="coerce")
    rows = rows.dropna().sort_values("date")
    rows["ym"] = rows["date"].dt.strftime("%Y-%m")
    return rows[["ym", "vna"]]


def extend_compatible_vna(
    baseline_vna: list[list],
    official_vna: pd.DataFrame,
) -> list[list]:
    """
    Mantém integralmente o histórico usado pelo HTML original e apenas o estende.

    O JSON do Claude não usa a mesma escala absoluta da publicação mensal oficial
    do Tesouro. Como o HTML utiliza VNA somente por razão (VNA_t / VNA_0),
    normalizamos os novos pontos oficiais pelo último mês comum. Assim:
    - nenhum resultado histórico do protótipo é reescrito;
    - a série fica contínua;
    - as variações futuras passam a seguir a série oficial do Tesouro.

    Nenhum ponto histórico existente é alterado.
    """
    if not baseline_vna:
        raise ValueError("Snapshot base sem VNA.")

    out = [list(x) for x in baseline_vna]
    last_ym, last_value = out[-1]
    lookup = dict(official_vna.itertuples(index=False, name=None))

    if last_ym not in lookup:
        raise ValueError(
            f"VNA oficial não contém o mês de calibração {last_ym}."
        )

    official_anchor = float(lookup[last_ym])
    if official_anchor <= 0:
        raise ValueError("VNA oficial de calibração inválido.")

    scale = float(last_value) / official_anchor

    for ym, value in official_vna.itertuples(index=False, name=None):
        if ym > last_ym:
            out.append([ym, round(float(value) * scale, 2)])

    return out

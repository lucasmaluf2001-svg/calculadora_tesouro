from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd
import requests


TESOURO_CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

KIND_TO_TIPO = {
    "ntnb_princ": "Tesouro IPCA+",
    "ntnb": "Tesouro IPCA+ com Juros Semestrais",
    "ltn": "Tesouro Prefixado",
    "ntnf": "Tesouro Prefixado com Juros Semestrais",
}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "Tipo Titulo",
        "Data Vencimento",
        "Data Base",
        "Taxa Venda Manha",
        "PU Venda Manha",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"CSV do Tesouro sem colunas esperadas: {sorted(missing)}")

    out = df.copy()
    out["Data Base"] = pd.to_datetime(out["Data Base"], dayfirst=True, errors="raise")
    out["Data Vencimento"] = pd.to_datetime(
        out["Data Vencimento"], dayfirst=True, errors="raise"
    )
    return out


def parse_tesouro_csv_bytes(content: bytes) -> pd.DataFrame:
    # O arquivo oficial é separado por ';' e usa vírgula decimal.
    # latin-1 mantém compatibilidade com o arquivo histórico do portal.
    df = pd.read_csv(BytesIO(content), sep=";", decimal=",", encoding="latin1")
    return _normalize(df)


def load_tesouro_csv(path: Union[str, Path]) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", decimal=",", encoding="latin1")
    return _normalize(df)


def download_tesouro(timeout: int = 45) -> pd.DataFrame:
    response = requests.get(
        TESOURO_CSV_URL,
        timeout=timeout,
        headers={"User-Agent": "CarteiraTesouro/1.0"},
    )
    response.raise_for_status()
    return parse_tesouro_csv_bytes(response.content)

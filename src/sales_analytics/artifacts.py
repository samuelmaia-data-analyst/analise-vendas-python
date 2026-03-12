from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data_contract import REQUIRED_RAW_COLUMNS


def generate_processed_artifacts(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    missing = sorted(REQUIRED_RAW_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Dados de entrada sem colunas obrigatorias: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = df.copy()
    tmp["ORDERDATE"] = pd.to_datetime(tmp["ORDERDATE"], errors="coerce")

    fato = tmp[
        [
            "ORDERNUMBER",
            "ORDERLINENUMBER",
            "QUANTITYORDERED",
            "PRICEEACH",
            "SALES",
            "STATUS",
            "DEALSIZE",
        ]
    ].copy()

    dim_tempo = (
        tmp[["ORDERDATE"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"ORDERDATE": "DATA"})
        .sort_values("DATA")
        .reset_index(drop=True)
    )
    dim_tempo["DATE_ID"] = range(1, len(dim_tempo) + 1)
    dim_tempo["ANO"] = dim_tempo["DATA"].dt.year
    dim_tempo["MES"] = dim_tempo["DATA"].dt.month
    dim_tempo["MES_NOME"] = dim_tempo["DATA"].dt.strftime("%B")

    arquivos = [
        output_dir / "fato_vendas.csv",
        output_dir / "dim_tempo.csv",
    ]
    fato.to_csv(arquivos[0], index=False, encoding="utf-8")
    dim_tempo.to_csv(arquivos[1], index=False, encoding="utf-8")
    return arquivos

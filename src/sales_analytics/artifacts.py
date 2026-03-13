from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data_contract import REQUIRED_RAW_COLUMNS
from .logging_utils import get_logger
from .quality import validate_sales_data
from .transformations import prepare_sales_data

LOGGER = get_logger(__name__)


def generate_processed_artifacts(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    quality_report = validate_sales_data(
        df,
        date_col="ORDERDATE",
        sales_col="SALES",
        required_columns=REQUIRED_RAW_COLUMNS,
    )
    if quality_report.missing_required_columns:
        missing = ", ".join(quality_report.missing_required_columns)
        raise ValueError(f"Dados de entrada sem colunas obrigatorias: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Gerando artefatos processados em %s", output_dir)
    tmp = prepare_sales_data(
        df,
        date_col="ORDERDATE",
        sales_col="SALES",
        quality_report=quality_report,
    ).rename(columns={"analysis_date": "ORDERDATE", "analysis_sales": "SALES"})

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
    LOGGER.info("Artefatos gerados: %s", ", ".join(str(path.name) for path in arquivos))
    return arquivos

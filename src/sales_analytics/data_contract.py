from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import get_project_paths

REQUIRED_RAW_COLUMNS = {
    "ORDERNUMBER",
    "ORDERDATE",
    "SALES",
    "PRODUCTLINE",
    "CUSTOMERNAME",
    "COUNTRY",
}

REQUIRED_ARTIFACT_COLUMNS = {
    "fato_vendas.csv": {"ORDERNUMBER", "ORDERLINENUMBER", "QUANTITYORDERED", "PRICEEACH", "SALES"},
    "dim_tempo.csv": {"DATE_ID", "DATA", "ANO", "MES", "MES_NOME"},
}


def resolve_first_existing_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Nenhum arquivo encontrado nos caminhos esperados: {checked}")


def load_raw_sales(path: Path | None = None) -> pd.DataFrame:
    if path is not None:
        csv_path = path
    else:
        paths = get_project_paths()
        csv_path = resolve_first_existing_path(
            paths.raw_data_dir / "sales_data_sample.csv",
            paths.legacy_raw_data_dir / "sales_data_sample.csv",
        )
    return pd.read_csv(csv_path, encoding="latin-1")


def validate_raw_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    missing = sorted(REQUIRED_RAW_COLUMNS - set(df.columns))
    return len(missing) == 0, missing


def validate_processed_schema(file_name: str, df: pd.DataFrame) -> tuple[bool, list[str]]:
    expected = REQUIRED_ARTIFACT_COLUMNS.get(file_name)
    if expected is None:
        raise ValueError(f"Artefato sem contrato registrado: {file_name}")
    missing = sorted(expected - set(df.columns))
    return len(missing) == 0, missing

from __future__ import annotations

import pandas as pd

from .exceptions import DataQualityError
from .quality import DataQualityReport


def prepare_sales_data(
    df: pd.DataFrame,
    *,
    date_col: str,
    sales_col: str,
    quality_report: DataQualityReport | None = None,
) -> pd.DataFrame:
    report = quality_report
    if report is not None and not report.is_valid:
        missing = ", ".join(report.missing_required_columns)
        if missing:
            raise DataQualityError(f"Colunas obrigatorias ausentes: {missing}")
        raise DataQualityError("Nao ha linhas validas para analise.")

    cleaned = df.copy()
    cleaned[date_col] = pd.to_datetime(cleaned[date_col], errors="coerce")
    cleaned[sales_col] = pd.to_numeric(cleaned[sales_col], errors="coerce")
    cleaned = cleaned.dropna(subset=[date_col, sales_col])
    cleaned = cleaned.loc[cleaned[sales_col] >= 0].copy()

    if cleaned.empty:
        raise DataQualityError("Nao ha linhas validas para analise.")

    cleaned = cleaned.rename(columns={date_col: "analysis_date", sales_col: "analysis_sales"})
    cleaned["analysis_month"] = cleaned["analysis_date"].dt.to_period("M").dt.to_timestamp()
    return cleaned.sort_values("analysis_date").reset_index(drop=True)

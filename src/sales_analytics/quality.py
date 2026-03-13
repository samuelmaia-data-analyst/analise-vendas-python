from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DataQualityReport:
    total_rows: int
    valid_rows: int
    missing_required_columns: tuple[str, ...]
    duplicate_rows: int
    null_date_rows: int
    invalid_date_rows: int
    null_sales_rows: int
    invalid_sales_rows: int
    negative_sales_rows: int
    zero_sales_rows: int
    warnings: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.missing_required_columns and self.valid_rows > 0


def validate_sales_data(
    df: pd.DataFrame,
    *,
    date_col: str,
    sales_col: str,
    required_columns: set[str] | None = None,
) -> DataQualityReport:
    required = set(required_columns or set())
    required.update({date_col, sales_col})

    missing_required_columns = tuple(sorted(required - set(df.columns)))
    total_rows = int(len(df))

    if missing_required_columns:
        return DataQualityReport(
            total_rows=total_rows,
            valid_rows=0,
            missing_required_columns=missing_required_columns,
            duplicate_rows=0,
            null_date_rows=0,
            invalid_date_rows=0,
            null_sales_rows=0,
            invalid_sales_rows=0,
            negative_sales_rows=0,
            zero_sales_rows=0,
            warnings=(f"Colunas obrigatorias ausentes: {', '.join(missing_required_columns)}",),
        )

    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    parsed_sales = pd.to_numeric(df[sales_col], errors="coerce")

    null_date_mask = df[date_col].isna()
    null_sales_mask = df[sales_col].isna()
    invalid_date_mask = parsed_dates.isna() & ~null_date_mask
    invalid_sales_mask = parsed_sales.isna() & ~null_sales_mask
    negative_sales_mask = parsed_sales < 0
    zero_sales_mask = parsed_sales == 0

    valid_mask = (
        parsed_dates.notna()
        & parsed_sales.notna()
        & (parsed_sales >= 0)
    )

    warnings: list[str] = []
    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        warnings.append(f"{duplicate_rows} linhas duplicadas identificadas.")
    if int(invalid_date_mask.sum()):
        warnings.append(f"{int(invalid_date_mask.sum())} linhas com data invalida.")
    if int(invalid_sales_mask.sum()):
        warnings.append(f"{int(invalid_sales_mask.sum())} linhas com valor invalido.")
    if int(negative_sales_mask.sum()):
        warnings.append(f"{int(negative_sales_mask.sum())} linhas com vendas negativas removidas da analise.")
    if int(zero_sales_mask.sum()):
        warnings.append(f"{int(zero_sales_mask.sum())} linhas com vendas zeradas.")
    if int(valid_mask.sum()) == 0:
        warnings.append("Nao ha linhas validas para analise apos a limpeza.")

    return DataQualityReport(
        total_rows=total_rows,
        valid_rows=int(valid_mask.sum()),
        missing_required_columns=missing_required_columns,
        duplicate_rows=duplicate_rows,
        null_date_rows=int(null_date_mask.sum()),
        invalid_date_rows=int(invalid_date_mask.sum()),
        null_sales_rows=int(null_sales_mask.sum()),
        invalid_sales_rows=int(invalid_sales_mask.sum()),
        negative_sales_rows=int(negative_sales_mask.sum()),
        zero_sales_rows=int(zero_sales_mask.sum()),
        warnings=tuple(warnings),
    )

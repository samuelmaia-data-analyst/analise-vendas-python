from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .logging_utils import get_logger
from .metrics import (
    SalesKpis,
    compute_growth_over_period,
    compute_pareto,
    compute_sales_kpis,
    compute_yoy,
)
from .quality import DataQualityReport, validate_sales_data
from .transformations import prepare_sales_data

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class SalesAnalysisResult:
    cleaned_data: pd.DataFrame
    quality_report: DataQualityReport
    kpis: SalesKpis
    periodic_sales: pd.DataFrame
    yoy_sales: pd.DataFrame
    pareto_sales: pd.DataFrame


def run_sales_analysis(
    df: pd.DataFrame,
    *,
    date_col: str = "ORDERDATE",
    sales_col: str = "SALES",
    dimension_col: str | None = "PRODUCTLINE",
    period: str = "M",
) -> SalesAnalysisResult:
    LOGGER.info(
        "Iniciando analise de vendas | linhas=%s | date_col=%s | sales_col=%s | dimension_col=%s | period=%s",
        len(df),
        date_col,
        sales_col,
        dimension_col,
        period,
    )

    quality_report = validate_sales_data(
        df,
        date_col=date_col,
        sales_col=sales_col,
        required_columns={dimension_col} if dimension_col else None,
    )
    cleaned_data = prepare_sales_data(
        df,
        date_col=date_col,
        sales_col=sales_col,
        quality_report=quality_report,
    )
    periodic_sales = compute_growth_over_period(
        cleaned_data,
        date_col="analysis_date",
        sales_col="analysis_sales",
        period=period,
    )
    yoy_sales = compute_yoy(cleaned_data, date_col="analysis_date", sales_col="analysis_sales")
    pareto_sales = pd.DataFrame()
    if dimension_col and dimension_col in cleaned_data.columns:
        pareto_sales = compute_pareto(cleaned_data, dim_col=dimension_col, value_col="analysis_sales")

    kpis = compute_sales_kpis(
        cleaned_data,
        periodic_sales=periodic_sales,
        dimension_col=dimension_col if dimension_col in cleaned_data.columns else None,
    )
    LOGGER.info(
        "Analise concluida | linhas_validas=%s | receita_total=%.2f | pedidos=%s",
        quality_report.valid_rows,
        kpis.total_revenue,
        kpis.total_orders,
    )
    return SalesAnalysisResult(
        cleaned_data=cleaned_data,
        quality_report=quality_report,
        kpis=kpis,
        periodic_sales=periodic_sales,
        yoy_sales=yoy_sales,
        pareto_sales=pareto_sales,
    )

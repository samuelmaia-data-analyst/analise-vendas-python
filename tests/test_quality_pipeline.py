from __future__ import annotations

import pandas as pd
import pytest

from src.sales_analytics.exceptions import DataQualityError
from src.sales_analytics.pipeline import run_sales_analysis
from src.sales_analytics.quality import validate_sales_data


def test_validate_sales_data_flags_invalid_rows_and_missing_columns():
    df = pd.DataFrame(
        {
            "ORDERDATE": ["2024-01-01", "invalid", None],
            "SALES": ["100", "-20", "abc"],
        }
    )

    report = validate_sales_data(df, date_col="ORDERDATE", sales_col="SALES")

    assert report.total_rows == 3
    assert report.valid_rows == 1
    assert report.invalid_date_rows == 1
    assert report.invalid_sales_rows == 1
    assert report.negative_sales_rows == 1


def test_run_sales_analysis_returns_centralized_outputs():
    df = pd.DataFrame(
        {
            "ORDERNUMBER": [1, 2, 3, 4],
            "ORDERDATE": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"],
            "SALES": [100, 120, 140, 200],
            "PRODUCTLINE": ["A", "A", "B", "C"],
            "CUSTOMERNAME": ["X", "Y", "Z", "W"],
            "COUNTRY": ["BR", "BR", "US", "US"],
        }
    )

    result = run_sales_analysis(df, dimension_col="PRODUCTLINE")

    assert result.quality_report.is_valid
    assert result.kpis.total_revenue == 560
    assert not result.periodic_sales.empty
    assert not result.yoy_sales.empty
    assert not result.pareto_sales.empty


def test_run_sales_analysis_rejects_dataset_without_valid_rows():
    df = pd.DataFrame(
        {
            "ORDERDATE": ["invalid"],
            "SALES": ["invalid"],
        }
    )

    with pytest.raises(DataQualityError, match="Nao ha linhas validas"):
        run_sales_analysis(df, date_col="ORDERDATE", sales_col="SALES", dimension_col=None)

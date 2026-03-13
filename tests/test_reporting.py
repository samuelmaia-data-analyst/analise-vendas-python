from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.sales_analytics.pipeline import run_sales_analysis
from src.sales_analytics.reporting import build_executive_summary_frame, export_executive_summary


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ORDERNUMBER": [1, 2, 3],
            "ORDERDATE": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "SALES": [100, 150, 200],
            "PRODUCTLINE": ["A", "B", "C"],
        }
    )


def test_build_executive_summary_frame_contains_core_metrics():
    result = run_sales_analysis(_sample_df(), dimension_col="PRODUCTLINE")

    summary = build_executive_summary_frame(result)

    assert "metric" in summary.columns
    assert "value" in summary.columns
    assert "total_revenue" in summary["metric"].tolist()


def test_export_executive_summary_writes_csv(tmp_path: Path):
    result = run_sales_analysis(_sample_df(), dimension_col="PRODUCTLINE")

    output = export_executive_summary(result, output_path=tmp_path / "executive_summary.csv")

    assert output.exists()

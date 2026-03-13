from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import get_project_paths
from .logging_utils import get_logger
from .pipeline import SalesAnalysisResult

LOGGER = get_logger(__name__)


def build_executive_summary_frame(result: SalesAnalysisResult) -> pd.DataFrame:
    rows = [
        {"metric": "total_revenue", "value": round(result.kpis.total_revenue, 2)},
        {"metric": "total_orders", "value": result.kpis.total_orders},
        {"metric": "average_order_value", "value": round(result.kpis.average_order_value, 2)},
        {"metric": "average_growth_pct", "value": round(result.kpis.average_growth_pct, 2)},
        {"metric": "last_period_growth_pct", "value": round(result.kpis.last_period_growth_pct, 2)},
        {"metric": "best_period", "value": result.kpis.best_period},
        {"metric": "worst_period", "value": result.kpis.worst_period},
        {"metric": "peak_month", "value": result.kpis.peak_month},
        {"metric": "top3_share_pct", "value": round(result.kpis.top3_share_pct, 2) if result.kpis.top3_share_pct is not None else ""},
        {"metric": "valid_rows", "value": result.quality_report.valid_rows},
        {"metric": "duplicate_rows", "value": result.quality_report.duplicate_rows},
        {"metric": "invalid_date_rows", "value": result.quality_report.invalid_date_rows},
        {"metric": "invalid_sales_rows", "value": result.quality_report.invalid_sales_rows},
        {"metric": "negative_sales_rows", "value": result.quality_report.negative_sales_rows},
    ]
    return pd.DataFrame(rows)


def export_executive_summary(
    result: SalesAnalysisResult,
    output_path: Path | None = None,
) -> Path:
    target = output_path or (get_project_paths().reports_dir / "executive_summary.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    build_executive_summary_frame(result).to_csv(target, index=False, encoding="utf-8")
    LOGGER.info("Resumo executivo exportado para %s", target)
    return target

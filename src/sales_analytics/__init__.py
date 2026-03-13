"""Sales analytics domain package."""

from .artifacts import generate_processed_artifacts
from .data_contract import (
    REQUIRED_ARTIFACT_COLUMNS,
    REQUIRED_RAW_COLUMNS,
    load_raw_sales,
    validate_processed_schema,
    validate_raw_schema,
)
from .exceptions import DataQualityError, SalesAnalyticsError
from .metrics import SalesKpis, compute_growth_over_period, compute_main_metrics, compute_pareto, compute_sales_kpis, compute_yoy
from .pipeline import SalesAnalysisResult, run_sales_analysis
from .quality import DataQualityReport, validate_sales_data
from .reporting import build_executive_summary_frame, export_executive_summary
from .settings import AppSettings, get_app_settings

__all__ = [
    "REQUIRED_ARTIFACT_COLUMNS",
    "REQUIRED_RAW_COLUMNS",
    "DataQualityError",
    "DataQualityReport",
    "SalesAnalysisResult",
    "SalesAnalyticsError",
    "SalesKpis",
    "compute_pareto",
    "compute_sales_kpis",
    "compute_yoy",
    "compute_growth_over_period",
    "compute_main_metrics",
    "build_executive_summary_frame",
    "export_executive_summary",
    "generate_processed_artifacts",
    "get_app_settings",
    "load_raw_sales",
    "run_sales_analysis",
    "validate_sales_data",
    "validate_processed_schema",
    "validate_raw_schema",
    "AppSettings",
]

__version__ = "0.3.0"

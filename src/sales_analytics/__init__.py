"""Sales analytics domain package."""

from .artifacts import generate_processed_artifacts
from .data_contract import (
    REQUIRED_ARTIFACT_COLUMNS,
    REQUIRED_RAW_COLUMNS,
    load_raw_sales,
    validate_processed_schema,
    validate_raw_schema,
)
from .metrics import compute_growth_over_period, compute_main_metrics

__all__ = [
    "REQUIRED_ARTIFACT_COLUMNS",
    "REQUIRED_RAW_COLUMNS",
    "compute_growth_over_period",
    "compute_main_metrics",
    "generate_processed_artifacts",
    "load_raw_sales",
    "validate_processed_schema",
    "validate_raw_schema",
]

__version__ = "0.3.0"

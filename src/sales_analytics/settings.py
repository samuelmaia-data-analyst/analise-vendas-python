from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    max_upload_mb: int
    max_upload_rows: int
    max_upload_columns: int
    streamlit_port: int


def _read_positive_int(env_name: str, default: int) -> int:
    raw = os.getenv(env_name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{env_name} must be greater than zero")
    return value


def get_app_settings() -> AppSettings:
    return AppSettings(
        max_upload_mb=_read_positive_int("MAX_UPLOAD_MB", 40),
        max_upload_rows=_read_positive_int("MAX_UPLOAD_ROWS", 250000),
        max_upload_columns=_read_positive_int("MAX_UPLOAD_COLUMNS", 50),
        streamlit_port=_read_positive_int("STREAMLIT_SERVER_PORT", 8501),
    )

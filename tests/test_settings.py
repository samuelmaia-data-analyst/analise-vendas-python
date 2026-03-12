from __future__ import annotations

import pytest

from src.sales_analytics.settings import get_app_settings


def test_get_app_settings_reads_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MAX_UPLOAD_MB", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_ROWS", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_COLUMNS", raising=False)
    monkeypatch.delenv("STREAMLIT_SERVER_PORT", raising=False)

    settings = get_app_settings()

    assert settings.max_upload_mb == 40
    assert settings.max_upload_rows == 250000
    assert settings.max_upload_columns == 50
    assert settings.streamlit_port == 8501


def test_get_app_settings_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")

    with pytest.raises(ValueError, match="MAX_UPLOAD_MB must be greater than zero"):
        get_app_settings()

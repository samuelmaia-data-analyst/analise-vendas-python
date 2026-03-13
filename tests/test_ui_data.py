from __future__ import annotations

import pandas as pd
import pytest

from app.presentation.data import (
    carregar_csv_upload,
    carregar_dados,
    detect_date_columns,
    detect_value_columns,
    filter_value_columns,
    format_currency,
    month_name_pt,
    safe_to_datetime,
    safe_to_numeric,
    suggest_dimension_columns,
    validate_upload_frame,
)


def test_format_currency_returns_na_for_invalid_value():
    assert format_currency("invalid") == "N/A"


def test_safe_converters_and_month_name_behave_as_expected():
    dates = safe_to_datetime(pd.Series(["2024-01-01", "invalid"]))
    values = safe_to_numeric(pd.Series(["10", "invalid"]))

    assert dates.notna().tolist() == [True, False]
    assert values.notna().tolist() == [True, False]
    assert month_name_pt(3) == "Mar"
    assert month_name_pt(99) == "99"


def test_column_detection_helpers_prioritize_relevant_columns():
    df = pd.DataFrame(
        {
            "ORDERDATE": ["2024-01-01"],
            "SALES": [100],
            "PRODUCTLINE": ["Classic Cars"],
            "COUNTRY": ["Brazil"],
        }
    )

    assert detect_date_columns(df.columns.tolist()) == ["ORDERDATE"]
    assert "SALES" in detect_value_columns(df)
    assert filter_value_columns(["ORDERDATE", "SALES"], "ORDERDATE") == ["SALES"]
    dims = suggest_dimension_columns(df)
    assert dims[:2] == ["PRODUCTLINE", "COUNTRY"]


def test_carregar_csv_upload_detects_separator_and_parses_rows():
    csv_bytes = "ORDERDATE;SALES\n2024-01-01;100\n2024-02-01;200\n".encode("utf-8")

    df = carregar_csv_upload(csv_bytes)

    assert list(df.columns) == ["ORDERDATE", "SALES"]
    assert len(df) == 2


def test_carregar_csv_upload_rejects_invalid_payload():
    with pytest.raises(ValueError, match="Nao foi possivel ler o CSV enviado"):
        carregar_csv_upload(b"only-one-column-without-delimiter")


def test_carregar_dados_reads_local_csv_with_fallback_encoding(tmp_path, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "sales_data_sample.csv"
    csv_path.write_bytes("DATA;VENDAS;CIDADE\n2024-01-01;100;São Paulo\n".encode("cp1252"))
    monkeypatch.chdir(tmp_path)
    carregar_dados.clear()

    df, dados_reais, origem = carregar_dados()

    assert dados_reais is True
    assert origem == "data/raw/sales_data_sample.csv"
    assert list(df.columns) == ["DATA", "VENDAS", "CIDADE"]
    assert df.iloc[0]["CIDADE"] == "São Paulo"


def test_validate_upload_frame_enforces_operational_limits():
    valid_df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    assert validate_upload_frame(valid_df, max_rows=10, max_columns=5) == (True, None)

    too_many_rows = pd.DataFrame({"A": range(3)})
    assert validate_upload_frame(too_many_rows, max_rows=2, max_columns=5) == (False, "too_many_rows")

    too_many_columns = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
    assert validate_upload_frame(too_many_columns, max_rows=10, max_columns=2) == (False, "too_many_columns")

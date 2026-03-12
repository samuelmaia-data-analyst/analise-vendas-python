import pandas as pd
import pytest

from src.data_contract import load_raw_sales, validate_processed_schema, validate_raw_schema


def test_raw_schema_is_valid():
    df = load_raw_sales()
    is_valid, missing = validate_raw_schema(df)
    assert is_valid, f"Colunas ausentes: {missing}"


def test_processed_schema_flags_missing_columns():
    df = pd.DataFrame({"DATE_ID": [1], "DATA": ["2024-01-01"]})
    is_valid, missing = validate_processed_schema("dim_tempo.csv", df)

    assert not is_valid
    assert missing == ["ANO", "MES", "MES_NOME"]


def test_processed_schema_rejects_unknown_artifact():
    with pytest.raises(ValueError, match="Artefato sem contrato registrado"):
        validate_processed_schema("desconhecido.csv", pd.DataFrame())

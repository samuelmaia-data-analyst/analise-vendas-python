from src.data_contract import load_raw_sales, validate_raw_schema


def test_raw_schema_is_valid():
    df = load_raw_sales()
    is_valid, missing = validate_raw_schema(df)
    assert is_valid, f"Colunas ausentes: {missing}"

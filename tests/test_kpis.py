import pandas as pd
import pytest

from src.data_contract import load_raw_sales
from src.metrics import compute_growth_over_period, compute_main_metrics


def test_main_metrics_have_expected_keys_and_values():
    df = load_raw_sales()
    metrics = compute_main_metrics(df, date_col="ORDERDATE", sales_col="SALES")

    assert set(metrics.keys()) == {
        "receita_total",
        "crescimento_medio_pct",
        "melhor_periodo",
        "pior_periodo",
    }
    assert metrics["receita_total"] > 0
    assert metrics["melhor_periodo"] != "N/A"
    assert metrics["pior_periodo"] != "N/A"


def test_compute_growth_over_period_rejects_missing_columns():
    df = pd.DataFrame({"DATA": ["2024-01-01"], "VALOR": [10]})

    with pytest.raises(ValueError, match="Colunas obrigatorias ausentes"):
        compute_growth_over_period(df, date_col="ORDERDATE", sales_col="SALES")


def test_compute_growth_over_period_rejects_empty_normalized_dataset():
    df = pd.DataFrame({"ORDERDATE": ["invalid"], "SALES": ["invalid"]})

    with pytest.raises(ValueError, match="Nao ha linhas validas"):
        compute_growth_over_period(df, date_col="ORDERDATE", sales_col="SALES")

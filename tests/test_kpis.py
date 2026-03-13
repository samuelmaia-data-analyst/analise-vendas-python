import pandas as pd
import pytest

from src.sales_analytics.data_contract import load_raw_sales
from src.sales_analytics.metrics import compute_growth_over_period, compute_main_metrics, compute_sales_kpis
from src.sales_analytics.transformations import prepare_sales_data


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


def test_compute_growth_over_period_rejects_same_date_and_value_column():
    df = pd.DataFrame({"ORDERDATE": ["2024-01-01"], "SALES": [10]})

    with pytest.raises(ValueError, match="nao podem ser iguais"):
        compute_growth_over_period(df, date_col="ORDERDATE", sales_col="ORDERDATE")


def test_compute_growth_over_period_rejects_empty_normalized_dataset():
    df = pd.DataFrame({"ORDERDATE": ["invalid"], "SALES": ["invalid"]})

    with pytest.raises(ValueError, match="Nao ha linhas validas"):
        compute_growth_over_period(df, date_col="ORDERDATE", sales_col="SALES")


def test_compute_sales_kpis_returns_business_metrics():
    df = pd.DataFrame(
        {
            "ORDERNUMBER": [1, 1, 2, 3],
            "ORDERDATE": ["2024-01-01", "2024-01-15", "2024-02-01", "2024-03-01"],
            "SALES": [100, 50, 120, 180],
            "PRODUCTLINE": ["A", "A", "B", "C"],
        }
    )

    cleaned = prepare_sales_data(df, date_col="ORDERDATE", sales_col="SALES")
    kpis = compute_sales_kpis(cleaned, dimension_col="PRODUCTLINE")

    assert kpis.total_revenue == 450
    assert kpis.total_orders == 3
    assert kpis.average_order_value == 150
    assert kpis.top3_share_pct == pytest.approx(100.0)

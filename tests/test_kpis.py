from src.data_contract import load_raw_sales
from src.metrics import compute_main_metrics


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

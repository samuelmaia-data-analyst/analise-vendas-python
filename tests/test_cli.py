from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.sales_analytics import app_runner
from src.sales_analytics import cli
from src.sales_analytics.data_contract import load_raw_sales, resolve_first_existing_path
from src.sales_analytics.metrics import compute_growth_over_period


def test_resolve_first_existing_path_returns_first_match(tmp_path: Path):
    target = tmp_path / "raw.csv"
    target.write_text("id\n1\n", encoding="utf-8")

    resolved = resolve_first_existing_path(tmp_path / "missing.csv", target)

    assert resolved == target


def test_resolve_first_existing_path_raises_when_nothing_exists(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Nenhum arquivo encontrado"):
        resolve_first_existing_path(tmp_path / "missing.csv")


def test_load_raw_sales_accepts_explicit_path(tmp_path: Path):
    csv_file = tmp_path / "sales.csv"
    csv_file.write_text("ORDERNUMBER,ORDERDATE,SALES,PRODUCTLINE,CUSTOMERNAME,COUNTRY\n1,2024-01-01,10,A,Client,BR\n", encoding="utf-8")

    df = load_raw_sales(csv_file)

    assert len(df) == 1
    assert list(df.columns) == [
        "ORDERNUMBER",
        "ORDERDATE",
        "SALES",
        "PRODUCTLINE",
        "CUSTOMERNAME",
        "COUNTRY",
    ]


def test_compute_growth_over_period_rejects_invalid_period():
    df = pd.DataFrame({"ORDERDATE": ["2024-01-01"], "SALES": [10]})

    with pytest.raises(ValueError, match="Periodo deve ser 'M', 'T' ou 'A'"):
        compute_growth_over_period(df, date_col="ORDERDATE", sales_col="SALES", period="W")


def test_cli_summary_command_prints_kpis(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("sys.argv", ["sales-analytics", "summary"])

    exit_code = cli.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "receita_total" in output
    assert "ticket_medio" in output


def test_cli_growth_command_prints_csv(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("sys.argv", ["sales-analytics", "growth", "--period", "M"])

    exit_code = cli.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "total_vendas" in output
    assert "crescimento_%" in output


def test_cli_build_artifacts_command_writes_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
):
    monkeypatch.setattr(
        "sys.argv",
        ["sales-analytics", "build-artifacts", "--output-dir", str(tmp_path)],
    )

    exit_code = cli.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "fato_vendas.csv" in output
    assert "dim_tempo.csv" in output
    assert (tmp_path / "fato_vendas.csv").exists()
    assert (tmp_path / "dim_tempo.csv").exists()


def test_cli_export_summary_command_writes_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
):
    output_file = tmp_path / "executive_summary.csv"
    monkeypatch.setattr(
        "sys.argv",
        ["sales-analytics", "export-summary", "--output", str(output_file)],
    )

    exit_code = cli.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "executive_summary.csv" in output
    assert output_file.exists()


def test_run_streamlit_app_delegates_to_runpy(monkeypatch: pytest.MonkeyPatch):
    called: dict[str, str] = {}

    def fake_run_path(path: str, run_name: str) -> None:
        called["path"] = path
        called["run_name"] = run_name

    monkeypatch.setattr(app_runner.runpy, "run_path", fake_run_path)

    app_runner.run_streamlit_app()

    assert called["path"].endswith("app\\streamlit_app.py")
    assert called["run_name"] == "__main__"

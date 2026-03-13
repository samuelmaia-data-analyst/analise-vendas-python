from __future__ import annotations

import argparse
from pathlib import Path

from .artifacts import generate_processed_artifacts
from .config import get_project_paths
from .data_contract import load_raw_sales
from .exceptions import SalesAnalyticsError
from .logging_utils import get_logger
from .pipeline import run_sales_analysis

LOGGER = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Official CLI for the sales analytics project.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Generate an executive summary from the raw dataset.")
    summary_parser.add_argument("--date-col", default="ORDERDATE")
    summary_parser.add_argument("--sales-col", default="SALES")
    summary_parser.add_argument("--dimension-col", default="PRODUCTLINE")
    summary_parser.add_argument("--period", default="M", choices=["M", "T", "A"])

    growth_parser = subparsers.add_parser("growth", help="Compute growth over time from the raw dataset.")
    growth_parser.add_argument("--date-col", default="ORDERDATE")
    growth_parser.add_argument("--sales-col", default="SALES")
    growth_parser.add_argument("--period", default="M", choices=["M", "T", "A"])

    artifact_parser = subparsers.add_parser("build-artifacts", help="Generate processed artifacts from the raw dataset.")
    artifact_parser.add_argument("--output-dir", default=None)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        df = load_raw_sales()

        if args.command == "summary":
            result = run_sales_analysis(
                df=df,
                date_col=args.date_col,
                sales_col=args.sales_col,
                dimension_col=args.dimension_col,
                period=args.period,
            )
            print(f"receita_total,{result.kpis.total_revenue:.2f}")
            print(f"pedidos,{result.kpis.total_orders}")
            print(f"ticket_medio,{result.kpis.average_order_value:.2f}")
            print(f"crescimento_medio_pct,{result.kpis.average_growth_pct:.2f}")
            print(f"melhor_periodo,{result.kpis.best_period}")
            print(f"pior_periodo,{result.kpis.worst_period}")
            if result.kpis.top3_share_pct is not None:
                print(f"top3_share_pct,{result.kpis.top3_share_pct:.2f}")
            return 0

        if args.command == "growth":
            result = run_sales_analysis(
                df=df,
                date_col=args.date_col,
                sales_col=args.sales_col,
                dimension_col=None,
                period=args.period,
            )
            print(result.periodic_sales.to_csv(index=False))
            return 0

        if args.command == "build-artifacts":
            default_output = get_project_paths().processed_data_dir
            output_dir = default_output if args.output_dir is None else Path(args.output_dir)
            files = generate_processed_artifacts(df=df, output_dir=output_dir)
            for file_path in files:
                print(file_path)
            return 0
    except (SalesAnalyticsError, ValueError, FileNotFoundError) as exc:
        LOGGER.error("Falha na execucao da CLI: %s", exc)
        print(f"Erro: {exc}")
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

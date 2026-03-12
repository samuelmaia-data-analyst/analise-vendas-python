from __future__ import annotations

import argparse
from pathlib import Path

from .artifacts import generate_processed_artifacts
from .config import get_project_paths
from .data_contract import load_raw_sales
from .metrics import compute_growth_over_period


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Official CLI for the sales analytics project.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    growth_parser = subparsers.add_parser("growth", help="Compute growth over time from the raw dataset.")
    growth_parser.add_argument("--date-col", default="ORDERDATE")
    growth_parser.add_argument("--sales-col", default="SALES")
    growth_parser.add_argument("--period", default="M", choices=["M", "T", "A"])

    artifact_parser = subparsers.add_parser("build-artifacts", help="Generate processed artifacts from the raw dataset.")
    artifact_parser.add_argument("--output-dir", default=None)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "growth":
        df = load_raw_sales()
        growth = compute_growth_over_period(
            df=df,
            date_col=args.date_col,
            sales_col=args.sales_col,
            period=args.period,
        )
        print(growth.to_csv(index=False))
        return 0

    if args.command == "build-artifacts":
        df = load_raw_sales()
        default_output = get_project_paths().processed_data_dir
        output_dir = default_output if args.output_dir is None else Path(args.output_dir)
        files = generate_processed_artifacts(df=df, output_dir=output_dir)
        for file_path in files:
            print(file_path)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations
# ruff: noqa: E402

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.sales_analytics.versioning import (
    bump_version,
    ensure_version_sync,
    prepend_changelog_stub,
    validate_semver,
    write_version_files,
)  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize project version files and prepare changelog entry.")
    parser.add_argument("--version", help="Explicit semantic version to write.")
    parser.add_argument("--part", choices=["major", "minor", "patch"], help="Semantic version part to bump.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    current = ensure_version_sync()

    if bool(args.version) == bool(args.part):
        raise ValueError("Provide exactly one of --version or --part")

    new_version = validate_semver(args.version) if args.version else bump_version(current, args.part)
    write_version_files(new_version)
    prepend_changelog_stub(new_version, date.today().isoformat())
    print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

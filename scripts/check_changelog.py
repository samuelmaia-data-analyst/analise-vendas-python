from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.sales_analytics.versioning import ensure_version_sync, validate_changelog_structure  # noqa: E402


def main() -> int:
    version = ensure_version_sync()
    validate_changelog_structure(version)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

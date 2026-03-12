from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    legacy_raw_data_dir: Path
    legacy_processed_data_dir: Path
    reports_dir: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_project_paths() -> ProjectPaths:
    root = project_root()
    return ProjectPaths(
        root=root,
        raw_data_dir=root / "data" / "raw",
        processed_data_dir=root / "data" / "processed",
        legacy_raw_data_dir=root / "legacy" / "dados",
        legacy_processed_data_dir=root / "legacy" / "dados_processados",
        reports_dir=root / "reports",
    )

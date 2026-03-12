from __future__ import annotations

import pytest

from src.sales_analytics.versioning import bump_version, changelog_has_version, ensure_version_sync, validate_semver


def test_validate_semver_accepts_and_rejects_expected_formats():
    assert validate_semver("1.2.3") == "1.2.3"
    with pytest.raises(ValueError, match="Invalid semantic version"):
        validate_semver("1.2")


def test_bump_version_updates_requested_part():
    assert bump_version("0.3.0", "patch") == "0.3.1"
    assert bump_version("0.3.0", "minor") == "0.4.0"
    assert bump_version("0.3.0", "major") == "1.0.0"


def test_project_version_files_are_in_sync_and_present_in_changelog():
    version = ensure_version_sync()
    assert version == "0.3.0"
    assert changelog_has_version(version)

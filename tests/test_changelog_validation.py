from __future__ import annotations

import pytest

from src.sales_analytics.versioning import get_latest_changelog_block, validate_changelog_structure


def test_latest_changelog_block_matches_current_release():
    version, block = get_latest_changelog_block()
    assert version == "0.3.0"
    assert "### Added" in block


def test_validate_changelog_structure_accepts_current_release():
    validate_changelog_structure("0.3.0")


def test_validate_changelog_structure_rejects_wrong_expected_version():
    with pytest.raises(ValueError, match="Latest changelog version"):
        validate_changelog_structure("9.9.9")

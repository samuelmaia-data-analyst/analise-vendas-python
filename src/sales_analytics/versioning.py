from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import project_root

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
CHANGELOG_SECTION_RE = re.compile(r"^## \[(?P<version>[^\]]+)\] - (?P<date>\d{4}-\d{2}-\d{2})$", re.MULTILINE)
CHANGELOG_SUBSECTION_RE = re.compile(r"^### (?P<section>Added|Changed|Fixed|Removed|Security|Deprecated)$", re.MULTILINE)


@dataclass(frozen=True)
class VersionFiles:
    version_file: Path
    pyproject_file: Path
    package_init_file: Path
    changelog_file: Path


def get_version_files() -> VersionFiles:
    root = project_root()
    return VersionFiles(
        version_file=root / "VERSION",
        pyproject_file=root / "pyproject.toml",
        package_init_file=root / "src" / "sales_analytics" / "__init__.py",
        changelog_file=root / "CHANGELOG.md",
    )


def validate_semver(version: str) -> str:
    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"Invalid semantic version: {version}")
    return version


def read_declared_versions() -> dict[str, str]:
    files = get_version_files()
    version_txt = files.version_file.read_text(encoding="utf-8").strip()
    pyproject = files.pyproject_file.read_text(encoding="utf-8")
    package_init = files.package_init_file.read_text(encoding="utf-8")

    pyproject_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    package_match = re.search(r'^__version__ = "([^"]+)"$', package_init, re.MULTILINE)
    if pyproject_match is None or package_match is None:
        raise ValueError("Unable to locate declared versions in project files")

    return {
        "VERSION": version_txt,
        "pyproject.toml": pyproject_match.group(1),
        "src/sales_analytics/__init__.py": package_match.group(1),
    }


def ensure_version_sync() -> str:
    versions = read_declared_versions()
    unique_versions = set(versions.values())
    if len(unique_versions) != 1:
        rendered = ", ".join(f"{name}={value}" for name, value in versions.items())
        raise ValueError(f"Version mismatch detected: {rendered}")
    return unique_versions.pop()


def bump_version(current_version: str, part: str) -> str:
    major, minor, patch = (int(item) for item in validate_semver(current_version).split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError("part must be 'major', 'minor', or 'patch'")


def write_version_files(new_version: str) -> None:
    validated = validate_semver(new_version)
    files = get_version_files()

    files.version_file.write_text(f"{validated}\n", encoding="utf-8")

    pyproject = files.pyproject_file.read_text(encoding="utf-8")
    pyproject = re.sub(r'^version = "[^"]+"$', f'version = "{validated}"', pyproject, flags=re.MULTILINE)
    files.pyproject_file.write_text(pyproject, encoding="utf-8")

    package_init = files.package_init_file.read_text(encoding="utf-8")
    package_init = re.sub(r'^__version__ = "[^"]+"$', f'__version__ = "{validated}"', package_init, flags=re.MULTILINE)
    files.package_init_file.write_text(package_init, encoding="utf-8")


def changelog_has_version(version: str) -> bool:
    changelog = get_version_files().changelog_file.read_text(encoding="utf-8")
    return f"## [{version}]" in changelog


def get_latest_changelog_block() -> tuple[str, str]:
    changelog = get_version_files().changelog_file.read_text(encoding="utf-8")
    matches = list(CHANGELOG_SECTION_RE.finditer(changelog))
    if not matches:
        raise ValueError("CHANGELOG.md does not contain any release sections")

    first = matches[0]
    end = matches[1].start() if len(matches) > 1 else len(changelog)
    return first.group("version"), changelog[first.start():end]


def validate_changelog_structure(expected_version: str) -> None:
    latest_version, latest_block = get_latest_changelog_block()
    if latest_version != expected_version:
        raise ValueError(
            f"Latest changelog version {latest_version} does not match expected version {expected_version}"
        )

    sections = {match.group("section") for match in CHANGELOG_SUBSECTION_RE.finditer(latest_block)}
    if not sections:
        raise ValueError("Latest changelog entry must contain at least one subsection such as Added or Changed")


def prepend_changelog_stub(version: str, release_date: str) -> None:
    files = get_version_files()
    changelog = files.changelog_file.read_text(encoding="utf-8")
    if changelog_has_version(version):
        return

    marker = "The format is based on Keep a Changelog and this project follows Semantic Versioning.\n"
    stub = (
        f"\n## [{version}] - {release_date}\n\n"
        "### Added\n"
        "- TBD\n\n"
        "### Changed\n"
        "- TBD\n"
    )
    if marker not in changelog:
        raise ValueError("Unable to locate changelog header marker")
    files.changelog_file.write_text(changelog.replace(marker, marker + stub), encoding="utf-8")

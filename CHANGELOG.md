# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.3.0] - 2026-03-12

### Added
- Installable package metadata and official CLI commands for growth analysis and artifact generation.
- Architecture documentation and `.env.example` for safer onboarding.
- Contract tests for processed artifacts and negative-path coverage for metrics/artifacts.

### Changed
- Streamlit now consumes shared domain logic from `src/sales_analytics/` instead of the legacy analysis script.
- Local and CI setup now install the project in editable mode with optional dev dependencies.

## [0.2.0] - 2026-03-06

### Added
- Executive impact positioning at the top of README docs (business outcomes and decision support).
- End-to-end architecture and pipeline section to communicate systemic vision.
- Official GitHub release workflow (`.github/workflows/release.yml`) for tagged versions.

### Changed
- Release management section to reference the official published release and release notes flow.

## [0.1.0] - 2026-03-05

### Added
- Engineering-first structure (`src`, `tests`, `data/raw`, `data/processed`, `reports`, `app`).
- CI pipeline with lint, typing, and tests.
- Pre-commit hooks for linting/formatting and file hygiene.
- Data contract, metrics, and artifact generation modules under `src/`.
- Minimum automated test suite for schema, business metrics, and artifact generation.
- Bilingual documentation (`README.md` and `README.pt-BR.md`).
- Governance docs (`CONTRIBUTING`, `SECURITY`, templates, `CODEOWNERS`).
- Local task runners (`Makefile` and `Taskfile.yml`).

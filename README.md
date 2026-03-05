# Sales Analytics Dashboard (International)

[![CI](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml/badge.svg)](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)

Language: [Português (Brasil)](README.pt-BR.md)

## Quick Links

- Repository: [samuelmaia-data-analyst/analise-vendas-python](https://github.com/samuelmaia-data-analyst/analise-vendas-python)
- CI Workflow: [GitHub Actions - CI](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml)
- Live App: [Streamlit Deploy](https://analys-vendas-python.streamlit.app/)
- Portuguese README: [README.pt-BR.md](README.pt-BR.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Version: [VERSION](VERSION)
- Documentation Index: [docs/README.md](docs/README.md)
- Engineering Standards: [docs/engineering_standards.md](docs/engineering_standards.md)
- Structure Print View: [docs/print_view.md](docs/print_view.md)
- Data Dictionary: [reports/data_dictionary.md](reports/data_dictionary.md)

## Table of Contents

- [Executive Summary](#executive-summary)
- [Engineering Structure](#engineering-structure)
- [Repository Map](#repository-map)
- [Quality Gates](#quality-gates)
- [Quick Start](#quick-start)
- [Automated Tests](#automated-tests)
- [Release Management](#release-management)
- [Governance](#governance)
- [Data Dictionary](#data-dictionary)
- [Dataset Source](#dataset-source)

## Executive Summary

This project is an end-to-end Sales Analytics solution focused on business decision support.

It combines:
- Revenue and growth KPIs
- Pareto concentration analysis
- Monthly Year-over-Year (YoY) tracking
- Interactive Streamlit dashboard

## Engineering Structure

```text
.
├── app/                       # Streamlit UI layer
├── src/                       # Core business/data logic
├── tests/                     # Automated tests
├── data/
│   ├── raw/                   # Source datasets
│   └── processed/             # Modeled outputs
├── reports/                   # Business-facing artifacts
├── scripts/                   # Utility scripts / CLI workflows
├── .github/workflows/ci.yml   # CI pipeline (ruff + pytest)
├── requirements.txt
├── requirements-dev.txt
└── app.py                     # Entry point
```

Legacy compatibility folders were isolated under `legacy/` and are still supported by fallback paths (`legacy/dados/`, `legacy/dados_processados/`).

## Repository Map

- Application: [app/](app) and [app.py](app.py)
- Core logic: [src/](src)
- Tests: [tests/](tests)
- Data: [data/raw/](data/raw) and [data/processed/](data/processed)
- Utility scripts: [scripts/](scripts)
- Project docs: [docs/](docs) and [reports/](reports)
- CI and templates: [.github/](.github)

## Quality Gates

- Lint: `ruff check .`
- Type check: `mypy src`
- Docs link check: `python scripts/check_markdown_links.py`
- Tests + coverage gate: `pytest` (minimum coverage: 80% in `src`)
- Local hooks: `pre-commit`

## Quick Start

```bash
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
make quality
streamlit run app.py
```

Alternative (Taskfile):

```bash
task quality
```

## Automated Tests

- `tests/test_schema.py`: validates raw schema contract
- `tests/test_metrics.py`: validates primary business metrics
- `tests/test_artifacts.py`: validates processed artifact generation

## Release Management

- Current version: `0.1.0` ([VERSION](VERSION))
- Change history: [CHANGELOG.md](CHANGELOG.md)

## Governance

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Engineering standards: [docs/engineering_standards.md](docs/engineering_standards.md)
- Project structure print view: [docs/print_view.md](docs/print_view.md)

## Data Dictionary

See [reports/data_dictionary.md](reports/data_dictionary.md).

## Dataset Source

Kaggle - [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data)

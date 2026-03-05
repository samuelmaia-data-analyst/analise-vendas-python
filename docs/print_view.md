# Print View (Project Structure)

```text
analise-vendas-python/
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |   |-- bug_report.yml
|   |   `-- feature_request.yml
|   |-- workflows/
|   |   `-- ci.yml
|   `-- pull_request_template.md
|-- app/
|   |-- __init__.py
|   `-- streamlit_app.py
|-- data/
|   |-- raw/
|   |   `-- sales_data_sample.csv
|   `-- processed/
|       |-- dim_clientes.csv
|       |-- dim_produtos.csv
|       |-- dim_tempo.csv
|       |-- fato_vendas.csv
|       |-- LEIAME_POWERBI.txt
|       |-- modelo_completo.xlsx
|       `-- vendas_simples.csv
|-- docs/
|   |-- README.md
|   |-- engineering_standards.md
|   `-- print_view.md
|-- legacy/
|   |-- dados/
|   |   `-- sales_data_sample.csv
|   `-- dados_processados/
|       |-- dim_clientes.csv
|       |-- dim_produtos.csv
|       |-- dim_tempo.csv
|       |-- fato_vendas.csv
|       |-- LEIAME_POWERBI.txt
|       |-- modelo_completo.xlsx
|       `-- vendas_simples.csv
|-- reports/
|   `-- data_dictionary.md
|-- scripts/
|   |-- analise_crescimento.py
|   |-- check_markdown_links.py
|   `-- processador_powerbi.py
|-- src/
|   |-- __init__.py
|   |-- artifacts.py
|   |-- data_contract.py
|   `-- metrics.py
|-- tests/
|   |-- conftest.py
|   |-- test_artifacts.py
|   |-- test_kpis.py
|   `-- test_data_schema.py
|-- .editorconfig
|-- .pre-commit-config.yaml
|-- app.py
|-- CHANGELOG.md
|-- CODEOWNERS
|-- CONTRIBUTING.md
|-- Makefile
|-- pyproject.toml
|-- README.md
|-- README.pt-BR.md
|-- requirements.txt
|-- requirements-dev.txt
|-- SECURITY.md
|-- Taskfile.yml
`-- VERSION
```

Notes:
- Legacy folders are isolated under `legacy/` and remain for backward compatibility.
- New development should target `data/raw` and `data/processed`.

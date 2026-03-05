# Dashboard de Análise de Vendas (PT-BR)

[![CI](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml/badge.svg)](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)

Idioma: [English](README.md)

## Links Rápidos

- Repositório: [samuelmaia-data-analyst/analise-vendas-python](https://github.com/samuelmaia-data-analyst/analise-vendas-python)
- Workflow de CI: [GitHub Actions - CI](https://github.com/samuelmaia-data-analyst/analise-vendas-python/actions/workflows/ci.yml)
- Deploy: [Streamlit](https://analys-vendas-python.streamlit.app/)
- README internacional: [README.md](README.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Versão: [VERSION](VERSION)
- Índice de documentação: [docs/README.md](docs/README.md)
- Padrões de engenharia: [docs/engineering_standards.md](docs/engineering_standards.md)
- Print view da estrutura: [docs/print_view.md](docs/print_view.md)
- Dicionário de dados: [reports/data_dictionary.md](reports/data_dictionary.md)

## Sumário

- [Resumo Executivo](#resumo-executivo)
- [Estrutura de Engenharia](#estrutura-de-engenharia)
- [Mapa do Repositório](#mapa-do-repositorio)
- [Portões de Qualidade](#portoes-de-qualidade)
- [Execução Rápida](#execucao-rapida)
- [Testes Automatizados](#testes-automatizados)
- [Gestão de Releases](#gestao-de-releases)
- [Governança](#governanca)
- [Dicionário de Dados](#dicionario-de-dados)
- [Fonte de Dados](#fonte-de-dados)

## <a id="resumo-executivo"></a>Resumo Executivo

Este projeto é uma solução end-to-end de Sales Analytics com foco em apoio à decisão de negócio.

Entrega:
- KPIs de receita e crescimento
- Análise de concentração por Pareto
- Comparação Year-over-Year (YoY) mensal
- Dashboard interativo em Streamlit

## <a id="estrutura-de-engenharia"></a>Estrutura de Engenharia

```text
.
├── app/                       # Camada de interface (Streamlit)
├── src/                       # Lógica de negócio e dados
├── tests/                     # Testes automatizados
├── data/
│   ├── raw/                   # Dados de origem
│   └── processed/             # Saídas processadas/modeladas
├── reports/                   # Artefatos para negócio
├── scripts/                   # Rotinas utilitárias e CLI
├── .github/workflows/ci.yml   # CI (ruff + pytest)
├── requirements.txt
├── requirements-dev.txt
└── app.py                     # Ponto de entrada
```

Pastas legadas foram isoladas em `legacy/` e continuam suportadas por fallback (`legacy/dados/`, `legacy/dados_processados/`) para manter compatibilidade.

## <a id="mapa-do-repositorio"></a>Mapa do Repositório

- Aplicação: [app/](app) e [app.py](app.py)
- Lógica central: [src/](src)
- Testes: [tests/](tests)
- Dados: [data/raw/](data/raw) e [data/processed/](data/processed)
- Scripts utilitários: [scripts/](scripts)
- Documentação: [docs/](docs) e [reports/](reports)
- CI e templates: [.github/](.github)

## <a id="portoes-de-qualidade"></a>Portões de Qualidade

- Lint: `ruff check .`
- Tipagem estática: `mypy src`
- Checagem de links da documentação: `python scripts/check_markdown_links.py`
- Testes + gate de cobertura: `pytest` (cobertura mínima: 80% em `src`)
- Hooks locais: `pre-commit`

## <a id="execucao-rapida"></a>Execução Rápida

```bash
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
make quality
streamlit run app.py
```

Alternativa (Taskfile):

```bash
task quality
```

## <a id="testes-automatizados"></a>Testes Automatizados

- `tests/test_schema.py`: valida o contrato mínimo de schema da base raw
- `tests/test_metrics.py`: valida métricas principais de negócio
- `tests/test_artifacts.py`: valida geração de artefatos processados

## <a id="gestao-de-releases"></a>Gestão de Releases

- Versão atual: `0.1.0` ([VERSION](VERSION))
- Histórico de mudanças: [CHANGELOG.md](CHANGELOG.md)

## <a id="governanca"></a>Governança

- Guia de contribuição: [CONTRIBUTING.md](CONTRIBUTING.md)
- Política de segurança: [SECURITY.md](SECURITY.md)
- Padrões de engenharia: [docs/engineering_standards.md](docs/engineering_standards.md)
- Print view da estrutura: [docs/print_view.md](docs/print_view.md)

## <a id="dicionario-de-dados"></a>Dicionário de Dados

Consulte [reports/data_dictionary.md](reports/data_dictionary.md).

## <a id="fonte-de-dados"></a>Fonte de Dados

Kaggle - [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data)

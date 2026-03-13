# Analise de Vendas em Python

[![CI](https://github.com/samuelmaia-analytics/analise-vendas-python/actions/workflows/ci.yml/badge.svg)](https://github.com/samuelmaia-analytics/analise-vendas-python/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Coverage](https://img.shields.io/badge/Cobertura-90%25-brightgreen)

Idioma: [English](README.md)

## Visao de negocio

Este projeto transforma uma base bruta de vendas em uma leitura executiva simples:

- quanto a empresa vendeu
- como a receita evoluiu ao longo do tempo
- quais periodos concentraram melhor e pior desempenho
- quanto da receita depende de poucas categorias, produtos ou clientes
- qual o nivel de qualidade da base antes da tomada de decisao

O objetivo nao e criar uma stack excessivamente sofisticada, e sim apresentar um projeto com criterio de negocio, organizacao de engenharia e fluxo analitico reproduzivel.

## Principais insights da base amostral

Resultados calculados sobre `data/raw/sales_data_sample.csv` em 13 de marco de 2026:

- Receita total: `10.032.628,85`
- Pedidos unicos: `307`
- Ticket medio por pedido: `32.679,57`
- Crescimento medio mensal: `14,30%`
- Melhor periodo: `2003-10`
- Pior periodo: `2003-12`
- Participacao do top 3 em `PRODUCTLINE`: `69,66%`

Leitura executiva:
- a receita esta concentrada em poucas linhas de produto, o que sugere dependencia comercial relevante
- outubro de 2003 representa o melhor momento de aceleracao da base
- dezembro de 2003 concentra a maior deterioracao relativa entre periodos

## O que foi melhorado

- fluxo analitico separado em leitura, qualidade, transformacao, metricas e visualizacao
- KPI centralizado em um modulo unico de negocio
- validacoes de qualidade de dados antes da analise
- logging simples para carga, processamento e CLI
- tratamento de erros para execucao local e dashboard
- dashboard reorganizado em ordem mais executiva
- testes cobrindo metricas, pipeline e contratos de dados

## Stack

- Python
- Pandas
- Plotly
- Streamlit
- Pytest
- Ruff
- Mypy

## Estrutura do projeto

```text
.
├── app/
│   ├── streamlit_app.py              # dashboard principal
│   └── presentation/                 # componentes e helpers visuais
├── data/
│   ├── raw/                          # dados de origem
│   └── processed/                    # artefatos processados
├── src/
│   └── sales_analytics/
│       ├── cli.py                    # fluxo de execucao via terminal
│       ├── data_contract.py          # leitura e contratos de schema
│       ├── quality.py                # validacoes de qualidade
│       ├── transformations.py        # limpeza e preparo analitico
│       ├── metrics.py                # KPIs e agregacoes centrais
│       ├── pipeline.py               # orquestracao da analise
│       └── artifacts.py              # geracao de saidas processadas
├── tests/                            # testes automatizados
├── docs/                             # documentacao de apoio
└── app.py                            # entrypoint limpo
```

## Fluxo de execucao

1. Ler a base de vendas.
2. Validar colunas obrigatorias, datas, valores e inconsistencias basicas.
3. Limpar e padronizar os dados para analise.
4. Calcular KPIs, crescimento, YoY e concentracao.
5. Exibir os resultados em uma narrativa visual mais executiva.

## Como executar

```bash
pip install -e ".[dev]"
streamlit run app.py
```

Fluxo via CLI:

```bash
sales-analytics summary
sales-analytics growth --period M
sales-analytics build-artifacts
```

## Testes e qualidade

```bash
ruff check .
pytest
mypy src
```

Cobertura atual da suite: `90%`.

## Diferenciais para recrutadores tecnicos

- contexto de negocio explicito no README e no dashboard
- separacao clara de responsabilidades no codigo
- validacao de qualidade antes do calculo de indicadores
- KPIs centralizados e testados
- entrada principal simples e facil de demonstrar

## Fonte de dados

Kaggle: [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data)

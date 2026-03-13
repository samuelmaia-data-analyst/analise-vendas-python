# Python Sales Analytics

[![CI](https://github.com/samuelmaia-analytics/analise-vendas-python/actions/workflows/ci.yml/badge.svg)](https://github.com/samuelmaia-analytics/analise-vendas-python/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Coverage](https://img.shields.io/badge/Coverage-90%25-brightgreen)

Language: [Portuguese (Brazil)](README.pt-BR.md)

## Business view

This project turns a raw sales dataset into a decision-ready analysis flow focused on a few management questions:

- how much revenue was generated
- whether revenue is expanding or slowing down
- which periods performed best and worst
- how concentrated revenue is across product lines, products, or customers
- how trustworthy the dataset is before the analysis is consumed

The goal is not unnecessary sophistication. The goal is a cleaner portfolio project with stronger structure, clearer business framing, and a more mature execution flow.

## Sample dataset highlights

Calculated from `data/raw/sales_data_sample.csv` on March 13, 2026:

- Total revenue: `10,032,628.85`
- Unique orders: `307`
- Average order value: `32,679.57`
- Average monthly growth: `14.30%`
- Best period: `2003-10`
- Worst period: `2003-12`
- Top 3 `PRODUCTLINE` share: `69.66%`

Executive takeaway:
- revenue is materially concentrated in a small set of product lines
- October 2003 is the strongest acceleration point in the sample
- December 2003 is the weakest relative period in the trend series

## What improved

- reusable functions separated by responsibility
- dedicated layers for reading, quality checks, transformation, analytics, and visualization
- centralized sales KPIs
- simple logging and error handling
- more executive chart sequence in the dashboard
- lightweight test coverage for analytical functions and pipeline behavior

## Stack

- Python
- Pandas
- Plotly
- Streamlit
- Pytest
- Ruff
- Mypy

## Project structure

```text
.
├── app/
│   ├── streamlit_app.py
│   └── presentation/
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   └── sales_analytics/
│       ├── cli.py
│       ├── data_contract.py
│       ├── quality.py
│       ├── transformations.py
│       ├── metrics.py
│       ├── pipeline.py
│       └── artifacts.py
├── tests/
├── docs/
└── app.py
```

## Execution flow

1. Load the sales dataset.
2. Validate core quality checks.
3. Clean and normalize the analytical base.
4. Compute KPIs, growth, YoY, and concentration.
5. Present outputs in a business-first dashboard flow.

## Run locally

```bash
pip install -e ".[dev]"
streamlit run app.py
```

CLI:

```bash
sales-analytics summary
sales-analytics growth --period M
sales-analytics build-artifacts
```

## Quality checks

```bash
ruff check .
pytest
mypy src
```

Current automated coverage: `90%`.

## Why this reads as more senior

- business context is explicit
- metrics are centralized instead of scattered across the UI
- data quality is visible, not implicit
- the main entrypoint stays clean
- tests support the core analytical logic

## Data source

Kaggle: [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data)

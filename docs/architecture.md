# Architecture

## Layers

- `src/sales_analytics/`: domain and data processing logic.
- `app/`: Streamlit presentation layer.
- `scripts/`: thin wrappers around official CLI commands.
- `tests/`: business, contract, and entrypoint regression coverage.

## Official execution paths

- Dashboard: `streamlit run app.py`
- Growth analysis CLI: `sales-analytics growth --period M`
- Artifact generation: `sales-analytics build-artifacts`

## Design decisions

- Raw schema validation is explicit and testable before transformations.
- Processed artifacts have a documented output contract.
- The UI consumes reusable domain logic instead of duplicating transformations.
- Legacy folders remain read-only fallback sources for backward compatibility.

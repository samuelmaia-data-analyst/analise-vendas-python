from __future__ import annotations

import pandas as pd


def _normalize_sales_frame(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
) -> pd.DataFrame:
    missing = [column for column in [date_col, sales_col] if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(missing)}")

    tmp = df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[sales_col] = pd.to_numeric(tmp[sales_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col, sales_col])

    if tmp.empty:
        raise ValueError("Nao ha linhas validas apos a normalizacao de data e valor")

    return tmp


def compute_growth_over_period(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    period: str = "M",
) -> pd.DataFrame:
    tmp = _normalize_sales_frame(df, date_col=date_col, sales_col=sales_col)
    period_map = {"M": "ME", "T": "QE", "A": "YE"}

    try:
        frequency = period_map[period.upper()]
    except KeyError as exc:
        raise ValueError("Periodo deve ser 'M', 'T' ou 'A'") from exc

    monthly = (
        tmp.set_index(date_col)[sales_col]
        .resample(frequency)
        .sum()
        .reset_index(name="total_vendas")
    )
    monthly["crescimento_%"] = monthly["total_vendas"].pct_change() * 100
    return monthly


def compute_main_metrics(
    df: pd.DataFrame,
    date_col: str = "ORDERDATE",
    sales_col: str = "SALES",
) -> dict[str, float | str]:
    monthly = compute_growth_over_period(
        df=df,
        date_col=date_col,
        sales_col=sales_col,
        period="M",
    )
    growth = monthly["crescimento_%"].dropna()

    melhor_idx = growth.idxmax() if not growth.empty else 0
    pior_idx = growth.idxmin() if not growth.empty else 0
    melhor_raw = pd.to_datetime(str(monthly.loc[melhor_idx, date_col]), errors="coerce")
    pior_raw = pd.to_datetime(str(monthly.loc[pior_idx, date_col]), errors="coerce")
    melhor = melhor_raw.strftime("%Y-%m") if pd.notna(melhor_raw) else "N/A"
    pior = pior_raw.strftime("%Y-%m") if pd.notna(pior_raw) else "N/A"

    return {
        "receita_total": float(monthly["total_vendas"].sum()),
        "crescimento_medio_pct": float(growth.mean() if not growth.empty else 0.0),
        "melhor_periodo": melhor,
        "pior_periodo": pior,
    }

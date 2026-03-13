from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SalesKpis:
    total_revenue: float
    total_orders: int
    average_order_value: float
    average_growth_pct: float
    last_period_growth_pct: float
    best_period: str
    worst_period: str
    peak_month: str
    top3_share_pct: float | None

    def to_dict(self) -> dict[str, float | int | str | None]:
        return asdict(self)


def _normalize_sales_frame(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
) -> pd.DataFrame:
    if date_col == sales_col:
        raise ValueError("A coluna de data e a coluna de valor nao podem ser iguais")

    missing = [column for column in [date_col, sales_col] if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(missing)}")

    tmp = df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[sales_col] = pd.to_numeric(tmp[sales_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col, sales_col])
    tmp = tmp.loc[tmp[sales_col] >= 0].copy()

    if tmp.empty:
        raise ValueError("Nao ha linhas validas apos a normalizacao de data e valor")

    return tmp.sort_values(date_col).reset_index(drop=True)


def _resolve_frequency(period: str) -> str:
    period_map = {"M": "ME", "T": "QE", "A": "YE"}

    try:
        return period_map[period.upper()]
    except KeyError as exc:
        raise ValueError("Periodo deve ser 'M', 'T' ou 'A'") from exc


def format_period_label(value: object) -> str:
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.notna(parsed):
        return parsed.strftime("%Y-%m")
    return str(value)


def compute_growth_over_period(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    period: str = "M",
) -> pd.DataFrame:
    tmp = _normalize_sales_frame(df, date_col=date_col, sales_col=sales_col)
    frequency = _resolve_frequency(period)

    aggregated = (
        tmp.set_index(date_col)[sales_col]
        .resample(frequency)
        .sum()
        .reset_index(name="total_vendas")
    )
    aggregated["crescimento_%"] = aggregated["total_vendas"].pct_change() * 100
    return aggregated


def compute_yoy(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    freq: str = "ME",
) -> pd.DataFrame:
    tmp = _normalize_sales_frame(df, date_col=date_col, sales_col=sales_col)

    yoy = (
        tmp.set_index(date_col)[sales_col]
        .resample(freq)
        .sum()
        .reset_index(name="total")
    )
    yoy["yoy_abs"] = yoy["total"] - yoy["total"].shift(12)
    yoy["yoy_pct"] = (yoy["total"] / yoy["total"].shift(12) - 1) * 100
    return yoy


def compute_pareto(df: pd.DataFrame, dim_col: str, value_col: str) -> pd.DataFrame:
    if dim_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Colunas obrigatorias ausentes: {dim_col}, {value_col}")

    tmp = df[[dim_col, value_col]].copy()
    tmp[value_col] = pd.to_numeric(tmp[value_col], errors="coerce")
    tmp = tmp.dropna(subset=[dim_col, value_col])

    if tmp.empty:
        return pd.DataFrame(columns=[dim_col, "total", "share_pct", "cum_share_pct", "rank"])

    pareto = (
        tmp.groupby(dim_col, dropna=False)[value_col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={value_col: "total"})
    )
    total_all = float(pareto["total"].sum())
    pareto["share_pct"] = np.where(total_all > 0, (pareto["total"] / total_all) * 100, 0.0)
    pareto["cum_share_pct"] = pareto["share_pct"].cumsum()
    pareto["rank"] = np.arange(1, len(pareto) + 1)
    return pareto


def compute_sales_kpis(
    df: pd.DataFrame,
    *,
    periodic_sales: pd.DataFrame | None = None,
    dimension_col: str | None = None,
    date_col: str = "analysis_date",
    sales_col: str = "analysis_sales",
) -> SalesKpis:
    tmp = _normalize_sales_frame(df, date_col=date_col, sales_col=sales_col)
    periodic = periodic_sales if periodic_sales is not None else compute_growth_over_period(tmp, date_col, sales_col, period="M")
    growth = periodic["crescimento_%"].dropna()

    if not growth.empty:
        best_index = growth.idxmax()
        worst_index = growth.idxmin()
        best_period = format_period_label(periodic.loc[best_index, date_col])
        worst_period = format_period_label(periodic.loc[worst_index, date_col])
        average_growth_pct = float(growth.mean())
        last_period_growth_pct = float(growth.iloc[-1])
    else:
        best_period = "N/A"
        worst_period = "N/A"
        average_growth_pct = 0.0
        last_period_growth_pct = 0.0

    monthly_seasonality = tmp.groupby(tmp[date_col].dt.month)[sales_col].sum()
    peak_month = "N/A"
    if not monthly_seasonality.empty:
        peak_period = pd.Timestamp(year=2000, month=int(monthly_seasonality.idxmax()), day=1)
        peak_month = peak_period.strftime("%b")

    total_orders = int(tmp["ORDERNUMBER"].nunique()) if "ORDERNUMBER" in tmp.columns else int(len(tmp))
    total_revenue = float(tmp[sales_col].sum())
    average_order_value = float(total_revenue / total_orders) if total_orders else 0.0

    top3_share_pct = None
    if dimension_col and dimension_col in tmp.columns:
        pareto = compute_pareto(tmp, dim_col=dimension_col, value_col=sales_col)
        if not pareto.empty:
            top3_share_pct = float(pareto["share_pct"].head(3).sum())

    return SalesKpis(
        total_revenue=total_revenue,
        total_orders=total_orders,
        average_order_value=average_order_value,
        average_growth_pct=average_growth_pct,
        last_period_growth_pct=last_period_growth_pct,
        best_period=best_period,
        worst_period=worst_period,
        peak_month=peak_month,
        top3_share_pct=top3_share_pct,
    )


def compute_main_metrics(
    df: pd.DataFrame,
    date_col: str = "ORDERDATE",
    sales_col: str = "SALES",
) -> dict[str, float | str]:
    normalized = _normalize_sales_frame(df, date_col=date_col, sales_col=sales_col)
    normalized = normalized.rename(columns={date_col: "analysis_date", sales_col: "analysis_sales"})
    kpis = compute_sales_kpis(
        normalized,
        date_col="analysis_date",
        sales_col="analysis_sales",
    )
    return {
        "receita_total": kpis.total_revenue,
        "crescimento_medio_pct": kpis.average_growth_pct,
        "melhor_periodo": kpis.best_period,
        "pior_periodo": kpis.worst_period,
    }

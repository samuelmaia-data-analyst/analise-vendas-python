from __future__ import annotations

from typing import Callable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.presentation.components import COLOR_GROWTH, COLOR_REVENUE, COLOR_YOY, PLOT_FONT
from app.presentation.data import format_currency
from src.sales_analytics import metrics as sales_metrics


@st.cache_data(show_spinner=False)
def cache_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    return data.copy()


def compute_pareto(df: pd.DataFrame, dim_col: str, value_col: str) -> pd.DataFrame:
    return sales_metrics.compute_pareto(df, dim_col, value_col)


def compute_yoy(df: pd.DataFrame, date_col: str, value_col: str, freq: str = "ME") -> pd.DataFrame:
    return sales_metrics.compute_yoy(df, date_col, value_col, freq=freq)


def format_period_label(value: object) -> str:
    return sales_metrics.format_period_label(value)


def build_executive_insights(
    receita_total: float,
    crescimento_medio: float,
    mes_pico: str,
    top3_share: float | None,
    melhor_periodo: str,
    pior_periodo: str,
    lang: str,
    tr: Callable[..., str],
) -> list[str]:
    insights = [
        tr("insight_revenue", lang, value=format_currency(receita_total, "$")),
        tr("insight_peak", lang, value=mes_pico),
    ]

    direcao = tr("expansion", lang) if crescimento_medio >= 0 else tr("retraction", lang)
    insights.append(tr("insight_growth", lang, direction=direcao, value=crescimento_medio))

    if top3_share is not None:
        insights.append(tr("insight_top3", lang, value=top3_share))

    insights.append(tr("insight_range", lang, best=melhor_periodo, worst=pior_periodo))
    return insights


def classify_growth_signal(value: float, lang: str, tr: Callable[..., str]) -> tuple[str, str]:
    if pd.isna(value):
        return tr("na", lang), "signal-warn"
    if value >= 8:
        return tr("growth_strong", lang), "signal-good"
    if value >= 2:
        return tr("growth_moderate", lang), "signal-warn"
    return tr("growth_weak", lang), "signal-risk"


def classify_concentration_signal(value: float | None, lang: str, tr: Callable[..., str]) -> tuple[str, str]:
    if value is None or pd.isna(value):
        return tr("na", lang), "signal-warn"
    if value <= 50:
        return tr("risk_low", lang), "signal-good"
    if value <= 70:
        return tr("risk_moderate", lang), "signal-warn"
    return tr("risk_high", lang), "signal-risk"


def build_revenue_chart(periodic_sales: pd.DataFrame, x_col: str) -> go.Figure:
    fig = px.area(periodic_sales, x=x_col, y="total_vendas", template="plotly_white")
    fig.update_traces(line_color=COLOR_REVENUE)
    fig.update_layout(
        title="Receita por periodo",
        xaxis_title="Periodo",
        yaxis_title="Receita",
        hovermode="x unified",
        height=400,
        font=dict(family=PLOT_FONT),
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return fig


def build_growth_chart(periodic_sales: pd.DataFrame, x_col: str) -> go.Figure:
    fig = px.bar(
        periodic_sales.dropna(subset=["crescimento_%"]),
        x=x_col,
        y="crescimento_%",
        template="plotly_white",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.6)
    fig.update_traces(marker_color=COLOR_GROWTH)
    fig.update_layout(
        title="Crescimento por periodo",
        xaxis_title="Periodo",
        yaxis_title="Crescimento (%)",
        height=400,
        font=dict(family=PLOT_FONT),
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return fig


def build_yoy_chart(yoy_sales: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not yoy_sales.empty:
        x_col = yoy_sales.columns[0]
        fig.add_trace(
            go.Scatter(
                x=yoy_sales[x_col],
                y=yoy_sales["total"],
                mode="lines+markers",
                name="Total mensal",
                line=dict(color=COLOR_REVENUE, width=3),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=yoy_sales[x_col],
                y=yoy_sales["yoy_pct"],
                mode="lines+markers",
                name="YoY (%)",
                yaxis="y2",
                line=dict(color=COLOR_YOY, width=2.5),
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=430,
        xaxis_title="Mes",
        yaxis=dict(title="Total mensal"),
        yaxis2=dict(title="YoY (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family=PLOT_FONT),
        margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig

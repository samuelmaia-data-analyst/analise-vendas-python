from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from app.presentation.analytics import (
    build_executive_insights,
    build_growth_chart,
    build_revenue_chart,
    build_yoy_chart,
    cache_dataframe,
    classify_concentration_signal,
    classify_growth_signal,
)
from app.presentation.components import (
    APP_ICON,
    APP_TITLE,
    LAYOUT,
    build_pareto_chart,
    inject_css,
    render_header,
    render_lead_strip,
    render_proof_strip,
)
from app.presentation.data import (
    carregar_csv_upload,
    carregar_dados,
    detect_date_columns,
    detect_value_columns,
    filter_value_columns,
    format_currency,
    suggest_dimension_columns,
    validate_upload_frame,
)
from app.presentation.i18n import LANG_OPTIONS, tr
from src.sales_analytics.exceptions import SalesAnalyticsError
from src.sales_analytics.logging_utils import get_logger
from src.sales_analytics.metrics import format_period_label
from src.sales_analytics.pipeline import run_sales_analysis
from src.sales_analytics.settings import get_app_settings

LOGGER = get_logger(__name__)
SETTINGS = get_app_settings()

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)
inject_css()


def render_quality_table(quality_report: object) -> None:
    quality_df = pd.DataFrame(
        [
            {"Indicador": "Linhas totais", "Valor": quality_report.total_rows},
            {"Indicador": "Linhas validas", "Valor": quality_report.valid_rows},
            {"Indicador": "Linhas duplicadas", "Valor": quality_report.duplicate_rows},
            {"Indicador": "Datas nulas", "Valor": quality_report.null_date_rows},
            {"Indicador": "Datas invalidas", "Valor": quality_report.invalid_date_rows},
            {"Indicador": "Vendas nulas", "Valor": quality_report.null_sales_rows},
            {"Indicador": "Vendas invalidas", "Valor": quality_report.invalid_sales_rows},
            {"Indicador": "Vendas negativas", "Valor": quality_report.negative_sales_rows},
            {"Indicador": "Vendas zeradas", "Valor": quality_report.zero_sales_rows},
        ]
    )
    st.dataframe(quality_df, width="stretch", hide_index=True)

    if quality_report.warnings:
        for warning in quality_report.warnings:
            st.warning(warning)
    else:
        st.success("Nenhum alerta critico de qualidade encontrado.")


with st.sidebar:
    selected_lang_label = st.selectbox("Language / Idioma", list(LANG_OPTIONS.keys()), index=0)
    lang = LANG_OPTIONS[selected_lang_label]
    st.session_state["lang"] = lang

    st.markdown(f"## {tr('settings', lang)}")
    uploaded_file = st.file_uploader(
        tr("upload_csv", lang),
        type=["csv"],
        help=tr("upload_help", lang),
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > SETTINGS.max_upload_mb:
            st.error(tr("file_too_large", lang, size=file_size_mb))
            st.stop()

        upload_key = f"{uploaded_file.name}:{len(file_bytes)}"
        cached_key = st.session_state.get("upload_key")
        cached_df = st.session_state.get("upload_df")
        if cached_key == upload_key and isinstance(cached_df, pd.DataFrame):
            df = cached_df
        else:
            with st.spinner(tr("loading_file", lang)):
                df = carregar_csv_upload(file_bytes)
            st.session_state["upload_key"] = upload_key
            st.session_state["upload_df"] = df

        if df.empty:
            st.error(tr("empty_file", lang))
            st.stop()

        is_valid_upload, upload_error = validate_upload_frame(
            df,
            max_rows=SETTINGS.max_upload_rows,
            max_columns=SETTINGS.max_upload_columns,
        )
        if not is_valid_upload and upload_error == "too_many_rows":
            st.error(tr("file_too_many_rows", lang, limit=SETTINGS.max_upload_rows))
            st.stop()
        if not is_valid_upload and upload_error == "too_many_columns":
            st.error(tr("file_too_many_columns", lang, limit=SETTINGS.max_upload_columns))
            st.stop()

        dados_reais = True
        origem = uploaded_file.name
    else:
        df, dados_reais, origem = carregar_dados()

    st.markdown(f"### {tr('base', lang)}")
    c1, c2 = st.columns(2)
    with c1:
        st.metric(tr("rows", lang), f"{len(df):,}")
    with c2:
        st.metric(tr("cols", lang), len(df.columns))

    st.caption(f"{tr('origin', lang)}: {origem if origem else tr('sample', lang)}")

    st.markdown(f"### {tr('mapping', lang)}")
    columns = df.columns.tolist()
    date_options = detect_date_columns(columns) or columns
    date_col = st.selectbox(tr("date_col", lang), date_options, index=0)

    value_options = filter_value_columns(detect_value_columns(df), date_col)
    if not value_options:
        st.error(tr("no_numeric", lang))
        st.stop()
    sales_col = st.selectbox(tr("value_col", lang), value_options, index=0)
    if sales_col == date_col:
        st.error(tr("same_date_value_col", lang))
        st.stop()

    st.markdown(f"### {tr('analysis', lang)}")
    period_labels = [tr("monthly", lang), tr("quarterly", lang), tr("yearly", lang)]
    selected_period = st.selectbox(tr("periodicity", lang), period_labels, index=0)
    period_map = {
        tr("monthly", lang): "M",
        tr("quarterly", lang): "T",
        tr("yearly", lang): "A",
    }

    dimension_options = suggest_dimension_columns(df)
    if dimension_options:
        dimension_col = st.selectbox(tr("pareto_dim", lang), dimension_options, index=0)
        top_n_pareto = st.slider(tr("pareto_topn", lang), min_value=5, max_value=30, value=12, step=1)
    else:
        dimension_col = None
        top_n_pareto = 12
        st.info(tr("no_categorical", lang))


try:
    render_header(origem, dados_reais, lang, tr)

    with st.spinner(tr("spinner_calc", lang)):
        analysis = run_sales_analysis(
            df=cache_dataframe(df),
            date_col=date_col,
            sales_col=sales_col,
            dimension_col=dimension_col,
            period=period_map[selected_period],
        )

    periodic_sales = analysis.periodic_sales
    cleaned_data = analysis.cleaned_data
    yoy_sales = analysis.yoy_sales
    pareto_sales = analysis.pareto_sales
    kpis = analysis.kpis

    if periodic_sales.empty:
        st.warning(tr("warn_no_aggregation", lang))
        st.stop()

    receita_total = kpis.total_revenue
    crescimento_medio = kpis.average_growth_pct
    top3_share = kpis.top3_share_pct
    mes_pico = kpis.peak_month
    melhor_periodo_exec = kpis.best_period
    pior_periodo_exec = kpis.worst_period

    insights = build_executive_insights(
        receita_total=receita_total,
        crescimento_medio=crescimento_medio,
        mes_pico=mes_pico,
        top3_share=top3_share,
        melhor_periodo=melhor_periodo_exec,
        pior_periodo=pior_periodo_exec,
        lang=lang,
        tr=tr,
    )

    crescimento_label, crescimento_class = classify_growth_signal(crescimento_medio, lang, tr)
    concentracao_label, concentracao_class = classify_concentration_signal(top3_share, lang, tr)
    momentum_label, momentum_class = classify_growth_signal(kpis.last_period_growth_pct, lang, tr)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(tr("revenue_total", lang), format_currency(receita_total, "$"))
    with k2:
        st.metric(tr("avg_growth", lang), f"{crescimento_medio:.1f}%")
    with k3:
        st.metric("Pedidos", f"{kpis.total_orders:,}")
    with k4:
        st.metric(tr("top3", lang), f"{top3_share:.1f}%" if top3_share is not None else tr("na", lang))

    render_proof_strip(
        periodos=int(len(periodic_sales)),
        dimensoes=int(len(cleaned_data.columns)),
        top3_share=top3_share,
        crescimento_medio=crescimento_medio,
        lang=lang,
        tr=tr,
    )
    render_lead_strip(
        receita_total=receita_total,
        crescimento_medio=crescimento_medio,
        top3_share=top3_share,
        dados_reais=dados_reais,
        lang=lang,
        tr=tr,
        format_currency=format_currency,
    )

    st.markdown(
        f"<div class='section-card'><h4 style='margin-top:0'>{tr('snapshot', lang)}</h4><ul class='snapshot-list'>"
        + "".join(f"<li>{item}</li>" for item in insights)
        + "</ul></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class='signal-grid'>
    <div class='signal-card {crescimento_class}'>
        <div class='signal-title'>{tr('signal_growth', lang)}</div>
        <div class='signal-value'>{crescimento_label}</div>
    </div>
    <div class='signal-card {concentracao_class}'>
        <div class='signal-title'>{tr('signal_concentration', lang)}</div>
        <div class='signal-value'>{concentracao_label}</div>
    </div>
    <div class='signal-card {momentum_class}'>
        <div class='signal-title'>{tr('signal_momentum', lang)}</div>
        <div class='signal-value'>{momentum_label}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    tab_overview, tab_trend, tab_concentration, tab_yoy, tab_quality = st.tabs(
        [tr("tabs_exec", lang), tr("tabs_growth", lang), tr("tabs_pareto", lang), tr("tabs_yoy", lang), "Qualidade e dados"]
    )

    with tab_overview:
        st.caption("Primeiro a leitura executiva: tamanho da receita, crescimento e ponto de concentracao.")
        left_col, right_col = st.columns(2)
        with left_col:
            st.plotly_chart(build_revenue_chart(periodic_sales, periodic_sales.columns[0]), width="stretch")
        with right_col:
            st.plotly_chart(build_growth_chart(periodic_sales, periodic_sales.columns[0]), width="stretch")

        summary_df = pd.DataFrame(
            [
                {"Indicador": "Receita total", "Valor": format_currency(kpis.total_revenue, "$")},
                {"Indicador": "Pedidos", "Valor": f"{kpis.total_orders:,}"},
                {"Indicador": "Ticket medio", "Valor": format_currency(kpis.average_order_value, "$")},
                {"Indicador": "Melhor periodo", "Valor": melhor_periodo_exec},
                {"Indicador": "Pior periodo", "Valor": pior_periodo_exec},
            ]
        )
        st.dataframe(summary_df, width="stretch", hide_index=True)

    with tab_trend:
        st.caption("Depois a leitura temporal: performance recorrente, variacao recente e estabilidade.")
        c1, c2, c3, c4 = st.columns(4)
        latest_revenue = float(periodic_sales["total_vendas"].iloc[-1]) if len(periodic_sales) else np.nan
        growth_delta = (
            float(periodic_sales["crescimento_%"].iloc[-1] - periodic_sales["crescimento_%"].iloc[-2])
            if len(periodic_sales) > 1 and pd.notna(periodic_sales["crescimento_%"].iloc[-1]) and pd.notna(periodic_sales["crescimento_%"].iloc[-2])
            else np.nan
        )
        with c1:
            st.metric(tr("avg_growth", lang), f"{kpis.average_growth_pct:.1f}%", delta=f"{growth_delta:.1f} pp" if pd.notna(growth_delta) else None)
        with c2:
            st.metric(tr("last_period", lang), format_currency(latest_revenue, "$") if pd.notna(latest_revenue) else tr("na", lang))
        with c3:
            st.metric(tr("best_period", lang), melhor_periodo_exec)
        with c4:
            st.metric(tr("worst_period", lang), pior_periodo_exec)

        trend_table = periodic_sales.rename(
            columns={
                periodic_sales.columns[0]: "Periodo",
                "total_vendas": "Receita",
                "crescimento_%": "Crescimento (%)",
            }
        ).copy()
        trend_table["Periodo"] = trend_table["Periodo"].map(format_period_label)
        trend_table["Receita"] = trend_table["Receita"].map(lambda value: format_currency(value, "$"))
        trend_table["Crescimento (%)"] = trend_table["Crescimento (%)"].map(
            lambda value: f"{value:.2f}%" if pd.notna(value) else "-"
        )
        st.dataframe(trend_table, width="stretch", hide_index=True)

    with tab_concentration:
        st.caption("A concentracao mostra quanto da receita depende de poucas categorias, produtos ou clientes.")
        if not pareto_sales.empty and dimension_col:
            st.plotly_chart(build_pareto_chart(pareto_sales, dimension_col, top_n=top_n_pareto), width="stretch")
            show_df = pareto_sales.copy()
            show_df["total"] = show_df["total"].map(lambda value: format_currency(value, "$"))
            show_df["share_pct"] = show_df["share_pct"].map(lambda value: f"{value:.2f}%")
            show_df["cum_share_pct"] = show_df["cum_share_pct"].map(lambda value: f"{value:.2f}%")
            st.dataframe(show_df[[dimension_col, "total", "share_pct", "cum_share_pct"]], width="stretch", hide_index=True)
        else:
            st.info(tr("pareto_enable", lang))

    with tab_yoy:
        st.caption("Por fim, a comparacao YoY ajuda a separar crescimento estrutural de ruido pontual.")
        yy1, yy2, yy3 = st.columns(3)
        total_ultimo = yoy_sales["total"].iloc[-1] if len(yoy_sales) else np.nan
        yoy_pct_last = yoy_sales["yoy_pct"].iloc[-1] if len(yoy_sales) else np.nan
        yoy_abs_last = yoy_sales["yoy_abs"].iloc[-1] if len(yoy_sales) else np.nan

        with yy1:
            st.metric(tr("total_last_month", lang), format_currency(total_ultimo, "$") if pd.notna(total_ultimo) else tr("na", lang))
        with yy2:
            st.metric(tr("yoy_last_month", lang), f"{yoy_pct_last:.2f}%" if pd.notna(yoy_pct_last) else tr("na", lang))
        with yy3:
            st.metric(tr("yoy_abs_last_month", lang), format_currency(yoy_abs_last, "$") if pd.notna(yoy_abs_last) else tr("na", lang))

        st.plotly_chart(build_yoy_chart(yoy_sales), width="stretch")
        yoy_view = yoy_sales.rename(columns={yoy_sales.columns[0]: "Periodo"}).copy() if not yoy_sales.empty else yoy_sales
        if not yoy_view.empty:
            yoy_view["Periodo"] = yoy_view["Periodo"].map(format_period_label)
            yoy_view["total"] = yoy_view["total"].map(lambda value: format_currency(value, "$"))
            yoy_view["yoy_abs"] = yoy_view["yoy_abs"].map(lambda value: format_currency(value, "$") if pd.notna(value) else "-")
            yoy_view["yoy_pct"] = yoy_view["yoy_pct"].map(lambda value: f"{value:.2f}%" if pd.notna(value) else "-")
            st.dataframe(yoy_view, width="stretch", hide_index=True)
        else:
            st.info(tr("yoy_no_history", lang))

    with tab_quality:
        st.caption("Esta camada deixa explicito o quanto a analise depende de limpeza e quais ajustes foram feitos nos dados.")
        render_quality_table(analysis.quality_report)
        st.dataframe(cleaned_data.head(20), width="stretch", hide_index=True)

        csv_data = periodic_sales.to_csv(index=False)
        st.download_button(
            label=tr("download_csv", lang),
            data=csv_data,
            file_name=f"analise_vendas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
except (SalesAnalyticsError, ValueError) as exc:
    LOGGER.error("Falha na analise do dashboard: %s", exc)
    st.error(tr("analysis_error", st.session_state.get("lang", "en"), error=str(exc)))
    st.exception(exc)

st.markdown("---")
st.markdown(
    f"""
<div style='text-align:center; color:#334155; padding:0.8rem;'>
    {tr("footer", st.session_state.get("lang", "en"))} <a href='https://github.com/samuelmaia-analytics' target='_blank'>Samuel Maia</a>
</div>
""",
    unsafe_allow_html=True,
)

# app.py
import os
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from scripts.analise_crescimento import calcular_crescimento


# =========================
# CONFIGURAÇÕES GERAIS
# =========================
APP_TITLE = "Análise de Vendas - Samuel Maia"
APP_ICON = "📈"
LAYOUT = "wide"
COLOR_REVENUE = "#1d4ed8"
COLOR_GROWTH = "#ea580c"
COLOR_PARETO_BAR = "#0284c7"
COLOR_PARETO_LINE = "#d97706"
COLOR_YOY = "#7c3aed"
PLOT_FONT = "Trebuchet MS, Segoe UI, sans-serif"


# =========================
# FUNÇÕES UTILITÁRIAS
# =========================
def format_currency(value: float, symbol: str = "$") -> str:
    """Formata moeda em padrão internacional simples."""
    try:
        return f"{symbol}{value:,.2f}"
    except Exception:
        return "N/A"


def safe_to_datetime(series: pd.Series) -> pd.Series:
    """Converte para datetime com coerção segura."""
    return pd.to_datetime(series, errors="coerce")


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Converte para numérico com coerção segura."""
    return pd.to_numeric(series, errors="coerce")


def month_name_pt(month_num: int) -> str:
    meses = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }
    return meses.get(int(month_num), str(month_num))


def detect_date_columns(columns: list[str]) -> list[str]:
    """Sugere colunas de data."""
    return [
        c
        for c in columns
        if any(t in c.lower() for t in ["date", "data", "dia", "mes", "orderdate"])
    ]


def detect_value_columns(df: pd.DataFrame) -> list[str]:
    """Sugere colunas numéricas de valor (vendas/receita)."""
    cols = df.columns.tolist()
    by_name = [
        c
        for c in cols
        if any(
            t in c.lower()
            for t in ["sales", "venda", "price", "total", "valor", "receita"]
        )
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Prioriza sugestão por nome e depois numéricas
    merged = list(dict.fromkeys(by_name + numeric_cols))
    return merged


def suggest_dimension_columns(df: pd.DataFrame) -> list[str]:
    """Sugere colunas categóricas para Pareto / Top 3 concentração."""
    cols = df.columns.tolist()
    hints = []
    for c in [
        "PRODUCTLINE",
        "PRODUTO",
        "CATEGORIA",
        "PRODUCT",
        "CATEGORY",
        "COUNTRY",
        "PAIS",
        "REGIAO",
        "REGION",
        "CUSTOMERNAME",
        "CLIENTE",
    ]:
        if c in cols:
            hints.append(c)

    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    merged = list(dict.fromkeys(hints + cat_cols))
    return merged


@st.cache_data
def criar_dados_exemplo():
    """Cria dados de exemplo realistas para fallback."""
    np.random.seed(42)

    datas = pd.date_range("2023-01-01", "2024-12-31", freq="D")
    tendencia = np.linspace(1000, 2000, len(datas))
    sazonalidade = 500 * np.sin(2 * np.pi * np.arange(len(datas)) / 365)
    ruido = np.random.normal(0, 100, len(datas))

    vendas = np.maximum(tendencia + sazonalidade + ruido, 500)

    produtos = [f"PROD_{i:03d}" for i in range(1, 21)]
    clientes = [f"CLI_{i:03d}" for i in range(1, 51)]

    df = pd.DataFrame(
        {
            "DATA": datas,
            "VENDAS": vendas.astype(int),
            "QUANTIDADE": np.random.randint(1, 50, len(datas)),
            "PRODUTO": np.random.choice(produtos, len(datas)),
            "CLIENTE": np.random.choice(clientes, len(datas)),
            "CATEGORIA": np.random.choice(
                ["Eletrônicos", "Móveis", "Roupas", "Livros"], len(datas)
            ),
        }
    )
    return df


@st.cache_data
def carregar_dados():
    """Carrega dados locais se existirem; caso contrário, usa dados de exemplo."""
    possiveis_caminhos = [
        "data/processed/fato_vendas.csv",
        "legacy/dados_processados/fato_vendas.csv",
        "data/raw/fato_vendas.csv",
        "legacy/dados/fato_vendas.csv",
        "./data/processed/fato_vendas.csv",
        "./legacy/dados_processados/fato_vendas.csv",
        "./data/raw/fato_vendas.csv",
        "./legacy/dados/fato_vendas.csv",
    ]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            df = pd.read_csv(caminho)
            return df, True, caminho

    return criar_dados_exemplo(), False, None


def compute_yoy(
    df: pd.DataFrame, date_col: str, value_col: str, freq: str = "ME"
) -> pd.DataFrame:
    """
    Calcula YoY (Year-over-Year) com agregação mensal por padrão.
    Retorna dataframe com colunas: periodo, total, yoy_abs, yoy_pct.
    """
    tmp = df[[date_col, value_col]].copy()
    tmp[date_col] = safe_to_datetime(tmp[date_col])
    tmp[value_col] = safe_to_numeric(tmp[value_col])
    tmp = tmp.dropna(subset=[date_col, value_col])

    # Agregação mensal (month-end). (Evita 'M' deprecation)
    agg = (
        tmp.set_index(date_col)
        .resample(freq)[value_col]
        .sum()
        .reset_index()
        .rename(columns={value_col: "total"})
    )
    agg["yoy_abs"] = agg["total"] - agg["total"].shift(12)
    agg["yoy_pct"] = (agg["total"] / agg["total"].shift(12) - 1) * 100
    return agg


def compute_pareto(df: pd.DataFrame, dim_col: str, value_col: str) -> pd.DataFrame:
    """Calcula Pareto (valor por dimensão + % acumulado)."""
    tmp = df[[dim_col, value_col]].copy()
    tmp[value_col] = safe_to_numeric(tmp[value_col])
    tmp = tmp.dropna(subset=[dim_col, value_col])

    pareto = (
        tmp.groupby(dim_col)[value_col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={value_col: "total"})
    )
    total_all = pareto["total"].sum()
    pareto["share_pct"] = (pareto["total"] / total_all) * 100 if total_all else 0
    pareto["cum_share_pct"] = pareto["share_pct"].cumsum()
    pareto["rank"] = np.arange(1, len(pareto) + 1)
    return pareto


def build_pareto_chart(
    pareto_df: pd.DataFrame, dim_col: str, top_n: int = 15
) -> go.Figure:
    """Gera gráfico de Pareto (barras + linha de % acumulado)."""
    plot_df = pareto_df.head(top_n).copy()

    fig = go.Figure()

    # Barras: total por categoria
    fig.add_trace(
        go.Bar(
            x=plot_df[dim_col].astype(str),
            y=plot_df["total"],
            name="Total",
            marker_color=COLOR_PARETO_BAR,
        )
    )

    # Linha: acumulado %
    fig.add_trace(
        go.Scatter(
            x=plot_df[dim_col].astype(str),
            y=plot_df["cum_share_pct"],
            name="% Acumulado",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=COLOR_PARETO_LINE, width=2.5),
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=420,
        xaxis_title=dim_col,
        yaxis=dict(title="Total", showgrid=True),
        yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family=PLOT_FONT),
        margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig


def build_executive_insights(
    receita_total: float,
    crescimento_medio: float,
    mes_pico: str,
    top3_share: float | None,
    melhor_periodo: str,
    pior_periodo: str,
) -> list[str]:
    insights = [
        f"Receita consolidada no periodo analisado: {format_currency(receita_total, '$')}.",
        f"Mes de maior sazonalidade de receita: {mes_pico}.",
    ]

    if pd.notna(crescimento_medio):
        direcao = "expansao" if crescimento_medio >= 0 else "retracao"
        insights.append(
            f"Crescimento medio em {direcao}: {crescimento_medio:.1f}% por periodo."
        )

    if top3_share is not None:
        insights.append(
            f"Concentracao top 3 em {top3_share:.1f}% da receita: monitorar dependencia comercial."
        )

    insights.append(
        f"Faixa de performance: melhor periodo em {melhor_periodo} e pior em {pior_periodo}."
    )
    return insights


def classify_growth_signal(value: float) -> tuple[str, str]:
    if pd.isna(value):
        return "N/A", "signal-warn"
    if value >= 8:
        return "Tração Forte", "signal-good"
    if value >= 2:
        return "Tração Moderada", "signal-warn"
    return "Tração Fraca", "signal-risk"


def classify_concentration_signal(value: float | None) -> tuple[str, str]:
    if value is None or pd.isna(value):
        return "N/A", "signal-warn"
    if value <= 50:
        return "Risco Baixo", "signal-good"
    if value <= 70:
        return "Risco Moderado", "signal-warn"
    return "Risco Alto", "signal-risk"


# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)

# CSS
st.markdown(
    """
<style>
    :root {
        --brand-ink: #0f172a;
        --brand-muted: #475569;
        --brand-soft: #fff4e6;
        --brand-soft-2: #ffe8cc;
    }
    .hero-wrap {
        background: linear-gradient(120deg, var(--brand-soft) 0%, var(--brand-soft-2) 100%);
        border: 1px solid #ffd8a8;
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
    }
    .hero-title {
        margin: 0;
        color: var(--brand-ink);
        font-size: 2.1rem;
        line-height: 1.2;
        font-weight: 750;
    }
    .hero-subtitle {
        margin: 0.45rem 0 0 0;
        color: var(--brand-muted);
        font-size: 1rem;
    }
    .exec-box {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 1rem;
    }
    .signal-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.6rem;
        margin-bottom: 1rem;
    }
    .signal-card {
        border-radius: 10px;
        padding: 0.75rem 0.85rem;
        border: 1px solid transparent;
    }
    .signal-title {
        font-size: 0.8rem;
        color: #334155;
        margin-bottom: 0.2rem;
    }
    .signal-value {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
    }
    .signal-good {
        background: #ecfdf5;
        border-color: #86efac;
    }
    .signal-warn {
        background: #fffbeb;
        border-color: #fde68a;
    }
    .signal-risk {
        background: #fef2f2;
        border-color: #fca5a5;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
<div class='hero-wrap'>
    <h1 class='hero-title'>Sales Analytics Command Center</h1>
    <p class='hero-subtitle'>Painel executivo para crescimento, concentracao, sazonalidade e decisao orientada por dados.</p>
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## ⚙️ Configurações")

    uploaded_file = st.file_uploader(
        "📤 Upload seu CSV",
        type=["csv"],
        help="Faça upload do seu arquivo de vendas",
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
        dados_reais = True
        origem = uploaded_file.name
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
    else:
        df, dados_reais, origem = carregar_dados()
        if dados_reais and origem:
            st.success(f"✅ Dados locais carregados: {origem}")
        else:
            st.info("ℹ️ Usando dados de exemplo (simulados)")

    st.markdown("---")
    st.markdown("### 📋 Sobre os dados")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Registros", f"{len(df):,}")
    with c2:
        st.metric("Colunas", len(df.columns))

    tipo_dados = "**Dados Reais**" if dados_reais else "**Dados de Exemplo**"
    st.markdown(f"Tipo: {tipo_dados}")

    st.markdown("---")
    st.markdown("### 🔧 Mapeamento de Colunas")

    colunas = df.columns.tolist()

    # Data
    data_options = detect_date_columns(colunas) or colunas
    coluna_data = st.selectbox("📅 Coluna de data", data_options, index=0)

    # Valor
    valor_options = detect_value_columns(df)
    if not valor_options:
        st.error("❌ Nenhuma coluna numérica encontrada para usar como valor.")
        st.stop()

    coluna_valor = st.selectbox("💰 Coluna de valor", valor_options, index=0)

    # Período de crescimento
    st.markdown("---")
    st.markdown("### 📊 Análise de Crescimento")
    periodo = st.selectbox("Período", ["Mensal", "Trimestral", "Anual"], index=0)

    periodo_map = {"Mensal": "M", "Trimestral": "T", "Anual": "A"}

    # Dimensão Pareto / Top3
    st.markdown("---")
    st.markdown("### 🧠 Métricas Executivas")
    dim_options = suggest_dimension_columns(df)
    if dim_options:
        dim_concentracao = st.selectbox(
            "📌 Dimensão para Pareto/Top 3", dim_options, index=0
        )
        top_n_pareto = st.slider(
            "📌 Top N no Pareto", min_value=5, max_value=30, value=15, step=1
        )
    else:
        dim_concentracao = None
        top_n_pareto = 15
        st.info("ℹ️ Nenhuma coluna categórica encontrada para Pareto/Top 3.")


# =========================
# MAIN
# =========================
try:
    df_analise = df.copy()

    # Converte data/valor
    df_analise[coluna_data] = safe_to_datetime(df_analise[coluna_data])
    df_analise[coluna_valor] = safe_to_numeric(df_analise[coluna_valor])

    df_analise = df_analise.dropna(subset=[coluna_data, coluna_valor])

    # Crescimento (usa sua função existente)
    with st.spinner("🔄 Calculando análise de crescimento..."):
        resultado = calcular_crescimento(
            df_analise,
            coluna_data=coluna_data,
            coluna_valor=coluna_valor,
            periodo=periodo_map[periodo],
        )

    st.success("✅ Análise concluída!")

    # =========================
    # MÉTRICAS EXECUTIVAS
    # =========================
    st.markdown("## 🧾 Métricas Executivas")

    receita_total = df_analise[coluna_valor].sum()

    mes_pico_num = (
        df_analise.groupby(df_analise[coluna_data].dt.month)[coluna_valor]
        .sum()
        .idxmax()
    )
    mes_pico = f"{month_name_pt(int(mes_pico_num))} ({int(mes_pico_num)})"

    top3_share = None
    top3_labels = None

    if dim_concentracao and dim_concentracao in df_analise.columns:
        df_tmp = df_analise.dropna(subset=[dim_concentracao])
        if len(df_tmp) > 0:
            top3 = (
                df_tmp.groupby(dim_concentracao)[coluna_valor]
                .sum()
                .sort_values(ascending=False)
                .head(3)
            )
            top3_share = (top3.sum() / receita_total) * 100 if receita_total else 0
            top3_labels = ", ".join([str(x) for x in top3.index.tolist()])

    crescimento_medio = resultado["crescimento_%"].mean()
    crescimento_valid = resultado.dropna(subset=["crescimento_%"])
    if not crescimento_valid.empty:
        melhor_periodo_exec = str(
            crescimento_valid.loc[
                crescimento_valid["crescimento_%"].idxmax(), coluna_data
            ]
        )
        pior_periodo_exec = str(
            crescimento_valid.loc[
                crescimento_valid["crescimento_%"].idxmin(), coluna_data
            ]
        )
    else:
        melhor_periodo_exec = "N/A"
        pior_periodo_exec = "N/A"

    insights = build_executive_insights(
        receita_total=receita_total,
        crescimento_medio=float(crescimento_medio)
        if pd.notna(crescimento_medio)
        else np.nan,
        mes_pico=mes_pico,
        top3_share=top3_share,
        melhor_periodo=melhor_periodo_exec,
        pior_periodo=pior_periodo_exec,
    )

    st.markdown("## Executive Snapshot")
    insights_html = "".join([f"<li>{item}</li>" for item in insights])
    st.markdown(
        f"<div class='exec-box'><ul>{insights_html}</ul></div>",
        unsafe_allow_html=True,
    )

    crescimento_label, crescimento_class = classify_growth_signal(
        float(crescimento_medio) if pd.notna(crescimento_medio) else np.nan
    )
    concentracao_label, concentracao_class = classify_concentration_signal(top3_share)
    ult_crescimento = (
        float(resultado["crescimento_%"].iloc[-1])
        if len(resultado) and pd.notna(resultado["crescimento_%"].iloc[-1])
        else np.nan
    )
    momentum_label, momentum_class = classify_growth_signal(ult_crescimento)

    st.markdown(
        f"""
<div class='signal-grid'>
    <div class='signal-card {crescimento_class}'>
        <div class='signal-title'>Sinal de Crescimento Medio</div>
        <div class='signal-value'>{crescimento_label}</div>
    </div>
    <div class='signal-card {concentracao_class}'>
        <div class='signal-title'>Sinal de Concentracao Top 3</div>
        <div class='signal-value'>{concentracao_label}</div>
    </div>
    <div class='signal-card {momentum_class}'>
        <div class='signal-title'>Sinal de Momentum Atual</div>
        <div class='signal-value'>{momentum_label}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Receita Total", format_currency(receita_total, "$"))
    with k2:
        st.metric("Pico Sazonal", mes_pico)
    with k3:
        if top3_share is not None:
            st.metric("Concentração Top 3", f"{top3_share:.1f}%")
            if top3_labels:
                st.caption(f"Top 3 em **{dim_concentracao}**: {top3_labels}")
        else:
            st.metric("Concentração Top 3", "N/A")
            st.caption("Selecione uma dimensão categórica no menu lateral.")

    st.markdown("---")

    # =========================
    # MÉTRICAS DE CRESCIMENTO (já existente)
    # =========================
    st.markdown("## 📈 Métricas de Crescimento")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        delta = (
            resultado["crescimento_%"].iloc[-1] - resultado["crescimento_%"].iloc[-2]
            if len(resultado) > 1
            else 0
        )
        st.metric(
            "Crescimento Médio",
            f"{crescimento_medio:.1f}%" if not pd.isna(crescimento_medio) else "N/A",
            delta=f"{delta:.1f} pp" if not pd.isna(delta) else None,
        )

    with c2:
        ultimo_valor = resultado["total_vendas"].iloc[-1] if len(resultado) > 0 else 0
        st.metric("Último Período", f"${ultimo_valor:,.0f}")

    with c3:
        melhor_cresc = resultado["crescimento_%"].max()
        melhor_periodo = (
            resultado.loc[resultado["crescimento_%"].idxmax(), coluna_data]
            if not pd.isna(melhor_cresc)
            else "N/A"
        )
        st.metric(
            "Melhor Período",
            f"{melhor_cresc:.1f}%" if not pd.isna(melhor_cresc) else "N/A",
            delta=f"em {melhor_periodo}" if melhor_periodo != "N/A" else None,
        )

    with c4:
        pior_cresc = resultado["crescimento_%"].min()
        pior_periodo = (
            resultado.loc[resultado["crescimento_%"].idxmin(), coluna_data]
            if not pd.isna(pior_cresc)
            else "N/A"
        )
        st.metric(
            "Pior Período",
            f"{pior_cresc:.1f}%" if not pd.isna(pior_cresc) else "N/A",
            delta=f"em {pior_periodo}" if pior_periodo != "N/A" else None,
        )

    st.markdown("---")

    # =========================
    # GRÁFICOS PRINCIPAIS
    # =========================
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### 💰 Evolução das Vendas")
        fig_vendas = px.line(
            resultado,
            x=coluna_data,
            y="total_vendas",
            markers=True,
            line_shape="spline",
            template="plotly_white",
        )

        fig_vendas.update_layout(
            xaxis_title="Período",
            yaxis_title="Total",
            hovermode="x unified",
            height=420,
            font=dict(family=PLOT_FONT),
        )
        fig_vendas.update_traces(
            line=dict(color=COLOR_REVENUE, width=3), marker=dict(size=6)
        )
        st.plotly_chart(fig_vendas, use_container_width=True)

    with g2:
        st.markdown("### 📊 Taxa de Crescimento")
        fig_cresc = px.bar(
            resultado.dropna(subset=["crescimento_%"]),
            x=coluna_data,
            y="crescimento_%",
            template="plotly_white",
        )
        fig_cresc.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig_cresc.update_traces(marker_color=COLOR_GROWTH)
        fig_cresc.update_layout(
            xaxis_title="Período",
            yaxis_title="Crescimento (%)",
            height=420,
            font=dict(family=PLOT_FONT),
        )
        st.plotly_chart(fig_cresc, use_container_width=True)

    st.markdown("---")

    # =========================
    # PARETO AUTOMÁTICO
    # =========================
    st.markdown("## 🧩 Concentração de Receita (Pareto)")

    if dim_concentracao and dim_concentracao in df_analise.columns:
        pareto_df = compute_pareto(df_analise, dim_concentracao, coluna_valor)
        fig_pareto = build_pareto_chart(pareto_df, dim_concentracao, top_n=top_n_pareto)
        st.plotly_chart(fig_pareto, use_container_width=True)

        with st.expander("📋 Ver tabela Pareto"):
            show_df = pareto_df.copy()
            show_df["total"] = show_df["total"].apply(lambda x: format_currency(x, "$"))
            show_df["share_pct"] = show_df["share_pct"].map(lambda x: f"{x:.2f}%")
            show_df["cum_share_pct"] = show_df["cum_share_pct"].map(
                lambda x: f"{x:.2f}%"
            )
            st.dataframe(
                show_df[[dim_concentracao, "total", "share_pct", "cum_share_pct"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info(
            "ℹ️ Selecione uma dimensão categórica no menu lateral para gerar o Pareto."
        )

    st.markdown("---")

    # =========================
    # YOY (Year-over-Year)
    # =========================
    st.markdown("## 📅 Comparação YoY (Year-over-Year)")

    yoy_df = compute_yoy(df_analise, coluna_data, coluna_valor, freq="ME")  # mensal
    yoy_df_display = yoy_df.copy()

    # Cards YoY
    yy1, yy2, yy3 = st.columns(3)
    with yy1:
        total_ultimo = yoy_df["total"].iloc[-1] if len(yoy_df) else 0
        st.metric("Total (último mês)", format_currency(total_ultimo, "$"))
    with yy2:
        yoy_pct_last = yoy_df["yoy_pct"].iloc[-1] if len(yoy_df) else np.nan
        st.metric(
            "YoY % (último mês)",
            f"{yoy_pct_last:.2f}%" if pd.notna(yoy_pct_last) else "N/A",
        )
    with yy3:
        yoy_abs_last = yoy_df["yoy_abs"].iloc[-1] if len(yoy_df) else np.nan
        st.metric(
            "YoY Abs (último mês)",
            format_currency(yoy_abs_last, "$") if pd.notna(yoy_abs_last) else "N/A",
        )

    # Gráfico YoY
    fig_yoy = go.Figure()
    fig_yoy.add_trace(
        go.Scatter(
            x=yoy_df["ORDERDATE"]
            if "ORDERDATE" in yoy_df.columns
            else yoy_df.iloc[:, 0],
            y=yoy_df["total"],
            mode="lines+markers",
            name="Total Mensal",
            line=dict(color=COLOR_REVENUE, width=3),
        )
    )
    fig_yoy.add_trace(
        go.Scatter(
            x=yoy_df["ORDERDATE"]
            if "ORDERDATE" in yoy_df.columns
            else yoy_df.iloc[:, 0],
            y=yoy_df["yoy_pct"],
            mode="lines+markers",
            name="YoY (%)",
            yaxis="y2",
            line=dict(color=COLOR_YOY, width=2.5),
        )
    )

    fig_yoy.update_layout(
        template="plotly_white",
        height=420,
        xaxis_title="Mês",
        yaxis=dict(title="Total Mensal"),
        yaxis2=dict(title="YoY (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family=PLOT_FONT),
        margin=dict(l=30, r=30, t=30, b=30),
    )
    st.plotly_chart(fig_yoy, use_container_width=True)

    with st.expander("📋 Ver tabela YoY"):
        date_col_name = yoy_df.columns[0]
        yoy_view = yoy_df_display.rename(columns={date_col_name: "Período"})

        yoy_styler = yoy_view.style.format(
            {
                "total": lambda x: format_currency(x, "$"),
                "yoy_abs": lambda x: format_currency(x, "$") if pd.notna(x) else "-",
                "yoy_pct": lambda x: f"{x:.2f}%" if pd.notna(x) else "-",
            }
        ).background_gradient(subset=["yoy_pct"], cmap="RdYlGn")

        st.dataframe(yoy_styler, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =========================
    # TABS: DETALHES / ESTATÍSTICAS / SOBRE
    # =========================
    tab1, tab2, tab3 = st.tabs(["📋 Dados Detalhados", "📊 Estatísticas", "ℹ️ Sobre"])

    with tab1:
        st.markdown("### Tabela de Resultados (Crescimento)")

        tabela = resultado.rename(
            columns={
                coluna_data: "Período",
                "total_vendas": "Vendas Totais",
                "crescimento_%": "Crescimento",
            }
        )

        tabela_styler = tabela.style.format(
            {
                "Vendas Totais": lambda x: format_currency(x, "$"),
                "Crescimento": lambda x: f"{x:.2f}%" if pd.notna(x) else "-",
            }
        ).background_gradient(subset=["Crescimento"], cmap="RdYlGn")

        st.dataframe(tabela_styler, use_container_width=True, hide_index=True)

        csv = resultado.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV (crescimento)",
            data=csv,
            file_name=f"analise_crescimento_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    with tab2:
        st.markdown("### Estatísticas Descritivas (Crescimento %)")
        stats = resultado["crescimento_%"].describe()

        stats_df = pd.DataFrame(
            {
                "Estatística": [
                    "Média",
                    "Desvio Padrão",
                    "Mínimo",
                    "25%",
                    "50%",
                    "75%",
                    "Máximo",
                ],
                "Valor": [
                    f"{stats['mean']:.2f}%" if pd.notna(stats.get("mean")) else "N/A",
                    f"{stats['std']:.2f}%" if pd.notna(stats.get("std")) else "N/A",
                    f"{stats['min']:.2f}%" if pd.notna(stats.get("min")) else "N/A",
                    f"{stats['25%']:.2f}%" if pd.notna(stats.get("25%")) else "N/A",
                    f"{stats['50%']:.2f}%" if pd.notna(stats.get("50%")) else "N/A",
                    f"{stats['75%']:.2f}%" if pd.notna(stats.get("75%")) else "N/A",
                    f"{stats['max']:.2f}%" if pd.notna(stats.get("max")) else "N/A",
                ],
            }
        )
        st.dataframe(stats_df, hide_index=True, use_container_width=True)

        st.markdown("### Períodos de Destaque")
        t1, t2 = st.columns(2)

        with t1:
            st.markdown("**🏆 Top 3 Melhores Crescimentos**")
            top3 = resultado.nlargest(3, "crescimento_%")[
                [coluna_data, "total_vendas", "crescimento_%"]
            ]
            st.dataframe(top3, use_container_width=True, hide_index=True)

        with t2:
            st.markdown("**📉 Top 3 Piores Crescimentos**")
            bottom3 = resultado.nsmallest(3, "crescimento_%")[
                [coluna_data, "total_vendas", "crescimento_%"]
            ]
            st.dataframe(bottom3, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Sobre este Dashboard")

        st.markdown(
            """
**Funcionalidades principais:**
- 📤 Upload de CSV com seleção dinâmica de colunas
- 📈 Crescimento periódico (mensal/trimestral/anual)
- 🧾 Métricas executivas (Receita Total, Pico Sazonal, Concentração Top 3)
- 🧩 Pareto automático (concentração de receita)
- 📅 Comparação YoY (mensal)
- 📋 Exportação de resultados

**Dica de uso:**
1. Faça upload do CSV (ou use dados locais/exemplo)
2. Selecione coluna de data e valor
3. (Opcional) Selecione dimensão para Pareto/Top 3
4. Explore crescimento, Pareto e YoY

**Autor:** Samuel Maia
**Projeto:** https://github.com/samuelmaia-analytics/analise-vendas-python
"""
        )

        if not dados_reais:
            st.info(
                "💡 Para uma análise ainda mais precisa, faça upload do seu CSV real."
            )

except Exception as e:
    st.error(f"❌ Erro na análise: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    f"""
<div style='text-align: center; color: #666; padding: 1rem;'>
    Desenvolvido por <a href='https://github.com/samuelmaia-analytics' target='_blank'>Samuel Maia</a> |
    Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""",
    unsafe_allow_html=True,
)

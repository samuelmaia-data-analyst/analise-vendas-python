import os
import csv as csvlib
from contextlib import redirect_stdout
from datetime import datetime
from io import BytesIO
from io import StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from scripts.analise_crescimento import calcular_crescimento

APP_TITLE = "Revenue Intelligence - Samuel Maia"
APP_ICON = ":bar_chart:"
LAYOUT = "wide"

COLOR_REVENUE = "#0b3c5d"
COLOR_GROWTH = "#c2410c"
COLOR_PARETO_BAR = "#0f766e"
COLOR_PARETO_LINE = "#b45309"
COLOR_YOY = "#1d4ed8"
PLOT_FONT = "Segoe UI, Segoe UI Variable, Helvetica Neue, Arial, sans-serif"


def format_currency(value: float, symbol: str = "$") -> str:
    try:
        return f"{symbol}{value:,.2f}"
    except Exception:
        return "N/A"


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def safe_to_numeric(series: pd.Series) -> pd.Series:
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
    return [
        c
        for c in columns
        if any(t in c.lower() for t in ["date", "data", "dia", "mes", "orderdate"])
    ]


def detect_value_columns(df: pd.DataFrame) -> list[str]:
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
    return list(dict.fromkeys(by_name + numeric_cols))


def suggest_dimension_columns(df: pd.DataFrame) -> list[str]:
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
    return list(dict.fromkeys(hints + cat_cols))


@st.cache_data
def criar_dados_exemplo() -> pd.DataFrame:
    np.random.seed(42)

    datas = pd.date_range("2023-01-01", "2024-12-31", freq="D")
    tendencia = np.linspace(1000, 2000, len(datas))
    sazonalidade = 500 * np.sin(2 * np.pi * np.arange(len(datas)) / 365)
    ruido = np.random.normal(0, 100, len(datas))

    vendas = np.maximum(tendencia + sazonalidade + ruido, 500)

    produtos = [f"PROD_{i:03d}" for i in range(1, 21)]
    clientes = [f"CLI_{i:03d}" for i in range(1, 51)]

    return pd.DataFrame(
        {
            "DATA": datas,
            "VENDAS": vendas.astype(int),
            "QUANTIDADE": np.random.randint(1, 50, len(datas)),
            "PRODUTO": np.random.choice(produtos, len(datas)),
            "CLIENTE": np.random.choice(clientes, len(datas)),
            "CATEGORIA": np.random.choice(
                ["Eletronicos", "Moveis", "Roupas", "Livros"], len(datas)
            ),
        }
    )


@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, bool, str | None]:
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
            return pd.read_csv(caminho), True, caminho

    return criar_dados_exemplo(), False, None


def carregar_csv_upload(file_bytes: bytes) -> pd.DataFrame:
    # Detecta encoding/separador em amostra para evitar multiplos parses pesados.
    encodings = ["utf-8-sig", "utf-8", "ISO-8859-1", "cp1252"]
    separators = [",", ";", "\t", "|"]
    sample = file_bytes[:200_000]
    last_error: Exception | None = None

    for enc in encodings:
        try:
            sample_text = sample.decode(enc)
        except UnicodeDecodeError:
            continue

        try:
            sep = csvlib.Sniffer().sniff(
                sample_text, delimiters="".join(separators)
            ).delimiter
        except csvlib.Error:
            sep = max(separators, key=sample_text.count)
            if sample_text.count(sep) == 0:
                sep = ","

        try:
            parsed = pd.read_csv(
                BytesIO(file_bytes),
                encoding=enc,
                sep=sep,
                low_memory=False,
                on_bad_lines="skip",
            )
            if parsed.shape[1] >= 2:
                return parsed
        except Exception as exc:  # noqa: PERF203
            last_error = exc

    # Fallback para casos em que o sniffer falha.
    for enc in encodings:
        for sep in separators:
            try:
                parsed = pd.read_csv(
                    BytesIO(file_bytes),
                    encoding=enc,
                    sep=sep,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if parsed.shape[1] >= 2:
                    return parsed
            except Exception as exc:  # noqa: PERF203
                last_error = exc

    raise ValueError(f"Nao foi possivel ler o CSV enviado. Erro: {last_error}")

def compute_yoy(
    df: pd.DataFrame, date_col: str, value_col: str, freq: str = "ME"
) -> pd.DataFrame:
    tmp = df[[date_col, value_col]].copy()
    tmp[date_col] = safe_to_datetime(tmp[date_col])
    tmp[value_col] = safe_to_numeric(tmp[value_col])
    tmp = tmp.dropna(subset=[date_col, value_col])

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


@st.cache_data(show_spinner=False)
def calcular_crescimento_cached(
    df: pd.DataFrame,
    coluna_data: str,
    coluna_valor: str,
    periodo: str,
) -> pd.DataFrame:
    # Silencia logs verbosos da rotina legada para evitar overhead em reruns.
    sink = StringIO()
    with redirect_stdout(sink):
        return calcular_crescimento(
            df.copy(),
            coluna_data=coluna_data,
            coluna_valor=coluna_valor,
            periodo=periodo,
        )


def build_pareto_chart(
    pareto_df: pd.DataFrame, dim_col: str, top_n: int = 15
) -> go.Figure:
    plot_df = pareto_df.head(top_n).copy()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=plot_df[dim_col].astype(str),
            y=plot_df["total"],
            name="Total",
            marker_color=COLOR_PARETO_BAR,
        )
    )
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


def classify_growth_signal(value: float) -> tuple[str, str]:
    if pd.isna(value):
        return "N/A", "signal-warn"
    if value >= 8:
        return "Tracao Forte", "signal-good"
    if value >= 2:
        return "Tracao Moderada", "signal-warn"
    return "Tracao Fraca", "signal-risk"


def classify_concentration_signal(value: float | None) -> tuple[str, str]:
    if value is None or pd.isna(value):
        return "N/A", "signal-warn"
    if value <= 50:
        return "Risco Baixo", "signal-good"
    if value <= 70:
        return "Risco Moderado", "signal-warn"
    return "Risco Alto", "signal-risk"


def inject_css() -> None:
    st.markdown(
        """
<style>
    :root {
        --ink-900: #0f172a;
        --ink-700: #334155;
        --surface: #ffffff;
        --line: #dbe4ef;
        --brand-1: #0f766e;
        --brand-2: #0b3c5d;
        --brand-3: #c2410c;
    }
    .stApp {
        background:
            radial-gradient(circle at 2% 2%, #e0f2fe 0, transparent 36%),
            radial-gradient(circle at 94% 7%, #ffedd5 0, transparent 35%),
            #f1f5f9;
        font-family: "Segoe UI", "Segoe UI Variable", "Helvetica Neue", Arial, sans-serif;
        color: var(--ink-900);
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1.8rem;
        max-width: 1380px;
    }
    .hero-wrap {
        background: linear-gradient(120deg, var(--brand-2) 0%, var(--brand-1) 52%, #0ea5e9 100%);
        border-radius: 20px;
        padding: 1.25rem 1.35rem;
        margin-bottom: 0.85rem;
        color: #f8fafc;
        box-shadow: 0 14px 30px rgba(11, 60, 93, 0.24);
    }
    .hero-title {
        margin: 0;
        font-size: 2.05rem;
        line-height: 1.2;
        font-weight: 760;
        font-family: "Segoe UI", "Segoe UI Variable", "Helvetica Neue", Arial, sans-serif;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        margin: 0.45rem 0 0 0;
        font-size: 0.96rem;
        color: #e2e8f0;
    }
    .hero-badges {
        margin-top: 0.65rem;
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
    }
    .hero-badge {
        border: 1px solid rgba(255, 255, 255, 0.32);
        border-radius: 999px;
        padding: 0.2rem 0.58rem;
        font-size: 0.74rem;
        color: #ecfeff;
        background: rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    [data-testid="stSidebar"] * {
        color: var(--ink-900) !important;
    }
    [data-testid="stSidebar"] .stFileUploader * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: #0f172a !important;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        color: #f8fafc !important;
        background-color: #0f172a !important;
    }
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.48rem 0.75rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    [data-testid="stMetricLabel"] {
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748b !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--ink-900) !important;
        font-weight: 760 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #0f766e !important;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {
        color: var(--ink-900);
    }
    .section-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.78rem 0.94rem;
        margin-bottom: 0.8rem;
    }
    .proof-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.6rem;
        margin: 0.1rem 0 0.8rem 0;
    }
    .proof-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.55rem 0.7rem;
    }
    .proof-k {
        font-size: 0.74rem;
        color: var(--ink-700);
        margin: 0;
    }
    .proof-v {
        font-size: 1.04rem;
        margin: 0.1rem 0 0 0;
        color: var(--ink-900);
        font-weight: 760;
    }
    .snapshot-list {
        margin: 0;
        padding-left: 1.1rem;
        color: var(--ink-900);
    }
    .snapshot-list li {
        margin-bottom: 0.25rem;
    }
    .signal-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.7rem;
        margin-top: 0.4rem;
    }
    .signal-card {
        border-radius: 10px;
        padding: 0.72rem 0.8rem;
        border: 1px solid transparent;
    }
    .signal-title {
        font-size: 0.78rem;
        color: var(--ink-700);
        margin-bottom: 0.2rem;
    }
    .signal-value {
        font-size: 1rem;
        font-weight: 700;
        color: var(--ink-900);
    }
    .signal-good { background: #ecfdf5; border-color: #86efac; }
    .signal-warn { background: #fffbeb; border-color: #fde68a; }
    .signal-risk { background: #fef2f2; border-color: #fca5a5; }
    .lead-strip {
        background: linear-gradient(90deg, #0b3c5d 0%, #0f766e 50%, #c2410c 100%);
        border-radius: 14px;
        padding: 0.8rem 0.95rem;
        margin: 0.85rem 0;
        color: #f8fafc;
        display: grid;
        grid-template-columns: 1.6fr 1fr 1fr;
        gap: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .lead-title {
        margin: 0;
        font-weight: 780;
        font-size: 1.02rem;
    }
    .lead-txt {
        margin: 0.2rem 0 0 0;
        font-size: 0.84rem;
        color: #e2e8f0;
    }
    .lead-k {
        margin: 0;
        font-size: 0.72rem;
        color: #dbeafe;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .lead-v {
        margin: 0.1rem 0 0 0;
        font-size: 1.08rem;
        font-weight: 760;
    }
    [data-baseweb="tab-list"] {
        gap: 0.35rem;
    }
    [data-baseweb="tab"] {
        border-radius: 10px;
        background: #e2e8f0;
        border: 1px solid #d1d9e6;
        color: var(--ink-700);
        font-weight: 650;
        padding: 0.4rem 0.65rem;
    }
    [aria-selected="true"][data-baseweb="tab"] {
        background: #0b3c5d;
        border-color: #0b3c5d;
        color: #f8fafc;
    }
    @media (max-width: 980px) {
        .signal-grid,
        .proof-grid,
        .lead-strip {
            grid-template-columns: 1fr;
        }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def render_header(origem: str | None, dados_reais: bool) -> None:
    fonte = origem if origem else "Dados simulados"
    tipo = "Dados reais" if dados_reais else "Amostra de demonstracao"
    st.markdown(
        f"""
<div class='hero-wrap'>
    <h1 class='hero-title'>Revenue Intelligence Studio</h1>
    <p class='hero-subtitle'>Painel executivo com narrativa de crescimento, risco comercial e concentracao de receita para tomada de decisao.</p>
    <p class='hero-subtitle'><strong>Fonte:</strong> {fonte} | <strong>Tipo:</strong> {tipo} | <strong>Atualizado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <div class='hero-badges'>
        <span class='hero-badge'>Visao C-Level</span>
        <span class='hero-badge'>Pareto + YoY</span>
        <span class='hero-badge'>Pronto para Pitch</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_proof_strip(
    periodos: int,
    dimensoes: int,
    top3_share: float | None,
    crescimento_medio: float,
) -> None:
    concentracao = f"{top3_share:.1f}%" if top3_share is not None else "N/A"
    crescimento = f"{crescimento_medio:.1f}%" if pd.notna(crescimento_medio) else "N/A"
    st.markdown(
        f"""
<div class='proof-grid'>
    <div class='proof-card'><p class='proof-k'>Escala analisada</p><p class='proof-v'>{periodos} periodos</p></div>
    <div class='proof-card'><p class='proof-k'>Dimensoes mapeadas</p><p class='proof-v'>{dimensoes}</p></div>
    <div class='proof-card'><p class='proof-k'>Concentracao Top 3</p><p class='proof-v'>{concentracao}</p></div>
    <div class='proof-card'><p class='proof-k'>Crescimento medio</p><p class='proof-v'>{crescimento}</p></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_lead_strip(
    receita_total: float,
    crescimento_medio: float,
    top3_share: float | None,
    dados_reais: bool,
) -> None:
    crescimento = f"{crescimento_medio:.1f}%" if pd.notna(crescimento_medio) else "N/A"
    concentracao = f"{top3_share:.1f}%" if top3_share is not None else "N/A"
    origem_label = "Dataset real" if dados_reais else "Dataset demonstrativo"
    st.markdown(
        f"""
<div class='lead-strip'>
    <div>
        <p class='lead-title'>Narrativa pronta para recrutadores e leads</p>
        <p class='lead-txt'>Dashboard orientado a impacto: combina crescimento, risco de concentracao e sazonalidade para guiar decisao executiva.</p>
    </div>
    <div>
        <p class='lead-k'>Receita consolidada</p>
        <p class='lead-v'>{format_currency(receita_total, '$')}</p>
        <p class='lead-txt'>{origem_label}</p>
    </div>
    <div>
        <p class='lead-k'>Headline comercial</p>
        <p class='lead-v'>Growth {crescimento}</p>
        <p class='lead-txt'>Top 3 share {concentracao}</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def format_period_label(value: object) -> str:
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m")
    except Exception:
        pass
    return str(value)


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
        insights.append(f"Crescimento medio em {direcao}: {crescimento_medio:.1f}% por periodo.")

    if top3_share is not None:
        insights.append(f"Concentracao top 3: {top3_share:.1f}% da receita total.")

    insights.append(f"Faixa de performance: melhor em {melhor_periodo} e pior em {pior_periodo}.")
    return insights


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    st.markdown("## Configuracoes")

    uploaded_file = st.file_uploader(
        "Upload do CSV",
        type=["csv"],
        help="Envie seu arquivo de vendas em CSV.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > 40:
            st.error(
                f"Arquivo muito grande ({file_size_mb:.1f} MB). Limite recomendado: 40 MB."
            )
            st.stop()

        upload_key = f"{uploaded_file.name}:{len(file_bytes)}"
        cached_key = st.session_state.get("upload_key")
        cached_df = st.session_state.get("upload_df")

        if cached_key == upload_key and isinstance(cached_df, pd.DataFrame):
            df = cached_df
        else:
            with st.spinner("Carregando arquivo..."):
                df = carregar_csv_upload(file_bytes)
            st.session_state["upload_key"] = upload_key
            st.session_state["upload_df"] = df

        if df.empty:
            st.error("O arquivo foi carregado, mas nao possui linhas validas.")
            st.stop()

        dados_reais = True
        origem = uploaded_file.name
    else:
        df, dados_reais, origem = carregar_dados()

    st.markdown("### Base")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Registros", f"{len(df):,}")
    with c2:
        st.metric("Colunas", len(df.columns))

    st.caption(f"Origem: {origem if origem else 'Amostra simulada'}")

    st.markdown("### Mapeamento")
    colunas = df.columns.tolist()
    data_options = detect_date_columns(colunas) or colunas
    coluna_data = st.selectbox("Coluna de data", data_options, index=0)

    valor_options = detect_value_columns(df)
    if not valor_options:
        st.error("Nenhuma coluna numerica encontrada para valor.")
        st.stop()
    coluna_valor = st.selectbox("Coluna de valor", valor_options, index=0)

    st.markdown("### Analise")
    periodo = st.selectbox("Periodicidade", ["Mensal", "Trimestral", "Anual"], index=0)
    periodo_map = {"Mensal": "M", "Trimestral": "T", "Anual": "A"}

    dim_options = suggest_dimension_columns(df)
    if dim_options:
        dim_concentracao = st.selectbox("Dimensao para Pareto", dim_options, index=0)
        top_n_pareto = st.slider("Top N do Pareto", min_value=5, max_value=30, value=12, step=1)
    else:
        dim_concentracao = None
        top_n_pareto = 12
        st.info("Nenhuma coluna categorica encontrada para Pareto.")


try:
    render_header(origem, dados_reais)

    df_analise = df.copy()
    df_analise[coluna_data] = safe_to_datetime(df_analise[coluna_data])
    df_analise[coluna_valor] = safe_to_numeric(df_analise[coluna_valor])
    df_analise = df_analise.dropna(subset=[coluna_data, coluna_valor])

    if df_analise.empty:
        st.warning("Nao ha dados validos apos conversao de data e valor.")
        st.stop()

    with st.spinner("Calculando indicadores..."):
        resultado = calcular_crescimento_cached(
            df_analise,
            coluna_data=coluna_data,
            coluna_valor=coluna_valor,
            periodo=periodo_map[periodo],
        )

    if resultado.empty:
        st.warning("A agregacao nao gerou periodos para analise.")
        st.stop()

    receita_total = float(df_analise[coluna_valor].sum())

    sazonal = df_analise.groupby(df_analise[coluna_data].dt.month)[coluna_valor].sum()
    mes_pico_num = int(sazonal.idxmax()) if not sazonal.empty else 1
    mes_pico = f"{month_name_pt(mes_pico_num)} ({mes_pico_num})"

    top3_share = None
    top3_labels = None
    if dim_concentracao and dim_concentracao in df_analise.columns:
        df_tmp = df_analise.dropna(subset=[dim_concentracao])
        if not df_tmp.empty:
            top3 = (
                df_tmp.groupby(dim_concentracao)[coluna_valor]
                .sum()
                .sort_values(ascending=False)
                .head(3)
            )
            top3_share = (top3.sum() / receita_total) * 100 if receita_total else 0
            top3_labels = ", ".join([str(x) for x in top3.index.tolist()])

    crescimento_medio = float(resultado["crescimento_%"].mean())
    crescimento_valid = resultado.dropna(subset=["crescimento_%"])
    if not crescimento_valid.empty:
        melhor_periodo_exec = format_period_label(
            crescimento_valid.loc[crescimento_valid["crescimento_%"].idxmax(), coluna_data]
        )
        pior_periodo_exec = format_period_label(
            crescimento_valid.loc[crescimento_valid["crescimento_%"].idxmin(), coluna_data]
        )
    else:
        melhor_periodo_exec = "N/A"
        pior_periodo_exec = "N/A"

    insights = build_executive_insights(
        receita_total=receita_total,
        crescimento_medio=crescimento_medio,
        mes_pico=mes_pico,
        top3_share=top3_share,
        melhor_periodo=melhor_periodo_exec,
        pior_periodo=pior_periodo_exec,
    )

    crescimento_label, crescimento_class = classify_growth_signal(crescimento_medio)
    concentracao_label, concentracao_class = classify_concentration_signal(top3_share)

    ult_crescimento = (
        float(resultado["crescimento_%"].iloc[-1])
        if len(resultado) and pd.notna(resultado["crescimento_%"].iloc[-1])
        else np.nan
    )
    momentum_label, momentum_class = classify_growth_signal(ult_crescimento)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Receita total", format_currency(receita_total, "$"))
    with k2:
        st.metric("Crescimento medio", f"{crescimento_medio:.1f}%" if pd.notna(crescimento_medio) else "N/A")
    with k3:
        st.metric("Pico sazonal", mes_pico)
    with k4:
        st.metric("Top 3", f"{top3_share:.1f}%" if top3_share is not None else "N/A")

    render_proof_strip(
        periodos=int(len(resultado)),
        dimensoes=int(len(df_analise.columns)),
        top3_share=top3_share,
        crescimento_medio=crescimento_medio,
    )
    render_lead_strip(
        receita_total=receita_total,
        crescimento_medio=crescimento_medio,
        top3_share=top3_share,
        dados_reais=dados_reais,
    )

    st.markdown(
        "<div class='section-card'><h4 style='margin-top:0'>Executive Snapshot</h4><ul class='snapshot-list'>"
        + "".join([f"<li>{item}</li>" for item in insights])
        + "</ul></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class='signal-grid'>
    <div class='signal-card {crescimento_class}'>
        <div class='signal-title'>Sinal de Crescimento</div>
        <div class='signal-value'>{crescimento_label}</div>
    </div>
    <div class='signal-card {concentracao_class}'>
        <div class='signal-title'>Risco de Concentracao</div>
        <div class='signal-value'>{concentracao_label}</div>
    </div>
    <div class='signal-card {momentum_class}'>
        <div class='signal-title'>Momentum Atual</div>
        <div class='signal-value'>{momentum_label}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    tab_overview, tab_growth, tab_pareto, tab_yoy, tab_data = st.tabs(
        ["Radar Executivo", "Crescimento", "Pareto", "YoY", "Dados"]
    )

    with tab_overview:
        st.caption(
            "Leitura rapida para reunioes comerciais: tendencia de receita e ritmo de crescimento no mesmo quadro."
        )
        c_left, c_right = st.columns(2)

        with c_left:
            fig_vendas = px.area(
                resultado,
                x=coluna_data,
                y="total_vendas",
                template="plotly_white",
            )
            fig_vendas.update_traces(line_color=COLOR_REVENUE)
            fig_vendas.update_layout(
                title="Evolucao das vendas",
                xaxis_title="Periodo",
                yaxis_title="Total",
                hovermode="x unified",
                height=420,
                font=dict(family=PLOT_FONT),
                margin=dict(l=10, r=10, t=45, b=10),
            )
            st.plotly_chart(fig_vendas, width="stretch")

        with c_right:
            fig_cresc = px.bar(
                resultado.dropna(subset=["crescimento_%"]),
                x=coluna_data,
                y="crescimento_%",
                template="plotly_white",
            )
            fig_cresc.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.6)
            fig_cresc.update_traces(marker_color=COLOR_GROWTH)
            fig_cresc.update_layout(
                title="Taxa de crescimento",
                xaxis_title="Periodo",
                yaxis_title="Crescimento (%)",
                height=420,
                font=dict(family=PLOT_FONT),
                margin=dict(l=10, r=10, t=45, b=10),
            )
            st.plotly_chart(fig_cresc, width="stretch")

    with tab_growth:
        st.caption("Performance ao longo dos periodos com destaque para variacao recente.")
        c1, c2, c3, c4 = st.columns(4)

        delta = (
            float(resultado["crescimento_%"].iloc[-1] - resultado["crescimento_%"].iloc[-2])
            if len(resultado) > 1 and pd.notna(resultado["crescimento_%"].iloc[-1]) and pd.notna(resultado["crescimento_%"].iloc[-2])
            else np.nan
        )
        ultimo_valor = float(resultado["total_vendas"].iloc[-1]) if len(resultado) else np.nan

        melhor_cresc = resultado["crescimento_%"].max()
        pior_cresc = resultado["crescimento_%"].min()

        with c1:
            st.metric(
                "Crescimento medio",
                f"{crescimento_medio:.1f}%" if pd.notna(crescimento_medio) else "N/A",
                delta=f"{delta:.1f} pp" if pd.notna(delta) else None,
            )
        with c2:
            st.metric("Ultimo periodo", format_currency(ultimo_valor, "$") if pd.notna(ultimo_valor) else "N/A")
        with c3:
            st.metric("Melhor periodo", f"{melhor_cresc:.1f}%" if pd.notna(melhor_cresc) else "N/A")
        with c4:
            st.metric("Pior periodo", f"{pior_cresc:.1f}%" if pd.notna(pior_cresc) else "N/A")

        fig_line = px.line(
            resultado,
            x=coluna_data,
            y="total_vendas",
            markers=True,
            line_shape="spline",
            template="plotly_white",
        )
        fig_line.update_traces(line=dict(color=COLOR_REVENUE, width=3), marker=dict(size=6))
        fig_line.update_layout(
            xaxis_title="Periodo",
            yaxis_title="Total",
            hovermode="x unified",
            height=440,
            font=dict(family=PLOT_FONT),
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_line, width="stretch")

    with tab_pareto:
        st.caption("Concentracao de receita para identificar dependencias e oportunidades de diversificacao.")
        if dim_concentracao and dim_concentracao in df_analise.columns:
            pareto_df = compute_pareto(df_analise, dim_concentracao, coluna_valor)
            fig_pareto = build_pareto_chart(pareto_df, dim_concentracao, top_n=top_n_pareto)
            st.plotly_chart(fig_pareto, width="stretch")

            if top3_labels:
                st.caption(f"Top 3 em {dim_concentracao}: {top3_labels}")

            show_df = pareto_df.copy()
            show_df["total"] = show_df["total"].apply(lambda x: format_currency(x, "$"))
            show_df["share_pct"] = show_df["share_pct"].map(lambda x: f"{x:.2f}%")
            show_df["cum_share_pct"] = show_df["cum_share_pct"].map(lambda x: f"{x:.2f}%")
            st.dataframe(
                show_df[[dim_concentracao, "total", "share_pct", "cum_share_pct"]],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Selecione uma dimensao categorica para habilitar Pareto.")

    with tab_yoy:
        st.caption("Comparacao ano contra ano para validar consistencia da expansao.")
        yoy_df = compute_yoy(df_analise, coluna_data, coluna_valor, freq="ME")

        yy1, yy2, yy3 = st.columns(3)
        total_ultimo = yoy_df["total"].iloc[-1] if len(yoy_df) else np.nan
        yoy_pct_last = yoy_df["yoy_pct"].iloc[-1] if len(yoy_df) else np.nan
        yoy_abs_last = yoy_df["yoy_abs"].iloc[-1] if len(yoy_df) else np.nan

        with yy1:
            st.metric("Total (ultimo mes)", format_currency(total_ultimo, "$") if pd.notna(total_ultimo) else "N/A")
        with yy2:
            st.metric("YoY % (ultimo mes)", f"{yoy_pct_last:.2f}%" if pd.notna(yoy_pct_last) else "N/A")
        with yy3:
            st.metric("YoY abs (ultimo mes)", format_currency(yoy_abs_last, "$") if pd.notna(yoy_abs_last) else "N/A")

        x_axis = yoy_df.columns[0] if not yoy_df.empty else None
        fig_yoy = go.Figure()
        if x_axis:
            fig_yoy.add_trace(
                go.Scatter(
                    x=yoy_df[x_axis],
                    y=yoy_df["total"],
                    mode="lines+markers",
                    name="Total mensal",
                    line=dict(color=COLOR_REVENUE, width=3),
                )
            )
            fig_yoy.add_trace(
                go.Scatter(
                    x=yoy_df[x_axis],
                    y=yoy_df["yoy_pct"],
                    mode="lines+markers",
                    name="YoY (%)",
                    yaxis="y2",
                    line=dict(color=COLOR_YOY, width=2.5),
                )
            )

        fig_yoy.update_layout(
            template="plotly_white",
            height=430,
            xaxis_title="Mes",
            yaxis=dict(title="Total mensal"),
            yaxis2=dict(title="YoY (%)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family=PLOT_FONT),
            margin=dict(l=30, r=30, t=30, b=30),
        )
        st.plotly_chart(fig_yoy, width="stretch")

        yoy_view = yoy_df.rename(columns={yoy_df.columns[0]: "Periodo"}) if not yoy_df.empty else yoy_df
        if not yoy_view.empty:
            yoy_styler = yoy_view.style.format(
                {
                    "total": lambda x: format_currency(x, "$"),
                    "yoy_abs": lambda x: format_currency(x, "$") if pd.notna(x) else "-",
                    "yoy_pct": lambda x: f"{x:.2f}%" if pd.notna(x) else "-",
                }
            )
            st.dataframe(yoy_styler, width="stretch", hide_index=True)
        else:
            st.info("Ainda nao ha historico suficiente para tabela YoY.")

    with tab_data:
        st.caption("Camada analitica para auditoria e compartilhamento da analise.")
        tabela = resultado.rename(
            columns={
                coluna_data: "Periodo",
                "total_vendas": "Vendas totais",
                "crescimento_%": "Crescimento",
            }
        )

        tabela_styler = tabela.style.format(
            {
                "Vendas totais": lambda x: format_currency(x, "$"),
                "Crescimento": lambda x: f"{x:.2f}%" if pd.notna(x) else "-",
            }
        )

        st.dataframe(tabela_styler, width="stretch", hide_index=True)

        stats = resultado["crescimento_%"].describe()
        stats_df = pd.DataFrame(
            {
                "Estatistica": ["Media", "Desvio padrao", "Minimo", "25%", "50%", "75%", "Maximo"],
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
        st.dataframe(stats_df, hide_index=True, width="stretch")

        csv_data = resultado.to_csv(index=False)
        st.download_button(
            label="Download CSV (crescimento)",
            data=csv_data,
            file_name=f"analise_crescimento_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

except Exception as e:
    st.error(f"Erro na analise: {str(e)}")
    st.exception(e)

st.markdown("---")
st.markdown(
    f"""
<div style='text-align:center; color:#334155; padding:0.8rem;'>
    Desenvolvido por <a href='https://github.com/samuelmaia-analytics' target='_blank'>Samuel Maia</a>
</div>
""",
    unsafe_allow_html=True,
)




from __future__ import annotations

import csv as csvlib
import os
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


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
        column
        for column in columns
        if any(token in column.lower() for token in ["date", "data", "dia", "mes", "orderdate"])
    ]


def detect_value_columns(df: pd.DataFrame) -> list[str]:
    cols = df.columns.tolist()
    by_name = [
        column
        for column in cols
        if any(token in column.lower() for token in ["sales", "venda", "price", "total", "valor", "receita"])
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return list(dict.fromkeys(by_name + numeric_cols))


def filter_value_columns(value_columns: list[str], date_col: str) -> list[str]:
    filtered = [column for column in value_columns if column != date_col]
    return filtered or value_columns


def suggest_dimension_columns(df: pd.DataFrame) -> list[str]:
    cols = df.columns.tolist()
    hints = []
    for column in [
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
        if column in cols:
            hints.append(column)

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
            "CATEGORIA": np.random.choice(["Eletronicos", "Moveis", "Roupas", "Livros"], len(datas)),
        }
    )


@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, bool, str | None]:
    possiveis_caminhos = [
        "data/raw/sales_data_sample.csv",
        "legacy/dados/sales_data_sample.csv",
        "./data/raw/sales_data_sample.csv",
        "./legacy/dados/sales_data_sample.csv",
        "data/processed/fato_vendas.csv",
        "legacy/dados_processados/fato_vendas.csv",
        "./data/processed/fato_vendas.csv",
        "./legacy/dados_processados/fato_vendas.csv",
    ]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                df = carregar_csv_upload(Path(caminho).read_bytes())
            except ValueError:
                continue
            if "ORDERDATE" in df.columns or "DATA" in df.columns:
                return df, True, caminho

    return criar_dados_exemplo(), False, None


def carregar_csv_upload(file_bytes: bytes) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "ISO-8859-1", "cp1252"]
    separators = [",", ";", "\t", "|"]
    sample = file_bytes[:200_000]
    last_error: Exception | None = None

    for encoding in encodings:
        try:
            sample_text = sample.decode(encoding)
        except UnicodeDecodeError:
            continue

        try:
            sep = csvlib.Sniffer().sniff(sample_text, delimiters="".join(separators)).delimiter
        except csvlib.Error:
            sep = max(separators, key=sample_text.count)
            if sample_text.count(sep) == 0:
                sep = ","

        try:
            parsed = pd.read_csv(
                BytesIO(file_bytes),
                encoding=encoding,
                sep=sep,
                low_memory=False,
                on_bad_lines="skip",
            )
            if parsed.shape[1] >= 2:
                return parsed
        except Exception as exc:  # noqa: PERF203
            last_error = exc

    for encoding in encodings:
        for sep in separators:
            try:
                parsed = pd.read_csv(
                    BytesIO(file_bytes),
                    encoding=encoding,
                    sep=sep,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if parsed.shape[1] >= 2:
                    return parsed
            except Exception as exc:  # noqa: PERF203
                last_error = exc

    raise ValueError(f"Nao foi possivel ler o CSV enviado. Erro: {last_error}")


def validate_upload_frame(df: pd.DataFrame, *, max_rows: int, max_columns: int) -> tuple[bool, str | None]:
    if df.empty:
        return False, "empty"
    if len(df) > max_rows:
        return False, "too_many_rows"
    if len(df.columns) > max_columns:
        return False, "too_many_columns"
    return True, None

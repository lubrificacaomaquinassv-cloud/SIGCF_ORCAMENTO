from __future__ import annotations

import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
from pyxlsb import open_workbook

from config import (
    COLUMNS,
    DATA_COLUMN_END,
    DATA_COLUMN_START,
    DATA_START_ROW_INDEX,
    DEFAULT_XLSB_PATH,
    HEADER_ROW_INDEX,
    SHEET_NAME,
)


def _normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Sem categoria"
    text = str(value).strip()
    if not text:
        return "Sem categoria"
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.split())


def _excel_date_to_datetime(value: object) -> pd.Timestamp | pd.NaT:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT
    if isinstance(value, datetime):
        return pd.Timestamp(value)
    if isinstance(value, (int, float)):
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(value))
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return parsed


def load_budget_data(path: Path | str | None = None) -> pd.DataFrame:
    file_path = Path(path or DEFAULT_XLSB_PATH)
    if not file_path.exists():
        raise FileNotFoundError(f"Planilha nao encontrada: {file_path}")

    rows: list[list[object]] = []
    with open_workbook(file_path) as workbook:
        with workbook.get_sheet(SHEET_NAME) as sheet:
            for row_index, row in enumerate(sheet.rows()):
                values = [cell.v for cell in row]
                if row_index < DATA_START_ROW_INDEX:
                    continue
                slice_values = values[DATA_COLUMN_START:DATA_COLUMN_END]
                if any(value is not None for value in slice_values):
                    rows.append(slice_values)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["VALOR_TOTAL_GESTAO"] = pd.to_numeric(df["VALOR_TOTAL_GESTAO"], errors="coerce").fillna(0)
    df["DATA_EMISSAO"] = df["DATA_EMISSAO"].map(_excel_date_to_datetime)
    df["ITEM"] = df["ITEM"].map(_normalize_text)
    df["CATEGORIA"] = df["CATEGORIA"].map(_normalize_text)
    df["SUBGRUPO"] = df["SUBGRUPO"].map(_normalize_text)
    df["CENTRO_CUSTO"] = df["CENTRO_CUSTO"].map(_normalize_text)
    df["FORNECEDORES"] = df["FORNECEDORES"].map(_normalize_text)
    return df


def summarize_by_category(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("CATEGORIA", as_index=False)["VALOR_TOTAL_GESTAO"]
        .sum()
        .rename(columns={"VALOR_TOTAL_GESTAO": "VALOR"})
        .sort_values("VALOR", ascending=False)
    )
    total = summary["VALOR"].sum()
    summary["PARTICIPACAO_%"] = (summary["VALOR"] / total * 100).round(2) if total else 0
    return summary


def summarize_by_item_category(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["ITEM", "CATEGORIA"], as_index=False)["VALOR_TOTAL_GESTAO"]
        .sum()
        .rename(columns={"VALOR_TOTAL_GESTAO": "VALOR"})
        .sort_values("VALOR", ascending=False)
    )
    return summary


def to_technical_view(df: pd.DataFrame, origem: str = "PLANILHA") -> pd.DataFrame:
    technical = pd.DataFrame(
        {
            "FORNECEDOR": df["FORNECEDORES"],
            "ID_FORNECEDOR_SAP": df["ID_FORNECEDOR_SAP"].astype(str),
            "CATEGORIA": df["CATEGORIA"],
            "VALOR": df["VALOR_TOTAL_GESTAO"],
            "ORIGEM": origem,
        }
    )
    if "DATA_EMISSAO" in df.columns:
        technical["DATA_REFERENCIA"] = df["DATA_EMISSAO"]
    return technical


def merge_technical_sources(
    planilha_df: pd.DataFrame,
    lancamentos_df: pd.DataFrame,
) -> pd.DataFrame:
    planilha = to_technical_view(planilha_df, origem="PLANILHA")
    if lancamentos_df.empty:
        return planilha

    manual = pd.DataFrame(
        {
            "FORNECEDOR": lancamentos_df["FORNECEDOR"],
            "ID_FORNECEDOR_SAP": lancamentos_df["ID_FORNECEDOR_SAP"].astype(str),
            "CATEGORIA": lancamentos_df["CATEGORIA"],
            "VALOR": lancamentos_df["VALOR"],
            "ORIGEM": "MANUAL",
            "DATA_REFERENCIA": lancamentos_df["DATA_LANCAMENTO"],
        }
    )
    return pd.concat([planilha, manual], ignore_index=True)


def summarize_technical_by_category(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("CATEGORIA", as_index=False)["VALOR"]
        .sum()
        .sort_values("VALOR", ascending=False)
    )
    total = summary["VALOR"].sum()
    summary["PARTICIPACAO_%"] = (summary["VALOR"] / total * 100).round(2) if total else 0
    return summary


def summarize_technical_by_fornecedor(df: pd.DataFrame, categoria: str | None = None) -> pd.DataFrame:
    scoped = df if not categoria else df[df["CATEGORIA"] == categoria]
    summary = (
        scoped.groupby(["FORNECEDOR", "ID_FORNECEDOR_SAP", "CATEGORIA"], as_index=False)["VALOR"]
        .sum()
        .sort_values("VALOR", ascending=False)
    )
    return summary


def filter_dataframe(
    df: pd.DataFrame,
    categorias: list[str] | None = None,
    itens: list[str] | None = None,
    centros_custo: list[str] | None = None,
    fornecedores: list[str] | None = None,
    data_inicio: pd.Timestamp | None = None,
    data_fim: pd.Timestamp | None = None,
) -> pd.DataFrame:
    filtered = df.copy()
    if categorias:
        filtered = filtered[filtered["CATEGORIA"].isin(categorias)]
    if itens:
        filtered = filtered[filtered["ITEM"].isin(itens)]
    if centros_custo:
        filtered = filtered[filtered["CENTRO_CUSTO"].isin(centros_custo)]
    if fornecedores:
        filtered = filtered[filtered["FORNECEDORES"].isin(fornecedores)]
    if data_inicio is not None:
        filtered = filtered[filtered["DATA_EMISSAO"] >= data_inicio]
    if data_fim is not None:
        filtered = filtered[filtered["DATA_EMISSAO"] <= data_fim]
    return filtered

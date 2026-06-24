from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from config import LANCAMENTOS_PATH

LANCAMENTO_COLUMNS = [
    "ID",
    "DATA_LANCAMENTO",
    "FORNECEDOR",
    "ID_FORNECEDOR_SAP",
    "CATEGORIA",
    "VALOR",
    "ORIGEM",
]


def _ensure_storage() -> None:
    LANCAMENTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LANCAMENTOS_PATH.exists():
        pd.DataFrame(columns=LANCAMENTO_COLUMNS).to_csv(
            LANCAMENTOS_PATH, index=False, sep=";", decimal=","
        )


def load_lancamentos() -> pd.DataFrame:
    _ensure_storage()
    df = pd.read_csv(LANCAMENTOS_PATH, sep=";", decimal=",")
    for column in LANCAMENTO_COLUMNS:
        if column not in df.columns:
            df[column] = None
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)
    df["DATA_LANCAMENTO"] = pd.to_datetime(df["DATA_LANCAMENTO"], errors="coerce", dayfirst=True)
    return df[LANCAMENTO_COLUMNS]


def save_lancamentos(df: pd.DataFrame) -> None:
    _ensure_storage()
    df[LANCAMENTO_COLUMNS].to_csv(LANCAMENTOS_PATH, index=False, sep=";", decimal=",")


def import_lancamentos_csv(content: bytes) -> pd.DataFrame:
    from io import BytesIO

    df = pd.read_csv(BytesIO(content), sep=";", decimal=",")
    for column in LANCAMENTO_COLUMNS:
        if column not in df.columns:
            df[column] = None
    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce").fillna(0)
    save_lancamentos(df[LANCAMENTO_COLUMNS])
    return load_lancamentos()


def export_lancamentos_csv() -> bytes:
    return LANCAMENTOS_PATH.read_bytes() if LANCAMENTOS_PATH.exists() else b""


def add_lancamento(
    fornecedor: str,
    id_fornecedor_sap: str,
    categoria: str,
    valor: float,
    data_lancamento: datetime | None = None,
) -> pd.DataFrame:
    df = load_lancamentos()
    novo = {
        "ID": str(uuid4())[:8].upper(),
        "DATA_LANCAMENTO": (data_lancamento or datetime.now()).strftime("%Y-%m-%d"),
        "FORNECEDOR": fornecedor.strip(),
        "ID_FORNECEDOR_SAP": id_fornecedor_sap.strip().upper(),
        "CATEGORIA": categoria.strip(),
        "VALOR": float(valor),
        "ORIGEM": "MANUAL",
    }
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    save_lancamentos(df)
    return df


def delete_lancamento(lancamento_id: str) -> pd.DataFrame:
    df = load_lancamentos()
    df = df[df["ID"] != lancamento_id].reset_index(drop=True)
    save_lancamentos(df)
    return df

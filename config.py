from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LANCAMENTOS_PATH = PROJECT_ROOT / "data" / "lancamentos.csv"
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

DEFAULT_XLSB_PATH = Path(
    r"v:\Usuários\Núcleo SV - Controladoria\Gestão Orçamentaria"
    r"\Gestão Orçamentaria Atual\Gestão Orçamentaria Atual - 2026.xlsb"
)

SHEET_NAME = "Planilha1"
HEADER_ROW_INDEX = 1
DATA_START_ROW_INDEX = 2
DATA_COLUMN_START = 1
DATA_COLUMN_END = 13

COLUMNS = [
    "DATA_EMISSAO",
    "FORNECEDORES",
    "ID_FORNECEDOR_SAP",
    "SERVICO",
    "NFE",
    "ITEM",
    "CENTRO_CUSTO",
    "DESTINACAO",
    "FROTA",
    "CATEGORIA",
    "SUBGRUPO",
    "VALOR_TOTAL_GESTAO",
]

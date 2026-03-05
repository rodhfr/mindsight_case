import unicodedata
import re
from pathlib import Path

import pandas as pd

VALID_EXT = {
    ".xlsx": pd.read_excel,
    ".csv": pd.read_csv
}

def read_df_by_suffix(path):
    """
    Le o sufixo do arquivo para ver se esta conforme as extensoes validas.
    Retorna o DataFrame lido pelo pandas.
    """
    ext = Path(path).suffix.lower()
    if ext not in VALID_EXT:
        raise ValueError(f"arquivo nao suportado: {ext}")
    return VALID_EXT[ext](path)

def normalize_text(txt):
    """
    NFD stands for 'Normalization Form Decomposition'.
    Separa letras e acentos em caracteres diferentes, encoda em ascii ignorando acentos,
    remove espacos excessivos e retorna texto decodado em utf-8.
    """
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'\s+', ' ', txt).strip()

def mv_col_to_start(df, coluna):
    """
    Move a coluna especificada para a primeira posição do DataFrame.
    """
    if coluna in df.columns:
        col_data = df.pop(coluna)
        df.insert(0, coluna, col_data)
    return df

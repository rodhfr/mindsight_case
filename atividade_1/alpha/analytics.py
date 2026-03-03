"""
analytics.py — lógica de negócio extraída do streamlit_app.py.

Todas as funções aqui são puras (sem dependências de Streamlit) e
podem ser importadas tanto pelo dashboard quanto pelos testes.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd


# ── Utilitários de texto ──────────────────────────────────────────────────────

def remover_acentos(texto) -> str | float:
    """Remove acentos de uma string. Retorna NaN inalterado."""
    if pd.isna(texto):
        return texto
    normalizado = unicodedata.normalize("NFKD", str(texto))
    return normalizado.encode("ascii", "ignore").decode("ascii")


# ── Detecção de colunas ───────────────────────────────────────────────────────

def detectar_cols_perf(df: pd.DataFrame) -> list[str]:
    """Retorna colunas de performance (prefixo 'perf_') em qualquer ordem."""
    return [c for c in df.columns if c.startswith("perf_")]


def ordenar_cols_perf(cols: list[str]) -> list[str]:
    """Ordena colunas perf_<sem>_<ano> cronologicamente (ano, semestre)."""
    def chave(c):
        parts = c.split("_")
        return int(parts[2]), int(parts[1])   # (ano, semestre)
    return sorted(cols, key=chave)


# ── Matriz 9-Box ──────────────────────────────────────────────────────────────

_MAPA_9BOX = {
    ("Alta",  "Alto"):  "Estrela",
    ("Alta",  "Médio"): "Forte Desempenho",
    ("Alta",  "Baixo"): "Eficiente",
    ("Média", "Alto"):  "Enigma",
    ("Média", "Médio"): "Core",
    ("Média", "Baixo"): "Em Desenvolvimento",
    ("Baixa", "Alto"):  "Alto Potencial",
    ("Baixa", "Médio"): "Sólido",
    ("Baixa", "Baixo"): "Em Risco",
}


def classificar_9box(
    perf_media: float,
    potencial: float,
    p33_pot: float,
    p66_pot: float,
) -> str:
    """
    Classifica um funcionário na Matriz 9-Box.

    Performance: Alta ≥ 2.5 / Média ≥ 1.5 / Baixa < 1.5
    Potencial:   Alto > p66 / Médio > p33 / Baixo ≤ p33
    """
    if perf_media >= 2.5:
        perf_cat = "Alta"
    elif perf_media >= 1.5:
        perf_cat = "Média"
    else:
        perf_cat = "Baixa"

    if potencial > p66_pot:
        pot_cat = "Alto"
    elif potencial > p33_pot:
        pot_cat = "Médio"
    else:
        pot_cat = "Baixo"

    return _MAPA_9BOX[(perf_cat, pot_cat)]


# ── Trajetórias individuais ───────────────────────────────────────────────────

def classificar_trajetoria(scores: list[float]) -> str:
    """
    Classifica a trajetória de um funcionário com base no primeiro
    e no último score não-nulo.

    Retorna: "Crescente" | "Estável" | "Decrescente" | "Insuficiente"
    """
    validos = [s for s in scores if s is not None and not (isinstance(s, float) and np.isnan(s))]
    if len(validos) < 2:
        return "Insuficiente"
    diff = validos[-1] - validos[0]
    if diff > 0:
        return "Crescente"
    if diff == 0:
        return "Estável"
    return "Decrescente"


def calcular_trajetorias(df: pd.DataFrame, cols_perf: list[str]) -> pd.Series:
    """
    Aplica classificar_trajetoria a cada linha do DataFrame.
    Retorna uma Series com o mesmo índice de df.
    """
    cols_ord = ordenar_cols_perf(cols_perf)

    def _traj(row):
        return classificar_trajetoria([row[c] for c in cols_ord])

    return df.apply(_traj, axis=1)


# ── Correlações ───────────────────────────────────────────────────────────────

def calcular_r_potencial_perf(
    df: pd.DataFrame,
    cols_perf: list[str],
    min_n: int = 5,
) -> float | None:
    """
    Correlação de Pearson entre Potencial Bruto e performance média.
    Retorna None se a coluna não existir ou amostra for menor que min_n.
    """
    if "Potencial Bruto" not in df.columns or not cols_perf:
        return None
    perf_media = df[cols_perf].mean(axis=1)
    validos = df["Potencial Bruto"].notna() & perf_media.notna()
    if validos.sum() < min_n:
        return None
    return float(df.loc[validos, "Potencial Bruto"].corr(perf_media[validos]))


def correlacoes_assessments_perf(
    df: pd.DataFrame,
    cols_perf: list[str],
    assessments: list[tuple[str, str]] | None = None,
) -> pd.Series:
    """
    Correlação de Pearson de cada assessment com a performance média.

    assessments: lista de (nome_display, nome_coluna). Usa padrão se None.
    Retorna Series vazia se não houver dados suficientes.
    """
    if assessments is None:
        assessments = [
            ("Raciocínio",   "Raciocínio"),
            ("Social",       "Social"),
            ("Motivacional", "Motivacional"),
            ("Cultura",      "Cultura pontuação"),
        ]
    perf_media = df[cols_perf].mean(axis=1)
    resultado = {}
    for nome, col in assessments:
        if col not in df.columns:
            continue
        validos = df[col].notna() & perf_media.notna()
        if validos.sum() < 5:
            continue
        resultado[nome] = float(df.loc[validos, col].corr(perf_media[validos]))
    return pd.Series(resultado).sort_values(ascending=False)


# ── Validação do workbook ─────────────────────────────────────────────────────

def validar_workbook(file) -> dict:
    """
    Valida abas e colunas obrigatórias de um arquivo Excel.

    Retorna dict com chaves:
      sections : list de seções com checks
      errors   : int — número de erros bloqueantes
      warnings : int — número de avisos
      fatal    : str | None — mensagem se o arquivo não puder ser aberto
    """
    SHEETS = ["Tablib Dataset", "performance", "área"]
    REQUIRED_MAIN = [
        "Nome", "Sobrenome", "E-mail", "CPF",
        "Raciocínio", "Social", "Motivacional",
        "Cultura pontuação", "Cultura classificação",
        "Potencial Bruto", "Match",
        "perfil-Comunicação", "atributo-Comunicação",
    ]
    OPTIONAL_GROUPS_MAIN = [
        {"label": "Colunas URL",      "prefix": "URL",    "minCount": 1},
        {"label": "Colunas Início/Fim", "prefix": "Início", "minCount": 1},
    ]
    REQUIRED_PERF = ["CPF"]
    REQUIRED_AREA = ["CPF", "Área"]

    errors, warnings_count, sections = 0, 0, []

    try:
        xls = pd.ExcelFile(file)
    except Exception as e:
        return {"sections": [], "errors": 1, "warnings": 0, "fatal": str(e)}

    # 1. Abas
    sheet_checks = []
    for sheet in SHEETS:
        exists = sheet in xls.sheet_names
        sheet_checks.append({
            "status": "ok" if exists else "err",
            "text": f'Aba "{sheet}"',
            "detail": None if exists else "Aba ausente",
        })
        if not exists:
            errors += 1
    sections.append({"title": "1. Abas do arquivo", "checks": sheet_checks})

    has_all = all(s in xls.sheet_names for s in SHEETS)

    # 2. Tablib Dataset
    main_checks = []
    if not has_all:
        main_checks.append({"status": "info", "text": "Validação ignorada — aba ausente", "detail": None})
    else:
        cols = pd.read_excel(xls, sheet_name="Tablib Dataset", nrows=0).columns.tolist()
        for col in REQUIRED_MAIN:
            found = col in cols
            main_checks.append({
                "status": "ok" if found else "err",
                "text": f'Coluna obrigatória: "{col}"',
                "detail": None if found else "Coluna ausente",
            })
            if not found:
                errors += 1
        for g in OPTIONAL_GROUPS_MAIN:
            found_cols = [c for c in cols if c.startswith(g["prefix"])]
            ok = len(found_cols) >= g["minCount"]
            main_checks.append({
                "status": "ok" if ok else "warn",
                "text": f"{g['label']} ({len(found_cols)} encontrada(s))",
                "detail": None if ok else "Esperado ao menos uma coluna com esse prefixo",
            })
            if not ok:
                warnings_count += 1
    sections.append({"title": "2. Colunas — Tablib Dataset", "checks": main_checks})

    # 3. Performance
    perf_checks = []
    if not has_all:
        perf_checks.append({"status": "info", "text": "Validação ignorada — aba ausente", "detail": None})
    else:
        cols = pd.read_excel(xls, sheet_name="performance", nrows=0).columns.tolist()
        for col in REQUIRED_PERF:
            found = col in cols
            perf_checks.append({
                "status": "ok" if found else "err",
                "text": f'Coluna obrigatória: "{col}"',
                "detail": None if found else "Coluna ausente",
            })
            if not found:
                errors += 1
        perf_cols = [c for c in cols if re.match(r"^performance", c, re.I)]
        ok = len(perf_cols) > 0
        perf_checks.append({
            "status": "ok" if ok else "err",
            "text": f"Colunas de performance ({len(perf_cols)})",
            "detail": None if ok else 'Nenhuma coluna começando com "Performance"',
        })
        if not ok:
            errors += 1
    sections.append({"title": "3. Colunas — performance", "checks": perf_checks})

    # 4. Área
    area_checks = []
    if not has_all:
        area_checks.append({"status": "info", "text": "Validação ignorada — aba ausente", "detail": None})
    else:
        cols = pd.read_excel(xls, sheet_name="área", nrows=0).columns.tolist()
        for col in REQUIRED_AREA:
            found = col in cols
            area_checks.append({
                "status": "ok" if found else "err",
                "text": f'Coluna obrigatória: "{col}"',
                "detail": None if found else "Coluna ausente",
            })
            if not found:
                errors += 1
    sections.append({"title": "4. Colunas — área", "checks": area_checks})

    # 5. CPF em todas as abas
    join_checks = []
    if has_all:
        for sheet in SHEETS:
            cols = pd.read_excel(xls, sheet_name=sheet, nrows=0).columns.tolist()
            found = "CPF" in cols
            join_checks.append({
                "status": "ok" if found else "err",
                "text": f'CPF em "{sheet}"',
                "detail": None if found else "Chave ausente",
            })
            if not found:
                errors += 1
    sections.append({"title": "5. Chave de junção (CPF)", "checks": join_checks})

    return {"sections": sections, "errors": errors, "warnings": warnings_count, "fatal": None}

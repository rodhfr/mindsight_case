"""
test_analytics.py — testes unitários para analytics.py
"""

import math

import numpy as np
import pandas as pd
import pytest

from analytics import (
    calcular_r_potencial_perf,
    calcular_trajetorias,
    classificar_9box,
    classificar_trajetoria,
    correlacoes_assessments_perf,
    detectar_cols_perf,
    ordenar_cols_perf,
    remover_acentos,
    validar_workbook,
)


# ─────────────────────────────────────────────────────────────────────────────
# remover_acentos
# ─────────────────────────────────────────────────────────────────────────────

class TestRemoverAcentos:
    def test_remove_acento_basico(self):
        assert remover_acentos("ação") == "acao"

    def test_remove_acento_portugues(self):
        assert remover_acentos("Ráciocínio") == "Raciocinio"

    def test_string_sem_acento_inalterada(self):
        assert remover_acentos("Comercial") == "Comercial"

    def test_nan_retorna_nan(self):
        resultado = remover_acentos(float("nan"))
        assert pd.isna(resultado)

    def test_none_retorna_nan(self):
        resultado = remover_acentos(None)
        assert pd.isna(resultado)

    def test_string_vazia(self):
        assert remover_acentos("") == ""

    def test_numero_convertido(self):
        assert remover_acentos(42) == "42"


# ─────────────────────────────────────────────────────────────────────────────
# detectar_cols_perf / ordenar_cols_perf
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectarColsPerf:
    def test_detecta_colunas_com_prefixo(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        assert set(cols) == {"perf_1_2018", "perf_2_2018"}

    def test_ignora_colunas_sem_prefixo(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        assert "Área" not in cols
        assert "Potencial Bruto" not in cols

    def test_retorna_vazio_sem_colunas_perf(self):
        df = pd.DataFrame({"nome": ["A"], "area": ["TI"]})
        assert detectar_cols_perf(df) == []

    def test_dataframe_vazio(self):
        assert detectar_cols_perf(pd.DataFrame()) == []


class TestOrdenarColsPerf:
    def test_ordena_cronologicamente(self):
        cols = ["perf_2_2019", "perf_1_2018", "perf_2_2018", "perf_1_2019"]
        esperado = ["perf_1_2018", "perf_2_2018", "perf_1_2019", "perf_2_2019"]
        assert ordenar_cols_perf(cols) == esperado

    def test_ordem_ja_correta_permanece(self):
        cols = ["perf_1_2018", "perf_2_2018"]
        assert ordenar_cols_perf(cols) == cols

    def test_lista_vazia(self):
        assert ordenar_cols_perf([]) == []

    def test_elemento_unico(self):
        assert ordenar_cols_perf(["perf_1_2020"]) == ["perf_1_2020"]


# ─────────────────────────────────────────────────────────────────────────────
# classificar_9box
# ─────────────────────────────────────────────────────────────────────────────

class TestClassificar9Box:
    P33, P66 = 33.0, 66.0

    @pytest.mark.parametrize("perf,pot,esperado", [
        (3.0, 90, "Estrela"),
        (3.0, 50, "Forte Desempenho"),
        (3.0, 10, "Eficiente"),
        (2.0, 90, "Enigma"),
        (2.0, 50, "Core"),
        (2.0, 10, "Em Desenvolvimento"),
        (1.0, 90, "Alto Potencial"),
        (1.0, 50, "Sólido"),
        (1.0, 10, "Em Risco"),
    ])
    def test_todos_os_quadrantes(self, perf, pot, esperado):
        resultado = classificar_9box(perf, pot, self.P33, self.P66)
        assert resultado == esperado

    def test_fronteira_alta_performance(self):
        # 2.5 é o limiar exato para "Alta"
        assert classificar_9box(2.5, 90, self.P33, self.P66) == "Estrela"
        assert classificar_9box(2.49, 90, self.P33, self.P66) == "Enigma"

    def test_fronteira_media_performance(self):
        # 1.5 é o limiar exato para "Média"
        assert classificar_9box(1.5, 10, self.P33, self.P66) == "Em Desenvolvimento"
        assert classificar_9box(1.49, 10, self.P33, self.P66) == "Em Risco"

    def test_fronteira_potencial_alto(self):
        # justo acima de p66 → Alto; exatamente em p66 → Médio
        assert classificar_9box(3.0, 66.1, self.P33, self.P66) == "Estrela"
        assert classificar_9box(3.0, 66.0, self.P33, self.P66) == "Forte Desempenho"

    def test_enigma_caso_critico(self):
        """Alto potencial + performance média = Enigma — caso de maior ROI."""
        resultado = classificar_9box(2.0, 90, self.P33, self.P66)
        assert resultado == "Enigma"


# ─────────────────────────────────────────────────────────────────────────────
# classificar_trajetoria / calcular_trajetorias
# ─────────────────────────────────────────────────────────────────────────────

class TestClassificarTrajetoria:
    def test_crescente(self):
        assert classificar_trajetoria([1.0, 2.0, 3.0]) == "Crescente"

    def test_decrescente(self):
        assert classificar_trajetoria([3.0, 2.0, 1.0]) == "Decrescente"

    def test_estavel(self):
        assert classificar_trajetoria([2.0, 2.0, 2.0]) == "Estável"

    def test_insuficiente_um_score(self):
        assert classificar_trajetoria([2.0]) == "Insuficiente"

    def test_insuficiente_lista_vazia(self):
        assert classificar_trajetoria([]) == "Insuficiente"

    def test_insuficiente_so_nans(self):
        assert classificar_trajetoria([float("nan"), float("nan")]) == "Insuficiente"

    def test_compara_apenas_primeiro_e_ultimo(self):
        # oscila no meio, mas primeiro=1 e último=2 → Crescente
        assert classificar_trajetoria([1.0, 3.0, 1.0, 2.0]) == "Crescente"

    def test_dois_scores_crescente(self):
        assert classificar_trajetoria([1.0, 3.0]) == "Crescente"

    def test_nans_ignorados(self):
        # NaN no meio não conta; primeiro=1, último=3
        assert classificar_trajetoria([1.0, float("nan"), 3.0]) == "Crescente"


class TestCalcularTrajetorias:
    def test_retorna_series_com_mesmo_indice(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        resultado = calcular_trajetorias(df_perf_simples, cols)
        assert list(resultado.index) == list(df_perf_simples.index)

    def test_tamanho_correto(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        resultado = calcular_trajetorias(df_perf_simples, cols)
        assert len(resultado) == len(df_perf_simples)

    def test_valores_validos(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        resultado = calcular_trajetorias(df_perf_simples, cols)
        validos = {"Crescente", "Estável", "Decrescente", "Insuficiente"}
        assert set(resultado.unique()).issubset(validos)

    def test_funcionario_sem_avaliacao_e_insuficiente(self, df_perf_simples):
        # Diego tem perf_1_2018=NaN e perf_2_2018=1.0 → só 1 score válido
        cols = detectar_cols_perf(df_perf_simples)
        resultado = calcular_trajetorias(df_perf_simples, cols)
        assert resultado.iloc[3] == "Insuficiente"


# ─────────────────────────────────────────────────────────────────────────────
# calcular_r_potencial_perf
# ─────────────────────────────────────────────────────────────────────────────

class TestCalcularRPotencialPerf:
    def test_retorna_float(self, df_grande):
        cols = detectar_cols_perf(df_grande)
        r = calcular_r_potencial_perf(df_grande, cols)
        assert isinstance(r, float)
        assert -1.0 <= r <= 1.0

    def test_sem_coluna_potencial_retorna_none(self, df_sem_potencial):
        cols = detectar_cols_perf(df_sem_potencial)
        assert calcular_r_potencial_perf(df_sem_potencial, cols) is None

    def test_cols_perf_vazias_retorna_none(self, df_perf_simples):
        assert calcular_r_potencial_perf(df_perf_simples, []) is None

    def test_amostra_abaixo_do_minimo_retorna_none(self):
        df = pd.DataFrame({
            "perf_1_2018":     [1.0, 2.0, 3.0],
            "Potencial Bruto": [30,  50,  80],
        })
        r = calcular_r_potencial_perf(df, ["perf_1_2018"], min_n=5)
        assert r is None

    def test_todos_nans_retorna_none(self):
        df = pd.DataFrame({
            "perf_1_2018":     [float("nan")] * 10,
            "Potencial Bruto": [50.0] * 10,
        })
        r = calcular_r_potencial_perf(df, ["perf_1_2018"])
        assert r is None

    def test_correlacao_perfeita_positiva(self):
        """Potencial e performance perfeitamente alinhados → r ≈ 1."""
        df = pd.DataFrame({
            "perf_1_2018":     [1.0, 2.0, 3.0, 1.5, 2.5] * 4,
            "Potencial Bruto": [10,  20,  30,  15,  25 ] * 4,
        })
        r = calcular_r_potencial_perf(df, ["perf_1_2018"])
        assert r is not None
        assert r == pytest.approx(1.0, abs=1e-6)

    def test_correlacao_nula_esperada_neste_dataset(self, df_grande):
        """No dataset sintético aleatório, r deve ser próximo de 0."""
        cols = detectar_cols_perf(df_grande)
        r = calcular_r_potencial_perf(df_grande, cols)
        assert r is not None
        assert abs(r) < 0.4   # correlação baixa é esperada em dados aleatórios


# ─────────────────────────────────────────────────────────────────────────────
# correlacoes_assessments_perf
# ─────────────────────────────────────────────────────────────────────────────

class TestCorrelacoesAssessmentsPerf:
    def test_retorna_series(self, df_grande):
        cols = detectar_cols_perf(df_grande)
        resultado = correlacoes_assessments_perf(df_grande, cols)
        assert isinstance(resultado, pd.Series)

    def test_ignora_colunas_ausentes(self, df_perf_simples):
        cols = detectar_cols_perf(df_perf_simples)
        # df_perf_simples tem Raciocínio, Social, Motivacional, Cultura pontuação
        resultado = correlacoes_assessments_perf(df_perf_simples, cols)
        # não deve lançar exceção mesmo que amostra seja pequena
        assert isinstance(resultado, pd.Series)

    def test_assessments_customizados(self, df_grande):
        cols = detectar_cols_perf(df_grande)
        resultado = correlacoes_assessments_perf(
            df_grande, cols,
            assessments=[("Raciocínio", "Raciocínio"), ("Social", "Social")]
        )
        assert set(resultado.index).issubset({"Raciocínio", "Social"})

    def test_valores_entre_menos1_e_1(self, df_grande):
        cols = detectar_cols_perf(df_grande)
        resultado = correlacoes_assessments_perf(df_grande, cols)
        assert (resultado.abs() <= 1.0).all()

    def test_ordenado_decrescente(self, df_grande):
        cols = detectar_cols_perf(df_grande)
        resultado = correlacoes_assessments_perf(df_grande, cols)
        if len(resultado) > 1:
            assert list(resultado.values) == sorted(resultado.values, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# validar_workbook
# ─────────────────────────────────────────────────────────────────────────────

class TestValidarWorkbook:
    def test_arquivo_invalido_retorna_fatal(self, arquivo_invalido):
        resultado = validar_workbook(arquivo_invalido)
        assert resultado["fatal"] is not None
        assert resultado["errors"] >= 1

    def test_excel_valido_sem_erros(self, excel_valido):
        resultado = validar_workbook(excel_valido)
        assert resultado["fatal"] is None
        assert resultado["errors"] == 0

    def test_excel_sem_abas_gera_erros(self, excel_sem_abas):
        resultado = validar_workbook(excel_sem_abas)
        assert resultado["fatal"] is None
        assert resultado["errors"] >= 3   # 3 abas ausentes

    def test_excel_sem_colunas_gera_erros(self, excel_sem_colunas):
        resultado = validar_workbook(excel_sem_colunas)
        assert resultado["fatal"] is None
        assert resultado["errors"] > 0

    def test_estrutura_retorno(self, excel_valido):
        resultado = validar_workbook(excel_valido)
        assert "sections" in resultado
        assert "errors" in resultado
        assert "warnings" in resultado
        assert "fatal" in resultado

    def test_secoes_esperadas(self, excel_valido):
        resultado = validar_workbook(excel_valido)
        titulos = [s["title"] for s in resultado["sections"]]
        assert any("Abas" in t for t in titulos)
        assert any("CPF" in t for t in titulos)

    def test_todos_os_checks_tem_status(self, excel_valido):
        resultado = validar_workbook(excel_valido)
        for secao in resultado["sections"]:
            for check in secao["checks"]:
                assert check["status"] in ("ok", "err", "warn", "info")

    def test_excel_sem_abas_marca_checks_como_info(self, excel_sem_abas):
        """Quando abas estão ausentes, os checks dependentes ficam como 'info'."""
        resultado = validar_workbook(excel_sem_abas)
        # A seção de colunas deve indicar "ignorada" e não adicionar erros
        for secao in resultado["sections"][1:]:   # pula a seção de abas
            for check in secao["checks"]:
                if check["status"] == "info":
                    assert "ignorada" in check["text"].lower() or "ignorada" in (check["detail"] or "").lower()

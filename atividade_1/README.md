# Atividade 1 — People Analytics: Performance e Contratação

Estudo quantitativo sobre dados psicométricos e avaliações de performance de funcionários, com o objetivo de identificar **o que prediz performance** e como usar isso para tomar melhores decisões de **contratação** e **movimentação interna**.

---

## Estrutura do projeto

```
atividade_1/
├── Dados - Atividade 1.xlsx         # base original (input)
├── Dados - Atividade 1_limpo.xlsx   # base após limpeza e merge (gerada por limpeza_dados.py)
│
├── limpeza_dados.py                 # script de limpeza e merge das 3 abas do Excel
├── limpeza_dados.ipynb              # versão notebook do script de limpeza
├── pre_processamento.ipynb          # exploração inicial da base bruta
│
├── analise_basica.ipynb             # análise completa (15 seções)
├── streamlit_app.py                 # dashboard interativo
│
├── alpha/                           # módulo com lógica testável + testes
│   ├── analytics.py                 # funções puras extraídas do dashboard
│   ├── streamlit_app.py             # cópia do dashboard (usa analytics.py)
│   ├── pytest.ini
│   └── tests/
│       ├── conftest.py              # fixtures compartilhadas
│       └── test_analytics.py        # 61 testes unitários
│
└── requirements.txt
```

---

## Como rodar

### Pré-requisitos

```bash
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 1. Limpeza dos dados

Gera o arquivo `Dados - Atividade 1_limpo.xlsx` com as 3 abas do Excel mergidas por CPF:

```bash
python limpeza_dados.py
```

### 2. Dashboard interativo

```bash
streamlit run streamlit_app.py
```

Acesse `http://localhost:8501`, faça upload de `Dados - Atividade 1.xlsx` e explore as 8 abas:

| Aba | O que mostra |
|-----|-------------|
| Distribuição de Scores | Histograma de scores 1–3 por semestre |
| Performance por Área | Médias e evolução temporal por departamento |
| Potencial & 9-Box | Matriz 9-Box com quadrantes e listagem nominal |
| Atributos | Radar dos 16 atributos comportamentais por quadrante |
| Assessments | Correlação dos assessments com performance + fit cultural |
| Clustering | K-Means dos perfis comportamentais (k=4) |
| Evolução Individual | Curva de performance por funcionário ao longo dos semestres |
| Recomendações | Síntese prescritiva com regressão múltipla e candidatos a movimentação |

### 3. Notebook de análise

Abrir `analise_basica.ipynb` no Jupyter. Requer o arquivo limpo gerado no passo 1.

```bash
jupyter notebook analise_basica.ipynb
```

### 4. Testes

```bash
cd alpha
pytest
```

---

## Principais achados

### O que NÃO prediz performance
O **Potencial Bruto** — principal instrumento de avaliação da empresa — tem correlação de **r ≈ −0.07** com a performance entregue, praticamente nula. Usar esse score como critério principal de contratação ou promoção é uma régua que não mede o que importa.

### O que PREDIZ performance
Os **atributos comportamentais por área** têm mais sinal do que qualquer assessment isolado. O perfil ideal varia entre departamentos: o que gera resultado em Comercial é diferente do que gera em Operações. A **regressão múltipla** (Seção 15 do notebook / Aba Recomendações do dashboard) identifica os preditores de maior peso quando todas as variáveis competem simultaneamente.

### Fit cultural como teto silencioso
A mediana de fit cultural é **~42/100**, com a maioria dos funcionários nas faixas Baixo e Médio-Baixo. Funcionários com baixo alinhamento cultural tendem a entregar menos independentemente de capacidade técnica. A solução começa na seleção.

### Avaliação sem poder discriminatório
**60–70% de todas as avaliações** são score 2 (Atende expectativas) em todos os semestres e áreas. Essa concentração é improvável numa distribuição real de performance — indica que gestores evitam os extremos. Sem discriminação, nenhuma decisão de promoção, desenvolvimento ou desligamento tem base quantitativa sólida.

---

## Análises do notebook (`analise_basica.ipynb`)

| # | Seção | Método |
|---|-------|--------|
| 1 | Cobertura dos Dados por Semestre | Contagem de não-nulos por período |
| 2 | Distribuição de Scores | Histograma empilhado por semestre |
| 3 | Evolução Temporal | Linha de scores e cobertura por área |
| 4 | Médias de Performance por Área | Série temporal de médias (escala 1–3) |
| 5 | Correlação Potencial Bruto × Performance | Pearson r + scatter com regressão |
| 6 | Matriz 9-Box | Heatmap de contagem por quadrante |
| 7 | Listagem por Quadrante da 9-Box | Tabela nominal com quadrantes |
| 8 | Fit Cultural por Área | Boxplot + stacked bar por classificação |
| 9 | Perfil de Atributos por Quadrante | Radar Estrela vs Em Risco e Enigma vs Core |
| 10 | Atributos Preditivos por Área | Heatmap de correlações por departamento |
| 11 | Tempo de Conclusão vs Score | Scatter por assessment com r de Pearson |
| 12 | Clusterização (K-Means) | Cotovelo + silhouette + radar dos 4 arquétipos |
| 13 | Fit Cultural — Distribuição e Impacto | Distribuição de classificações + boxplot de performance |
| 14 | Trajetórias Individuais | Crescente / Estável / Decrescente por funcionário |
| 15 | Regressão Múltipla | LinearRegression padronizada — R² e coeficientes |

---

## Recomendações prioritárias

1. **Substituir o Potencial Bruto** como critério de seleção pelo perfil comportamental ideal por área
2. **Incorporar fit cultural** como filtro eliminatório no processo seletivo (acima do percentil 50)
3. **Calibrar o processo de avaliação** — treinar gestores para diferenciar scores além do 2
4. **Agir sobre o quadrante Enigma** (alto potencial + baixa performance) — maior ROI de intervenção
5. **Usar a regressão múltipla** como bússola de seleção, atualizando o modelo conforme a base cresce

---

## Módulo `alpha/` — lógica testável

`analytics.py` expõe as funções de negócio como funções puras, independentes do Streamlit:

```python
from analytics import (
    detectar_cols_perf,       # identifica colunas de performance
    ordenar_cols_perf,        # ordena cronologicamente
    classificar_9box,         # classifica funcionário na Matriz 9-Box
    classificar_trajetoria,   # Crescente / Estável / Decrescente
    calcular_trajetorias,     # aplica a toda a base
    calcular_r_potencial_perf,        # correlação Potencial × Performance
    correlacoes_assessments_perf,     # correlação de cada assessment
    validar_workbook,         # valida abas e colunas do Excel de entrada
)
```

```bash
cd alpha && pytest -v
# 61 passed in 0.85s
```

---

## Dependências principais

| Pacote | Uso |
|--------|-----|
| `pandas` / `numpy` | manipulação de dados |
| `streamlit` | dashboard interativo |
| `plotly` | gráficos interativos no dashboard |
| `matplotlib` / `seaborn` | gráficos estáticos no notebook |
| `scikit-learn` | K-Means, regressão múltipla, StandardScaler |
| `openpyxl` | leitura/escrita de Excel |
| `pytest` | testes unitários |

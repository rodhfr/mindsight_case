# Case Analista de DataOps — Mindsight

Esse repositório contém a solução para as duas atividades do case técnico da Mindsight. Cada uma vive na sua própria pasta e tem seu próprio README com detalhes de execução.

---

## Atividade 1 — People Analytics

**O desafio:** a empresa tem dados psicométricos e avaliações de performance dos funcionários, mas ninguém sabe muito bem o que fazer com eles. O pedido foi: descubra o que prediz performance e traduza isso em recomendações práticas para contratação e movimentação interna.

**O que foi feito:**

A base chegou em três abas de Excel separadas (dados de assessments, performance por semestre e área dos funcionários). O primeiro passo foi juntar tudo por CPF e limpar — renomear colunas, converter datas, criar flags de quais testes cada pessoa realizou, padronizar categorias de fit cultural.

Com a base limpa em mãos, a análise seguiu em 15 seções no notebook `analise_basica.ipynb`, cobrindo desde a distribuição dos scores até uma regressão múltipla para identificar os preditores de maior peso. O mesmo raciocínio foi embutido em um dashboard Streamlit com 8 abas interativas, onde é possível explorar os dados visualmente — incluindo a Matriz 9-Box, clustering de perfis comportamentais e evolução individual de cada funcionário.

**O que o dado revelou:**

O achado mais importante foi que o **Potencial Bruto** — principal instrumento de avaliação — tem correlação quase nula com a performance entregue (r ≈ −0.07). Usar ele como critério de seleção é basicamente um sorteio. O que tem mais sinal são os **atributos comportamentais específicos por área**: o perfil que gera resultado em Comercial é diferente do que gera em Operações. Além disso, o fit cultural mediano está em apenas 42/100 — e funcionários com baixo alinhamento cultural tendem a entregar menos independentemente de capacidade técnica.

Outro ponto relevante: 60–70% de todas as avaliações são score 2 ("atende expectativas") em todos os semestres e áreas. Essa concentração improvável indica que gestores evitam dar notas extremas, o que esvazia o poder discriminatório da avaliação e compromete qualquer decisão baseada nela.

**Como rodar:**

```bash
cd atividade_1
pip install -r requirements.txt

# limpeza
python limpeza_dados.py "Dados - Atividade 1.xlsx"

# dashboard
streamlit run streamlit_app.py

# testes
cd alpha && pytest
```

Mais detalhes em [`atividade_1/README.md`](atividade_1/README.md).

---

## Atividade 2 — ETL People Hub

**O desafio:** um cliente enviou uma planilha com alterações cadastrais dos colaboradores (salários, cargos e áreas) e precisava que essas mudanças entrassem no sistema People Hub. O problema é que o sistema não aceita a planilha bruta — cada módulo tem seu próprio formato de importação, e os dados precisam ser cruzados com o estado atual antes de gerar qualquer arquivo.

**O que foi feito:**

O `etl.py` resolve isso em três etapas: lê as alterações do cliente e os dados atuais do sistema, cruza os registros, e gera os arquivos prontos para importação em cada módulo — salários, cargos, áreas e instância de área.

Alguns detalhes práticos que demandaram atenção:

- **Matching de nomes:** a planilha do cliente vem com acentos e caixa mista; a base do sistema vem sem acento e em maiúsculas. A função `normalize_text()` resolve isso via decomposição NFD antes de qualquer comparação.
- **Roberto Tonetti duplicado:** o mesmo funcionário aparece com dois IDs diferentes na base (481 e 102). O critério de desempate foi preferir o ID com histórico em mais tabelas — o 481 vence por aparecer tanto em áreas quanto em cargos.
- **raise_type:** compara a data da alteração com o último salário registrado para determinar se é `initial` (sem histórico) ou `raise` (salário já existia).
- **Cargos e áreas:** só registros sem `end_date` são ativos. Se mudou, o registro antigo é fechado com `end_date` e um novo é criado. Se não mudou, nada é alterado.

Ao final, o pipeline também gera um arquivo `pendencias.xlsx` com as 7 pessoas que não puderam ser processadas por não terem cadastro em `Pessoas - Full` — elas precisam ser adicionadas ao sistema antes de rodar o ETL novamente.

**Como rodar:**

```bash
cd atividade_2
pip install -r requirements.txt
python etl.py
```

Os arquivos de saída aparecem na pasta `objetivo/`. Mais detalhes em [`atividade_2/README.md`](atividade_2/README.md).

---

## Estrutura geral

```
mindsight_case/
├── atividade_1/    # People Analytics — análise, dashboard e testes
└── atividade_2/    # ETL People Hub — pipeline de atualização cadastral
```

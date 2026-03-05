# Atividade 2 — ETL People Hub

O contexto do case: sou um Analista de DataOps da Mindsight e recebi uma planilha de alterações de um cliente. Meu papel é processar essas alterações e gerar os arquivos de importação para atualizar o sistema People Hub com os salários, cargos e áreas corretos de cada funcionário.

## O que o script faz

O `etl.py` lê todos os arquivos de entrada, faz o matching dos funcionários pelo nome com a base `Pessoas - Full` e gera quatro planilhas prontas para importar no sistema:

- `salarios_objetivo.xlsx` — novos registros de salário com `raise_type` classificado como `INITIAL` ou `RAISE`
- `instancia_area_objetivo.xlsx` — áreas que não existiam no sistema
- `areas_objetivo.xlsx` — fechamento de áreas antigas (com `end_date`) + abertura das novas
- `cargos_objetivo.xlsx` — fechamento de cargos antigos (com `end_date`) + abertura dos novos
- `pendencias.xlsx` — pessoas que não puderam ser processadas (sem cadastro ou nome duplicado)

Todos os arquivos gerados ficam na pasta `objetivo/`.

## Decisões de implementação

**Matching de nomes:** a planilha do cliente vem com nomes acentuados e em caixa mista; `Pessoas - Full` vem normalizado. Antes de fazer o join, ambos passam por `normalize_text()` — que remove acentos via NFD e padroniza espaços — para evitar falsos negativos.

**Duplicata de person:** Roberto Tonetti aparece com dois `person` IDs diferentes na base. O critério de desempate foi preferir o ID com histórico em mais tabelas (áreas + cargos), que é o 481.

**Raise type:** compara a data da alteração do cliente com a data do último salário registrado no sistema para aquela pessoa. Se não tem histórico é `INITIAL`; se a data é mais recente é `RAISE`.

**Cargos e áreas:** só registros sem `end_date` são considerados "ativos". Se o cargo/área mudou, o registro antigo é fechado com `end_date` e um novo é criado. Se não mudou, nada é alterado.

**Instância de área:** IDs novos são gerados sequencialmente a partir do maior ID existente, apenas para uso interno no mapeamento. O arquivo exportado sai com `id` vazio para o sistema gerar.

## Pendências encontradas

- **7 pessoas sem cadastro** em `Pessoas - Full` — sem o `person` ID não dá para criar nenhum registro. Estão em `pendencias.xlsx` e precisam ser cadastradas no sistema antes de rodar o ETL novamente.
- **Roberto Tonetti duplicado** — dois IDs para o mesmo nome. O 481 foi usado por ter mais histórico, mas o ideal é limpar essa duplicata na base.

## Como rodar

```bash
pip install -r requirements.txt
python etl.py
```

Os arquivos de saída serão gerados (ou sobrescritos) na pasta `objetivo/`.

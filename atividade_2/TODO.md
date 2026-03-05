# TODO — Atividade 2

## ETL

### Setup
- [x] leitura de arquivos por extensão no utils.py
- [x] normalização de texto (acentos, espaços)
- [x] separar utils.py do etl.py
- [x] pasta objetivo/ pra guardar os arquivos gerados

### Extract
- [x] carregar todos os arquivos de entrada
- [x] header da planilha do cliente tá na linha 3, ajustar

### Pessoas
- [x] normalizar nomes pra fazer o match com Pessoas Full
- [x] separar nome/sobrenome pra poder fazer o join
- [x] Roberto Tonetti aparece duplicado — prefere o que tem histórico em áreas e cargos
- [x] gerar pendencias.xlsx com dois casos:
  - [x] pessoa não encontrada em Pessoas Full
  - [x] nome duplicado (ambíguo)

### Salários
- [x] classificar raise_type comparando data do cliente com último salário no sistema
- [x] não reprocessar registros que já existem (mesmo person + data)
- [x] id vazio, sistema gera

### Instância de Área
- [x] identificar departamentos novos
- [x] gerar ids sequenciais internamente pra usar no mapeamento
- [x] exportar com id vazio

### Área
- [x] só áreas ativas (sem end_date)
- [x] se mudou: fecha registro antigo + abre novo
- [x] se não tem área no sistema: só cria
- [x] incluir inativos que aparecem nas alterações

### Cargos
- [x] só cargos ativos (sem end_date)
- [x] normalizar nomes (Cargos Full vem em caps sem acento)
- [x] se mudou: fecha registro antigo + abre novo
- [x] se não tem cargo no sistema: só cria
- [x] level = primeira palavra do cargo

### Load
- [x] objetivo/salarios_objetivo.xlsx
- [x] objetivo/instancia_area_objetivo.xlsx
- [x] objetivo/areas_objetivo.xlsx
- [x] objetivo/cargos_objetivo.xlsx
- [x] objetivo/pendencias.xlsx

---

## Pendências encontradas

- [ ] **7 pessoas sem cadastro** — não tem como processar sem o person id. Estão em pendencias.xlsx, precisam ser cadastradas no sistema antes de rodar o ETL de novo
- [ ] **Roberto Tonetti duplicado** — person 481 e 102 com o mesmo nome em Pessoas Full. O 481 tem histórico em áreas e cargos então foi usado, mas o ideal é limpar essa duplicata na base
---

## Apresentação

- [ ] explicar como foi feito o matching de nomes
- [ ] mostrar o que foi encontrado em pendencias.xlsx
- [ ] explicar a lógica do raise_type
- [ ] explicar quando edita vs quando cria (cargos e áreas)
- [ ] propor o que fazer com os pendentes

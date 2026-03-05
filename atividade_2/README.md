# Atividade 2 — ETL People Hub

O cliente enviou uma planilha com alterações cadastrais dos colaboradores (salário, cargo e área) e precisava que esses dados fossem importados no People Hub. O problema é que o sistema não aceita a planilha bruta — ela precisa ser cruzada com a base atual, comparada registro a registro, e exportada em formatos específicos para cada módulo.

É isso que o `etl.py` faz: lê as alterações do cliente, cruza com o estado atual do sistema e gera os arquivos prontos para importação.

---

## Estrutura do projeto

```
atividade_2/
├── Alterações do Cliente.xlsx           # planilha de entrada com as mudanças
│
├── Dados atuais no sistema/             # estado atual do People Hub (inputs)
│   ├── Pessoas - Full.xlsx
│   ├── Áreas - Full.xlsx
│   ├── Instância de Áreas - Full.xlsx
│   ├── Cargos - Full.csv
│   └── Salários - Full.csv
│
├── Modelos/                             # templates de importação do sistema
│   ├── Modelo Salários.xlsx
│   ├── Modelo Áreas.xlsx
│   ├── Modelo Instância de Área.xlsx
│   └── Modelo Cargos.xlsx
│
├── etl.py                               # pipeline principal (Extract → Transform → Load)
├── utils.py                             # leitura de arquivos e normalização de texto
├── requirements.txt
│
└── objetivo/                            # arquivos gerados (prontos para importar)
    ├── salarios_objetivo.xlsx
    ├── instancia_area_objetivo.xlsx
    ├── areas_objetivo.xlsx
    ├── cargos_objetivo.xlsx
    └── pendencias.xlsx
```

---

## Como rodar

```bash
pip install -r requirements.txt
python etl.py
```

Os arquivos de saída serão gerados (ou sobrescritos) na pasta `objetivo/`.

---

## O que o ETL produz

Para cada módulo do People Hub, o pipeline gera um arquivo no formato de importação do sistema:

| Arquivo | O que contém |
|---------|--------------|
| `salarios_objetivo.xlsx` | Novos registros de salário com `raise_type` `initial` ou `raise` |
| `instancia_area_objetivo.xlsx` | Departamentos que ainda não existem como instância de área no sistema |
| `areas_objetivo.xlsx` | Fechamento das áreas antigas (com `end_date`) + abertura das novas |
| `cargos_objetivo.xlsx` | Fechamento dos cargos antigos (com `end_date`) + abertura dos novos |
| `pendencias.xlsx` | Pessoas que não puderam ser processadas, com o motivo |

---

## Decisões de implementação

**Matching de nomes**
A planilha do cliente vem com nomes acentuados e em caixa mista; `Pessoas - Full` vem sem acento e em maiúsculas. Para não ter falsos negativos no join, os dois lados passam por `normalize_text()` em `utils.py` antes da comparação — que decompõe os acentos via NFD, descarta os diacríticos e normaliza espaços.

**Duplicata de person**
Roberto Tonetti aparece com dois `person` IDs diferentes na base (481 e 102). O critério de desempate foi preferir o ID com histórico em mais tabelas: quem aparece tanto em áreas quanto em cargos tem prioridade sobre quem aparece em apenas uma — o 481 vence.

**raise_type**
Compara a data da alteração do cliente com a data do último salário registrado no sistema para aquela pessoa. Se não há histórico: `initial`. Se a data é mais recente: `raise`. Registros com o mesmo `person` + data já existentes no sistema são ignorados e logados no terminal.

**Cargos e áreas**
Só registros sem `end_date` são considerados ativos. Se o cargo ou área mudou: o registro antigo é fechado (preenchendo `end_date`) e um novo é criado. Se não mudou, nada é alterado.

**Instância de área**
IDs são gerados sequencialmente a partir do maior ID existente, apenas para uso interno no mapeamento durante a execução. O arquivo exportado sai com `id` vazio para o sistema gerar o ID real no upload.

---

## Pendências encontradas

- **7 pessoas sem cadastro** em `Pessoas - Full` — sem o `person` ID não é possível criar nenhum registro. Estão em `pendencias.xlsx` e precisam ser cadastradas no sistema antes de rodar o ETL novamente.
- **Roberto Tonetti duplicado** — dois IDs (481 e 102) para o mesmo nome. O 481 foi usado por ter mais histórico, mas o ideal é limpar essa duplicata na base.

---

## Dependências

| Pacote | Uso |
|--------|-----|
| `pandas` | manipulação e cruzamento dos dados |
| `openpyxl` | leitura/escrita de Excel |

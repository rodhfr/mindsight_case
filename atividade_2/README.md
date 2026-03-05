# Atividade 2 — ETL People Hub

Pipeline de processamento de alterações cadastrais de um cliente. O script lê uma planilha de mudanças, cruza com a base atual do sistema People Hub e gera os arquivos prontos para importação — atualizando salários, cargos e áreas de cada funcionário.

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

## O que o ETL faz

O `etl.py` processa cada linha da planilha do cliente e gera cinco arquivos:

| Arquivo | Conteúdo |
|---------|----------|
| `salarios_objetivo.xlsx` | Novos registros de salário com `raise_type` classificado como `INITIAL` ou `RAISE` |
| `instancia_area_objetivo.xlsx` | Instâncias de área que não existiam no sistema |
| `areas_objetivo.xlsx` | Fechamento de áreas antigas (com `end_date`) + abertura das novas |
| `cargos_objetivo.xlsx` | Fechamento de cargos antigos (com `end_date`) + abertura dos novos |
| `pendencias.xlsx` | Pessoas que não puderam ser processadas (sem cadastro ou nome duplicado) |

---

## Decisões de implementação

**Matching de nomes**
A planilha do cliente vem com nomes acentuados e em caixa mista; `Pessoas - Full` vem normalizado. Antes do join, ambos passam por `normalize_text()` em `utils.py` — que remove acentos via NFD e padroniza espaços — para evitar falsos negativos.

**Duplicata de person**
Roberto Tonetti aparece com dois `person` IDs diferentes na base. O critério de desempate foi preferir o ID com histórico em mais tabelas (áreas + cargos), que é o 481.

**Raise type**
Compara a data da alteração do cliente com a data do último salário registrado no sistema para aquela pessoa. Se não há histórico: `INITIAL`. Se a data é mais recente: `RAISE`. Registros com o mesmo `person` + data não são reprocessados.

**Cargos e áreas**
Só registros sem `end_date` são considerados ativos. Se o cargo ou área mudou: o registro antigo é fechado com `end_date` e um novo é criado. Se não mudou, nada é alterado.

**Instância de área**
IDs novos são gerados sequencialmente a partir do maior ID existente, apenas para uso interno no mapeamento. O arquivo exportado sai com `id` vazio para o sistema gerar.

---

## Pendências encontradas

- **7 pessoas sem cadastro** em `Pessoas - Full` — sem o `person` ID não é possível criar nenhum registro. Estão listadas em `pendencias.xlsx` e precisam ser cadastradas no sistema antes de rodar o ETL novamente.
- **Roberto Tonetti duplicado** — dois IDs (481 e 102) para o mesmo nome. O 481 foi usado por ter mais histórico, mas o ideal é limpar essa duplicata na base.

---

## Dependências principais

| Pacote | Uso |
|--------|-----|
| `pandas` | manipulação e cruzamento dos dados |
| `openpyxl` | leitura/escrita de Excel |

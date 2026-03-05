import pandas as pd
from utils import read_df_by_suffix, normalize_text, mv_col_to_start

def classify_raise(row):
    if pd.isna(row['person']):
        return 'others'  # pessoa sem ID no sistema
    if pd.isna(row['ultima_data_salario']):
        return 'initial'  # pessoa sem historico de salario no sistema
    if row['Data de Alteração'] > row['ultima_data_salario']:
        return 'raise'  # data mais recente que o ultimo salario no sistema
    return 'initial'  # mesma data ou anterior: primeiro registro


def main():
    arquivos = {
        "alteracoes_cliente": "Alterações do Cliente.xlsx",
        "areas":              "Dados atuais no sistema/Áreas - Full.xlsx",
        "pessoas":            "Dados atuais no sistema/Pessoas - Full.xlsx",
        "salarios":           "Dados atuais no sistema/Salários - Full.csv",
        "instancia_areas":    "Dados atuais no sistema/Instância de Áreas - Full.xlsx",
        "cargos":             "Dados atuais no sistema/Cargos - Full.csv",
    }
    # dict comprehension para gerar dataframe['nome_do_df']
    dataframes = {name: read_df_by_suffix(path) for name, path in arquivos.items()}

    # --- ALTERACOES ---
    df_alteracoes = dataframes['alteracoes_cliente']
    # header esta na 3a linha do arquivo
    df_alteracoes.columns = df_alteracoes.iloc[2]
    df_alteracoes = df_alteracoes.iloc[3:].reset_index(drop=True)
    df_alteracoes[["nome", "sobrenome"]] = (
        df_alteracoes["Colaborador"]
        .str.upper()
        .apply(normalize_text)
        .str.split(r"\s+", n=1, expand=True)
    )

    # --- PESSOAS ---
    df_pessoas = dataframes['pessoas']
    df_pessoas_original = df_pessoas.copy()

    # resolve duplicatas de nome: prefere o person com historico em mais tabelas
    # (ex: Roberto Tonetti 481 aparece em areas+cargos; 102 so em cargos → 481 vence)
    pessoas_em_ambas = set(dataframes['cargos']['person']) & set(dataframes['areas']['person'])
    pessoas_em_alguma = set(dataframes['cargos']['person']) | set(dataframes['areas']['person'])

    df_pessoas['prioridade'] = 0
    df_pessoas.loc[df_pessoas['person'].isin(pessoas_em_alguma), 'prioridade'] = 1
    df_pessoas.loc[df_pessoas['person'].isin(pessoas_em_ambas), 'prioridade'] = 2
    df_pessoas = (
        df_pessoas
        .sort_values('prioridade', ascending=False)
        .drop_duplicates(subset=['nome', 'sobrenome'])
        .drop(columns='prioridade')
    )

    # LEFT JOIN para obter o person de cada colaborador pelo nome
    """
    SELECT *
    FROM alteracoes
    LEFT JOIN pessoas ON nome AND sobrenome
    """
    df_ids = df_alteracoes.merge(
        df_pessoas[["person", "nome", "sobrenome"]],
        on=["nome", "sobrenome"],
        how="left"
    )
    # com o merge a coluna fica float64 porque int64 nao suporta nan.
    # astype("Int64") converte para nullable integer
    df_ids["person"] = df_ids["person"].astype("Int64")
    df_ids = mv_col_to_start(df_ids, "person")

    # --- PENDENCIAS ---
    # 1. pessoas que nao encontrou o id person
    nao_encontrados = df_ids[df_ids['person'].isna()].copy()
    nao_encontrados['motivo'] = 'pessoa nao encontrada em Pessoas - Full'

    # 2. nomes duplicados no sistema
    # duplicated() com keep=False marca todas as ocorrencias de duplicatas
    nomes_dup = df_pessoas_original[
        df_pessoas_original.duplicated(subset=['nome', 'sobrenome'], keep=False)
    ][['nome', 'sobrenome']]

    # INNER JOIN para encontrar os colaboradores com nome duplicado
    """
    SELECT df_ids.*
    FROM df_ids
    INNER JOIN nomes_dup ON nome AND sobrenome
    """
    ambiguos = df_ids.merge(nomes_dup, on=['nome', 'sobrenome']).drop_duplicates(subset=['nome', 'sobrenome'])
    ambiguos['motivo'] = 'nome duplicado em Pessoas - Full'

    # 3. junta e exporta pendencias
    pd.concat([nao_encontrados, ambiguos], ignore_index=True).to_excel('objetivo/pendencias.xlsx', index=False)

    # remove pendencias do fluxo principal
    """
    No exemplo do case
    * Foram identificadas 7 pessoas na planilha do cliente sem correspondência em Pessoas - Full
    * Sem o person, não é possível criar registros de salário, cargo ou área
    * Estão documentadas em pendencias.xlsx e devem ser cadastradas no sistema antes de serem processadas
    """
    df_ids = df_ids[df_ids['person'].notna()]

    ### SALARIOS ###
    df_salario = dataframes['salarios']
    df_salario['date_parsed'] = pd.to_datetime(df_salario['date'], format='%d/%m/%Y')

    # pega a data mais recente de salario por person para classificar raise_type
    ultima_data = df_salario.groupby('person')['date_parsed'].max().rename('ultima_data_salario')
    df_ids = df_ids.merge(ultima_data, on='person', how='left')

    """
    Regras de negocio:
    id:         vazio para criar novo registro (salario nunca e editado)
    person:     codigo da pessoa
    date:       data que comecou a receber o salario
    salary:     valor do salario
    raise_type: initial (primeiro salario) | raise (aumento) | others (sem person)
    """
    df_ids['id'] = ""
    df_ids['date'] = df_ids['Data de Alteração']
    df_ids['salary'] = df_ids['Salário']
    df_ids['raise_type'] = df_ids.apply(classify_raise, axis=1)

    cols_objetivo = ["id", "person", "date", "salary", "raise_type"]
    df_novos_salarios = df_ids[cols_objetivo].copy()

    # LEFT JOIN com indicator: filtra registros que ja existem no sistema (mesmo person + date)
    """
    SELECT novos.*
    FROM novos_salarios novos
    LEFT JOIN salarios_full sal ON novos.person = sal.person AND novos.date = sal.date
    WHERE sal.person IS NULL
    """
    df_novos_salarios['date_key'] = pd.to_datetime(df_novos_salarios['date']).dt.date
    df_salario['date_key'] = df_salario['date_parsed'].dt.date
    df_novos_salarios = df_novos_salarios.merge(
        df_salario[['person', 'date_key']], on=['person', 'date_key'], how='left', indicator=True
    )
    ja_existentes = df_novos_salarios[df_novos_salarios['_merge'] == 'both'][['person', 'date', 'salary']]
    print(f"\n[SALARIOS] {len(ja_existentes)} registros ignorados por ja existirem no sistema:")
    print(ja_existentes.to_string(index=False))
    df_novos_salarios = df_novos_salarios.query('_merge == "left_only"').drop(columns=['date_key', '_merge'])

    # exporta apenas os novos registros no formato de importacao do sistema
    df_novos_salarios.to_excel("objetivo/salarios_objetivo.xlsx", index=False)


    ### INSTÂNCIA DE ÁREA ###
    df_instancia = dataframes['instancia_areas']

    # departamentos novos que nao existem no sistema
    depts_existentes = set(df_instancia['name'])
    depts_novos = [d for d in df_ids['Departamento'].dropna().unique() if d not in depts_existentes]

    # atribui IDs subsequentes aos atuais
    proximo_id = df_instancia['id'].max() + 1
    df_novas_instancias = pd.DataFrame({
        'id': range(proximo_id, proximo_id + len(depts_novos)),
        'name': depts_novos
    })
    print(f"\n[INSTANCIA AREA] {len(df_novas_instancias)} novas areas:")
    print(df_novas_instancias.to_string(index=False))

    # exporta com id vazio: sistema gera o id automaticamente no upload
    # os ids sequenciais sao usados apenas internamente para preencher a coluna area
    df_novas_instancias.assign(id='')[['id', 'name']].to_excel('objetivo/instancia_area_objetivo.xlsx', index=False)

    # mapa completo nome -> id (existentes + novos)
    df_instancia_completa = pd.concat([df_instancia, df_novas_instancias], ignore_index=True)
    dept_to_id = df_instancia_completa.set_index('name')['id'].to_dict()

    ### AREA ###
    """
    id:         vazio para criar novo | id existente para editar (fechar area antiga com end_date)
    person:     codigo da pessoa
    start_date: data que comecou na area
    end_date:   data que terminou na area
    area:       codigo da instancia de area
    """
    df_areas = dataframes['areas']
    df_areas_ativas = df_areas[df_areas['end_date'].isna()]

    # apenas registros Atual para saber o estado atual de cada person
    df_atual = df_ids[df_ids['Situação'].str.startswith('Atual')].copy()
    df_atual['area_nova'] = df_atual['Departamento'].map(dept_to_id)

    # LEFT JOIN para trazer a area ativa atual de cada person no sistema
    """
    SELECT *
    FROM df_atual
    LEFT JOIN areas_ativas ON person
    """
    df_area_merge = df_atual.merge(
        df_areas_ativas[['id', 'person', 'start_date', 'area']].rename(columns={'id': 'area_id'}),
        on='person', how='left'
    )

    edicoes = []  # fecha area antiga preenchendo end_date no registro existente
    criacoes = []  # abre nova area

    for _, row in df_area_merge.iterrows():
        area_atual = row['area']
        area_nova  = row['area_nova']
        person     = row['person']
        data       = row['Data de Alteração']

        if pd.isna(area_atual):
            # pessoa sem area no sistema: apenas cria
            criacoes.append({'id': '', 'person': person, 'start_date': data, 'end_date': '', 'area': area_nova})
        elif area_atual != area_nova:
            # mudou de area: fecha antiga + abre nova
            edicoes.append({'id': row['area_id'], 'person': person, 'start_date': row['start_date'], 'end_date': data, 'area': area_atual})
            criacoes.append({'id': '', 'person': person, 'start_date': data, 'end_date': '', 'area': area_nova})
        # mesma area: sem alteracao

    df_areas_objetivo = pd.concat([pd.DataFrame(edicoes), pd.DataFrame(criacoes)], ignore_index=True)
    print(f"\n[AREA] {len(edicoes)} edicoes, {len(criacoes)} criacoes")
    df_areas_objetivo.to_excel('objetivo/areas_objetivo.xlsx', index=False)


    ### CARGOS ###
    """
    id:         vazio para criar novo | id existente para editar (fechar cargo antigo com end_date)
    person:     codigo da pessoa
    start_date: data que comecou no cargo
    end_date:   data que terminou no cargo
    name:       nome do cargo
    level:      primeira palavra do cargo (ex: ANALISTA, ASSISTENTE, COORDENADOR)
    """
    df_cargos = dataframes['cargos']
    df_cargos_ativos = df_cargos[df_cargos['end_date'].isna()].copy()

    # normaliza nomes para comparacao (cargos full e caps sem acento, cliente tem acentos)
    df_cargos_ativos['name_norm'] = df_cargos_ativos['name'].apply(normalize_text)

    # apenas registros Atual para saber o cargo atual de cada person
    df_atual_cargo = df_ids[df_ids['Situação'].str.startswith('Atual')].copy()
    df_atual_cargo['cargo_norm'] = df_atual_cargo['Cargo'].str.upper().apply(normalize_text)
    df_atual_cargo['level_novo'] = df_atual_cargo['Cargo'].str.split().str[0].str.upper().apply(normalize_text)

    # LEFT JOIN para trazer o cargo ativo atual de cada person no sistema
    """
    SELECT *
    FROM df_atual_cargo
    LEFT JOIN cargos_ativos ON person
    """
    df_cargo_merge = df_atual_cargo.merge(
        df_cargos_ativos[['id', 'person', 'start_date', 'name', 'name_norm', 'level']].rename(columns={
            'id': 'cargo_id', 'start_date': 'cargo_start_date',
            'name': 'cargo_atual', 'name_norm': 'cargo_atual_norm', 'level': 'level_atual'
        }),
        on='person', how='left'
    )

    edicoes_cargo = []  # fecha cargo antigo preenchendo end_date no registro existente
    criacoes_cargo = []  # abre novo cargo

    for _, row in df_cargo_merge.iterrows():
        cargo_atual_norm = row['cargo_atual_norm']
        cargo_novo_norm  = row['cargo_norm']
        person           = row['person']
        data             = row['Data de Alteração']
        cargo_novo_name  = row['Cargo'].upper()
        level_novo       = row['level_novo']

        if pd.isna(cargo_atual_norm):
            # pessoa sem cargo no sistema: apenas cria
            criacoes_cargo.append({'id': '', 'person': person, 'start_date': data, 'end_date': '', 'name': cargo_novo_name, 'level': level_novo})
        elif cargo_atual_norm != cargo_novo_norm:
            # mudou de cargo: fecha antigo + abre novo
            edicoes_cargo.append({'id': row['cargo_id'], 'person': person, 'start_date': row['cargo_start_date'], 'end_date': data, 'name': row['cargo_atual'], 'level': row['level_atual']})
            criacoes_cargo.append({'id': '', 'person': person, 'start_date': data, 'end_date': '', 'name': cargo_novo_name, 'level': level_novo})
        # mesmo cargo: sem alteracao

    df_cargos_objetivo = pd.concat([pd.DataFrame(edicoes_cargo), pd.DataFrame(criacoes_cargo)], ignore_index=True)
    print(f"\n[CARGOS] {len(edicoes_cargo)} edicoes, {len(criacoes_cargo)} criacoes")
    df_cargos_objetivo.to_excel('objetivo/cargos_objetivo.xlsx', index=False)


if __name__ == "__main__":
    main()

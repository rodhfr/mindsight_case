import argparse
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import unicodedata


# ────────────────────────────────────────────────────────────

def carregar(file):
    df_main = pd.read_excel(file, sheet_name='Tablib Dataset')
    df_perf = pd.read_excel(file, sheet_name='performance')
    df_area = pd.read_excel(file, sheet_name='área')
    print(f'Tablib Dataset : {df_main.shape[0]:,} linhas x {df_main.shape[1]} colunas')
    print(f'performance    : {df_perf.shape[0]:,} linhas x {df_perf.shape[1]} colunas')
    print(f'área           : {df_area.shape[0]:,} linhas x {df_area.shape[1]} colunas')
    return df_main, df_perf, df_area


def limpar_tablib(df):
    df = df.copy()

    # 1.1 Remover coluna sem dados úteis
    print('Match — % nula:', df['Match'].isnull().mean() * 100, '%')
    df = df.drop(columns=['Match'])

    # 1.2 Remover colunas de URL
    url_cols = [c for c in df.columns if c.startswith('URL')]
    print('Colunas URL removidas:', url_cols)
    df = df.drop(columns=url_cols)

    # 1.3 Converter colunas de data/hora para datetime
    date_cols = [c for c in df.columns if c.startswith('Início') or c.startswith('Fim')]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], utc=True, errors='coerce')
    print('Colunas de data convertidas:', date_cols)

    # 1.4 Criar flags de testes realizados
    testes = {
        'fez_raciocinio'   : 'Raciocínio',
        'fez_cultura'      : 'Cultura pontuação',
        'fez_social'       : 'Social',
        'fez_motivacional' : 'Motivacional',
        'fez_perfil'       : 'perfil-Comunicação',
        'fez_atributos'    : 'atributo-Comunicação',
    }
    for flag, col in testes.items():
        df[flag] = df[col].notna().astype(int)
    print('Flags criadas:', list(testes.keys()))

    # 1.5 Padronizar Cultura classificação
    df['Cultura classificação'] = (
        df['Cultura classificação']
        .str.strip()
        .str.title()
        .map(_remover_acentos)
        .str.replace(' ', '-', regex=False)
    )
    print('Cultura classificação:', df['Cultura classificação'].value_counts(dropna=False).to_dict())

    # 1.6 Concatenar Nome + Sobrenome
    df.insert(0, 'Nome Completo',
              (df['Nome'].str.strip() + ' ' + df['Sobrenome'].str.strip()).str.title())
    df = df.drop(columns=['Nome', 'Sobrenome'])

    return df


def limpar_performance(df):
    df = df.copy()
    df.columns = (
        df.columns
            .str.replace('Performance ', 'perf_', regex=False)
            .str.replace('º/', '_', regex=False)
            .str.replace('º ', '_', regex=False)
    )
    print('Colunas performance:', df.columns.tolist())
    return df


def limpar_area(df):
    df = df.copy()
    df['Área'] = (
        df['Área']
        .str.strip()
        .str.title()
        .map(_remover_acentos)
    )
    print('Áreas:', df['Área'].value_counts().to_dict())

    dup = df[df['CPF'].duplicated(keep=False)]
    print(f'Linhas com CPF duplicado em área: {len(dup)}')
    df = df.drop_duplicates(subset='CPF', keep='last').reset_index(drop=True)
    return df


def juntar(df_main, df_area, df_perf):
    df = (
        df_main
        .merge(df_area, on='CPF', how='left')
        .merge(df_perf,  on='CPF', how='left')
    )
    print(f'\nDataset final: {df.shape[0]:,} linhas x {df.shape[1]} colunas')
    print(f'Candidatos com área mapeada: {df["Área"].notna().sum():,}')
    print('Cobertura de performance por semestre:')
    for col in [c for c in df.columns if c.startswith('perf_')]:
        n = df[col].notna().sum()
        print(f'  {col}: {n:,} ({n/len(df)*100:.1f}%)')
    return df


def resumo_qualidade(df):
    nulos = df.isnull().sum()
    pct   = (nulos / len(df) * 100).round(1)
    resumo = pd.DataFrame({'nulos': nulos, '% nulos': pct})
    print('\nColunas com nulos no dataset final:')
    print(resumo[resumo['nulos'] > 0].sort_values('% nulos', ascending=False).to_string())


def exportar(df, output):
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    for col in date_cols:
        df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)
    df.to_excel(output, index=False)
    print(f'\nDataset exportado para "{output}" — {df.shape[0]:,} linhas x {df.shape[1]} colunas')


# ────────────────────────────────────────────────────────────

def _remover_acentos(texto):
    if pd.isna(texto):
        return texto
    normalizado = unicodedata.normalize('NFKD', str(texto))
    return normalizado.encode('ascii', 'ignore').decode('ascii')


# ────────────────────────────────────────────────────────────

def pipeline(input_path, output_path):
    df_main, df_perf, df_area = carregar(input_path)
    df_main = limpar_tablib(df_main)
    df_perf = limpar_performance(df_perf)
    df_area = limpar_area(df_area)
    df      = juntar(df_main, df_area, df_perf)
    resumo_qualidade(df)
    exportar(df, output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pipeline de limpeza de dados')
    parser.add_argument('input',  help='Arquivo Excel de entrada  (ex: data.xlsx)')
    parser.add_argument('output', nargs='?', default=None,
                        help='Arquivo Excel de saída (padrão: <input>_limpo.xlsx)')
    args = parser.parse_args()

    if args.output is None:
        stem, ext = args.input.rsplit('.', 1)
        args.output = f'{stem}_limpo.{ext}'

    df_main, df_perf, df_area = carregar(args.input)
    df_main = limpar_tablib(df_main)
    df_perf = limpar_performance(df_perf)
    df_area = limpar_area(df_area)
    df      = juntar(df_main, df_area, df_perf)
    resumo_qualidade(df)
    exportar(df, args.output)

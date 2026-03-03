import streamlit as st
import pandas as pd
import re
import unicodedata
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Validador e Dashboard", layout="wide")
st.title("📊 Validação e Dashboard de Performance")

FILE = 'Dados - Atividade 1.xlsx'  # caminho fixo do Excel

# ────────────────────────────────────────────────────────────
# Funções utilitárias

def _remover_acentos(texto):
    if pd.isna(texto): return texto
    normalizado = unicodedata.normalize('NFKD', str(texto))
    return normalizado.encode('ascii','ignore').decode('ascii')

def _validar_workbook(file):
    """Valida abas e colunas obrigatórias"""
    errors = 0
    warnings_count = 0
    sections = []

    # Abas esperadas
    SHEETS = ['Tablib Dataset', 'performance', 'área']
    REQUIRED_MAIN = [
        'Nome','Sobrenome','E-mail','CPF',
        'Raciocínio','Social','Motivacional',
        'Cultura pontuação','Cultura classificação',
        'Potencial Bruto','Match',
        'perfil-Comunicação','atributo-Comunicação',
    ]
    OPTIONAL_GROUPS_MAIN = [
        {'label':'Colunas URL','prefix':'URL','minCount':1},
        {'label':'Colunas Início/Fim','prefix':'Início','minCount':1},
    ]
    REQUIRED_PERF = ['CPF']
    REQUIRED_AREA = ['CPF','Área']

    # Ler workbook
    try:
        xls = pd.ExcelFile(file)
    except Exception as e:
        return {'sections':[], 'errors':1, 'warnings':0, 'fatal':str(e)}

    # 1. Abas
    sheet_checks = []
    for sheet in SHEETS:
        exists = sheet in xls.sheet_names
        sheet_checks.append({'status':'ok' if exists else 'err','text':f'Aba "{sheet}"',
                             'detail':None if exists else 'Aba ausente'})
        if not exists: errors+=1
    sections.append({'title':'1. Abas do arquivo','checks':sheet_checks})

    has_all = all(s in xls.sheet_names for s in SHEETS)

    # 2. Tablib Dataset
    main_checks=[]
    if not has_all:
        main_checks.append({'status':'info','text':'Validação ignorada — aba ausente','detail':None})
    else:
        df_main = pd.read_excel(xls, sheet_name='Tablib Dataset', nrows=0)
        cols = df_main.columns.tolist()
        for col in REQUIRED_MAIN:
            found = col in cols
            main_checks.append({'status':'ok' if found else 'err','text':f'Coluna obrigatória: "{col}"',
                                'detail':None if found else 'Coluna ausente'})
            if not found: errors+=1
        for g in OPTIONAL_GROUPS_MAIN:
            found_cols = [c for c in cols if c.startswith(g['prefix'])]
            ok = len(found_cols)>=g['minCount']
            main_checks.append({'status':'ok' if ok else 'warn','text':f"{g['label']} ({len(found_cols)} encontrada(s))",
                                'detail':None if ok else 'Esperado ao menos uma coluna com esse prefixo'})
            if not ok: warnings_count+=1
    sections.append({'title':'2. Colunas — Tablib Dataset','checks':main_checks})

    # 3. Performance
    perf_checks=[]
    if not has_all:
        perf_checks.append({'status':'info','text':'Validação ignorada — aba ausente','detail':None})
    else:
        df_perf = pd.read_excel(xls, sheet_name='performance', nrows=0)
        cols = df_perf.columns.tolist()
        for col in REQUIRED_PERF:
            found = col in cols
            perf_checks.append({'status':'ok' if found else 'err','text':f'Coluna obrigatória: "{col}"',
                                'detail':None if found else 'Coluna ausente'})
            if not found: errors+=1
        perf_cols = [c for c in cols if re.match(r'^performance', c, re.I)]
        ok = len(perf_cols)>0
        perf_checks.append({'status':'ok' if ok else 'err','text':f'Colunas de performance ({len(perf_cols)})',
                            'detail': None if ok else 'Nenhuma coluna começando com "Performance"'})
        if not ok: errors+=1
    sections.append({'title':'3. Colunas — performance','checks':perf_checks})

    # 4. Área
    area_checks=[]
    if not has_all:
        area_checks.append({'status':'info','text':'Validação ignorada — aba ausente','detail':None})
    else:
        df_area = pd.read_excel(xls, sheet_name='área', nrows=0)
        cols = df_area.columns.tolist()
        for col in REQUIRED_AREA:
            found = col in cols
            area_checks.append({'status':'ok' if found else 'err','text':f'Coluna obrigatória: "{col}"',
                                'detail':None if found else 'Coluna ausente'})
            if not found: errors+=1
    sections.append({'title':'4. Colunas — área','checks':area_checks})

    # 5. CPF em todas as abas
    join_checks=[]
    if has_all:
        for sheet in SHEETS:
            cols = pd.read_excel(xls, sheet_name=sheet, nrows=0).columns.tolist()
            found = 'CPF' in cols
            join_checks.append({'status':'ok' if found else 'err','text':f'CPF em "{sheet}"',
                                'detail':None if found else 'Chave ausente'})
            if not found: errors+=1
    sections.append({'title':'5. Chave de junção (CPF)','checks':join_checks})

    return {'sections':sections, 'errors':errors, 'warnings':warnings_count, 'fatal':None}


# ────────────────────────────────────────────────────────────
# Upload de arquivo e validação
import os

demo_mode = 'mindsight_c1' in st.query_params
if demo_mode:
    if os.path.exists(FILE):
        uploaded_file = FILE
        st.info(f"Modo demonstração — carregando **{FILE}** automaticamente. ([voltar ao upload normal](?))")
    else:
        st.error(f"Arquivo de demonstração não encontrado: `{FILE}`")
        uploaded_file = None
else:
    uploaded_file = st.file_uploader("📥 Selecione o arquivo Excel", type=['xlsx','xls'])
    st.caption("Acesse [?mindsight_c1](?mindsight_c1) para carregar o arquivo de demonstração automaticamente.")

if uploaded_file is not None:
    result = _validar_workbook(uploaded_file)
    if result.get('fatal'):
        st.error(f"Erro ao abrir o arquivo: {result['fatal']}")
    else:
        # Mostrar resumo
        if result['errors']==0 and result['warnings']==0:
            st.success("Arquivo compatível — pronto para a limpeza.")
        elif result['errors']==0:
            st.warning(f"Compatível com {result['warnings']} aviso(s).")
        else:
            st.error(f"Incompatível — {result['errors']} erro(s) encontrado(s).")
        
        # Mostrar detalhes
        expanded_default = result['errors'] > 0 or result['warnings'] > 0
        with st.expander("Ver detalhes da validação", expanded=expanded_default):
            for sec in result['sections']:
                st.markdown(f"**{sec['title']}**")
                for check in sec['checks']:
                    status = check['status']
                    text = check['text']
                    detail = check.get('detail')
                    if status=='ok':
                        st.markdown(f"- ✅ {text}")
                    elif status=='warn':
                        st.markdown(f"- ⚠️ {text} ({detail})")
                    elif status=='err':
                        st.markdown(f"- ❌ {text} ({detail})")
                    else:
                        st.markdown(f"- ℹ️ {text}")

        # Se não houver erro, permitir processar e mostrar dashboard
        if result['errors']==0:
            st.markdown("---")
            st.subheader("📊 Dashboard de Performance")
            
            # Processar o arquivo usando o pipeline de limpeza
            def pipeline_streamlit(file):
                df_main = pd.read_excel(file, sheet_name='Tablib Dataset')
                df_perf = pd.read_excel(file, sheet_name='performance')
                df_area = pd.read_excel(file, sheet_name='área')
                # limpeza
                df_main = df_main.copy()
                df_main = df_main.drop(columns=['Match'], errors='ignore')
                df_main.insert(0, 'Nome Completo',
                               (df_main['Nome'].str.strip() + ' ' + df_main['Sobrenome'].str.strip()).str.title())
                df_main = df_main.drop(columns=['Nome','Sobrenome'], errors='ignore')
                df_perf.columns = (
                    df_perf.columns
                    .str.replace('Performance ','perf_',regex=False)
                    .str.replace('º/','_',regex=False)
                    .str.replace('º ','_',regex=False)
                )
                df_area['Área'] = df_area['Área'].str.strip().str.title().map(_remover_acentos)
                df = df_main.merge(df_area, on='CPF', how='left').merge(df_perf, on='CPF', how='left')
                return df
            
            with st.spinner("Processando arquivo..."):
                df = pipeline_streamlit(uploaded_file)

            total_func = len(df)
            cols_perf = [c for c in df.columns if c.startswith('perf_')]
            pct_com_dados = df[cols_perf].notna().mean().mean()*100
            st.metric("Total de Funcionários", total_func)
            st.metric("Cobertura média de performance", f"{pct_com_dados:.1f}%")

            # Gráfico de cobertura
            if cols_perf:
                ordem_cronologica = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
                labels_dict = {s:f"{s.split('_')[2]}-{s.split('_')[1]}º" for s in ordem_cronologica}
                cobertura = pd.DataFrame({
                    'semestre':ordem_cronologica,
                    'label':[labels_dict[s] for s in ordem_cronologica],
                    'pct':[df[s].notna().mean()*100 for s in ordem_cronologica],
                })
                fig = px.bar(cobertura, x='label', y='pct', text=cobertura['pct'].map(lambda v:f"{v:.1f}%"),
                             title="Cobertura de Performance por Semestre", color='pct', color_continuous_scale="Blues")
                st.plotly_chart(fig, use_container_width=True)

            # ── Tabs com as demais análises ──────────────────────────────
            tab_scores, tab_area, tab_9box, tab_atr, tab_assess, tab_km, tab_evol, tab_rec = st.tabs([
                "Distribuição de Scores",
                "Performance por Área",
                "Potencial & 9-Box",
                "Atributos",
                "Assessments",
                "Clustering",
                "Evolução Individual",
                "Recomendações",
            ])

            # ── Tab 1: Distribuição de scores ────────────────────────────
            with tab_scores:
                relacao_lst = []
                for col in cols_perf:
                    vc = df[col].value_counts().sort_index()
                    for score, cnt in vc.items():
                        relacao_lst.append({'semestre': col, 'score': str(int(score)), 'qnt_func': int(cnt)})
                if relacao_lst:
                    relacao = pd.DataFrame(relacao_lst)
                    ordem_cron_sc = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
                    relacao['label'] = relacao['semestre'].map(lambda s: f"{s.split('_')[2]}-{s.split('_')[1]}º")
                    labels_cron = [f"{s.split('_')[2]}-{s.split('_')[1]}º" for s in ordem_cron_sc]
                    fig_sc = px.bar(relacao, x='label', y='qnt_func', color='score', barmode='group',
                                    text='qnt_func', category_orders={'label': labels_cron},
                                    title='Distribuição de Presença de Scores por Semestre',
                                    labels={'label':'Semestre','qnt_func':'Nº de Funcionários','score':'Score'})
                    st.plotly_chart(fig_sc, use_container_width=True)

                    ordem_cron = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
                    lbl_cron = {s: f"{s.split('_')[2]}-{s.split('_')[1]}º" for s in ordem_cron}
                    totais_sc = relacao.groupby('semestre')['qnt_func'].sum()
                    rel_pct = relacao.copy()
                    rel_pct['pct'] = rel_pct.apply(lambda r: r['qnt_func'] / totais_sc[r['semestre']] * 100, axis=1)
                    rel_pct['label'] = rel_pct['semestre'].map(lbl_cron)
                    fig_trend = px.line(rel_pct, x='label', y='pct', color='score', markers=True,
                                        category_orders={'label': [lbl_cron[s] for s in ordem_cron]},
                                        title='Distribuição Proporcional de Scores por Semestre',
                                        labels={'label':'Semestre','pct':'% dos avaliados','score':'Score'})
                    fig_trend.update_layout(yaxis_range=[0, 80])
                    st.plotly_chart(fig_trend, use_container_width=True)

            # ── Tab 2: Performance por Área ──────────────────────────────
            with tab_area:
                if 'Área' not in df.columns:
                    st.info("Coluna 'Área' não encontrada.")
                else:
                    ordem_cron2 = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
                    lbl2 = {s: f"{s.split('_')[2]}-{s.split('_')[1]}º" for s in ordem_cron2}

                    rel_area_lst = []
                    for col in cols_perf:
                        for area, grp in df.groupby('Área'):
                            rel_area_lst.append({'semestre': col, 'Área': area, 'media_perf': grp[col].mean()})
                    rel_area = pd.DataFrame(rel_area_lst)
                    rel_area['label'] = rel_area['semestre'].map(lbl2)
                    labels_cron2 = [lbl2[s] for s in sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))]
                    fig_area = px.bar(rel_area, x='label', y='media_perf', color='Área', barmode='group',
                                      category_orders={'label': labels_cron2},
                                      title='Performance Média por Área e Semestre',
                                      labels={'label':'Semestre','media_perf':'Score Médio'})
                    fig_area.update_yaxes(range=[1, 3])
                    st.plotly_chart(fig_area, use_container_width=True)

                    df_longo = df.melt(id_vars=['Área'], value_vars=cols_perf, var_name='semestre', value_name='score')
                    df_longo['score'] = pd.to_numeric(df_longo['score'], errors='coerce')
                    rel_media = df_longo.groupby(['semestre','Área'])['score'].mean().reset_index()
                    rel_media['label'] = rel_media['semestre'].map(lbl2)
                    _ordem_idx = {s: i for i, s in enumerate(ordem_cron2)}
                    rel_media = rel_media.sort_values('semestre', key=lambda col: col.map(_ordem_idx))
                    fig_med = px.line(rel_media, x='label', y='score', color='Área', markers=True,
                                      facet_col='Área', facet_col_wrap=3,
                                      category_orders={'label': [lbl2[s] for s in ordem_cron2]},
                                      title='Tendência de Performance por Área',
                                      labels={'label':'Semestre','score':'Score Médio'})
                    fig_med.update_yaxes(range=[1, 3])
                    fig_med.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                    st.plotly_chart(fig_med, use_container_width=True)

            # ── Tab 3: Potencial & 9-Box ─────────────────────────────────
            with tab_9box:
                if 'Potencial Bruto' not in df.columns:
                    st.info("Coluna 'Potencial Bruto' não encontrada.")
                else:
                    perf_m = df[cols_perf].mean(axis=1)
                    validos = pd.DataFrame({
                        'Potencial Bruto': df['Potencial Bruto'],
                        'perf_media': perf_m,
                        'Área': df['Área'] if 'Área' in df.columns else 'N/A',
                    }).dropna()
                    if len(validos) > 1:
                        correlacao = validos['Potencial Bruto'].corr(validos['perf_media'])
                        m_reg, b_reg = np.polyfit(validos['Potencial Bruto'], validos['perf_media'], 1)
                        x_line = np.linspace(validos['Potencial Bruto'].min(), validos['Potencial Bruto'].max(), 100)
                        fig_pot = px.scatter(validos, x='Potencial Bruto', y='perf_media', color='Área',
                                             opacity=0.5,
                                             title=f'Potencial Bruto vs Performance Média  (r = {correlacao:.2f})',
                                             labels={'perf_media':'Média de Performance'})
                        fig_pot.add_trace(go.Scatter(x=x_line, y=m_reg*x_line+b_reg, mode='lines',
                                                     line=dict(color='black', width=2, dash='dash'),
                                                     name='Regressão', showlegend=False))
                        st.plotly_chart(fig_pot, use_container_width=True)

                    # Matriz 9-Box
                    n_aval = df[cols_perf].notna().sum(axis=1)
                    dados_9 = pd.DataFrame({
                        'Potencial Bruto': df['Potencial Bruto'],
                        'perf_media': df[cols_perf].mean(axis=1),
                        'n_avaliacoes': n_aval,
                        'Área': df['Área'] if 'Área' in df.columns else 'N/A',
                    })
                    dados_9 = dados_9[(dados_9['n_avaliacoes'] >= 2) & (dados_9['Potencial Bruto'].notna())]
                    if len(dados_9) > 0:
                        dados_9['perf_cat'] = pd.cut(dados_9['perf_media'], bins=[0,1.5,2.5,3.01],
                                                      labels=['Baixa','Média','Alta'], include_lowest=True)
                        q33 = dados_9['Potencial Bruto'].quantile(0.33)
                        q66 = dados_9['Potencial Bruto'].quantile(0.66)
                        dados_9['pot_cat'] = pd.cut(dados_9['Potencial Bruto'], bins=[0,q33,q66,101],
                                                     labels=['Baixo','Médio','Alto'], include_lowest=True)
                        quadrantes_nomes = {
                            ('Alto','Alta'):'Estrela',       ('Alto','Média'):'Alto\nPotencial', ('Alto','Baixa'):'Enigma',
                            ('Médio','Alta'):'Forte\nDesempenho', ('Médio','Média'):'Core',      ('Médio','Baixa'):'Em\nDesenvolvimento',
                            ('Baixo','Alta'):'Sólido',       ('Baixo','Média'):'Eficiente',     ('Baixo','Baixa'):'Em Risco',
                        }
                        rank = {'Baixo':1,'Médio':2,'Alto':3,'Baixa':1,'Média':2,'Alta':3}
                        rank_v = {(p,f): rank[p]*rank[f] for p in ['Alto','Médio','Baixo'] for f in ['Alta','Média','Baixa']}
                        matriz_n = (dados_9.groupby(['pot_cat','perf_cat'], observed=True)
                                    .size().unstack(fill_value=0)[['Baixa','Média','Alta']].loc[['Alto','Médio','Baixo']])
                        total_9 = int(matriz_n.values.sum())

                        import matplotlib.pyplot as plt
                        import matplotlib.colors as mcolors
                        import seaborn as sns
                        cmap9 = sns.diverging_palette(10, 140, s=60, l=45, n=256, as_cmap=True)
                        norm9 = mcolors.Normalize(vmin=1, vmax=9)
                        fig9, ax9 = plt.subplots(figsize=(10, 7))
                        for i, pot in enumerate(['Alto','Médio','Baixo']):
                            for j, perf in enumerate(['Baixa','Média','Alta']):
                                rgba = cmap9(norm9(rank_v[(pot, perf)]))
                                lum = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
                                fg = 'white' if lum < 0.55 else '#333333'
                                ax9.add_patch(plt.Rectangle([j, 2-i], 1, 1, color=rgba, ec='white', lw=3))
                                n_c = int(matriz_n.loc[pot, perf])
                                pct_c = n_c / total_9 * 100
                                ax9.text(j+0.5, 2-i+0.65, quadrantes_nomes[(pot,perf)],
                                         ha='center', va='center', fontsize=10, fontweight='bold', color=fg)
                                ax9.text(j+0.5, 2-i+0.28, f'n={n_c}  ({pct_c:.1f}%)',
                                         ha='center', va='center', fontsize=9, color=fg)
                        ax9.set_xlim(0,3); ax9.set_ylim(0,3)
                        ax9.set_xticks([0.5,1.5,2.5]); ax9.set_xticklabels(['Baixa','Média','Alta'], fontsize=11)
                        ax9.set_yticks([0.5,1.5,2.5]); ax9.set_yticklabels(['Baixo','Médio','Alto'], fontsize=11)
                        ax9.set_xlabel('Performance Média', fontsize=12, labelpad=12)
                        ax9.set_ylabel('Potencial Bruto', fontsize=12, labelpad=12)
                        ax9.set_title(f'Matriz 9-Box — Potencial × Performance  (n={total_9})', fontsize=14, pad=15)
                        ax9.tick_params(length=0)
                        sns.despine(ax=ax9, left=True, bottom=True)
                        plt.tight_layout()
                        st.pyplot(fig9)
                        plt.close(fig9)

                        # Tabela de funcionários por quadrante
                        st.subheader("Funcionários por Quadrante")
                        ql_flat = {(p,f): v.replace('\n',' ') for (p,f),v in quadrantes_nomes.items()}
                        df_tab = pd.DataFrame({
                            'Nome Completo': df.get('Nome Completo', df['CPF']),
                            'CPF': df['CPF'],
                            'Área': df['Área'] if 'Área' in df.columns else 'N/A',
                            'Potencial Bruto': df['Potencial Bruto'],
                            'perf_media': df[cols_perf].mean(axis=1).round(2),
                            'n_avaliacoes': df[cols_perf].notna().sum(axis=1),
                        })
                        df_tab = df_tab[(df_tab['n_avaliacoes'] >= 2) & (df_tab['Potencial Bruto'].notna())].copy()
                        df_tab['perf_cat'] = pd.cut(df_tab['perf_media'], bins=[0,1.5,2.5,3.01],
                                                    labels=['Baixa','Média','Alta'], include_lowest=True)
                        df_tab['pot_cat'] = pd.cut(df_tab['Potencial Bruto'], bins=[0,q33,q66,101],
                                                   labels=['Baixo','Médio','Alto'], include_lowest=True)
                        df_tab['quadrante'] = df_tab.apply(lambda r: ql_flat.get((str(r['pot_cat']), str(r['perf_cat'])), 'N/A'), axis=1)
                        ordem_quad = ['Estrela','Forte Desempenho','Alto Potencial','Sólido','Core',
                                      'Em Desenvolvimento','Eficiente','Enigma','Em Risco']
                        df_tab['quadrante'] = pd.Categorical(df_tab['quadrante'], categories=ordem_quad, ordered=True)
                        df_todos = (df_tab[['Nome Completo','CPF','Área','Potencial Bruto','perf_media','quadrante']]
                                    .sort_values(['quadrante','perf_media'], ascending=[True,False])
                                    .reset_index(drop=True))
                        quad_sel = st.selectbox('Filtrar por quadrante', ['Todos'] + ordem_quad)
                        df_show = df_todos if quad_sel == 'Todos' else df_todos[df_todos['quadrante'] == quad_sel]
                        st.dataframe(df_show, use_container_width=True)

            # ── Tab 4: Atributos ─────────────────────────────────────────
            with tab_atr:
                cols_atr = [c for c in df.columns if c.startswith('atributo-')]
                if not cols_atr:
                    st.info("Nenhuma coluna 'atributo-' encontrada.")
                else:
                    nomes_atr = [c.replace('atributo-','') for c in cols_atr]

                    # Radar: perfis por quadrante 9-Box
                    if 'Potencial Bruto' in df.columns:
                        n_av2 = df[cols_perf].notna().sum(axis=1)
                        pm2 = df[cols_perf].mean(axis=1)
                        df_rad = df[cols_atr + ['Potencial Bruto']].copy()
                        df_rad['perf_media'] = pm2
                        df_rad['n_avaliacoes'] = n_av2
                        df_rad = df_rad[(df_rad['n_avaliacoes'] >= 2) &
                                        (df_rad['Potencial Bruto'].notna()) &
                                        (df_rad[cols_atr].notna().all(axis=1))].copy()
                        if len(df_rad) > 0:
                            df_rad['perf_cat'] = pd.cut(df_rad['perf_media'], bins=[0,1.5,2.5,3.01],
                                                        labels=['Baixa','Média','Alta'], include_lowest=True)
                            q33r = df_rad['Potencial Bruto'].quantile(0.33)
                            q66r = df_rad['Potencial Bruto'].quantile(0.66)
                            df_rad['pot_cat'] = pd.cut(df_rad['Potencial Bruto'], bins=[0,q33r,q66r,101],
                                                       labels=['Baixo','Médio','Alto'], include_lowest=True)
                            ql_r = {('Alto','Alta'):'Estrela',('Alto','Média'):'Alto Potencial',('Alto','Baixa'):'Enigma',
                                    ('Médio','Alta'):'Forte Desempenho',('Médio','Média'):'Core',('Médio','Baixa'):'Em Desenvolvimento',
                                    ('Baixo','Alta'):'Sólido',('Baixo','Média'):'Eficiente',('Baixo','Baixa'):'Em Risco'}
                            df_rad['quadrante'] = df_rad.apply(lambda r: ql_r.get((str(r['pot_cat']),str(r['perf_cat'])),'N/A'), axis=1)
                            med_atr = df_rad.groupby('quadrante')[cols_atr].mean()
                            med_atr.columns = nomes_atr

                            fig_radar = make_subplots(rows=1, cols=2,
                                                      specs=[[{'type':'polar'},{'type':'polar'}]],
                                                      subplot_titles=['Estrela vs Em Risco','Enigma vs Core'])
                            pares = [('Estrela','Em Risco'), ('Enigma','Core')]
                            cores_pares = [('#2ecc71','#e74c3c'), ('#e67e22','#3498db')]
                            for col_idx, (par, cores) in enumerate(zip(pares, cores_pares), 1):
                                for q, cor in zip(par, cores):
                                    if q not in med_atr.index: continue
                                    vals = med_atr.loc[q].tolist()
                                    n_q = int((df_rad['quadrante'] == q).sum())
                                    fig_radar.add_trace(go.Scatterpolar(
                                        r=vals+[vals[0]], theta=nomes_atr+[nomes_atr[0]],
                                        fill='toself', fillcolor=cor, opacity=0.2,
                                        line=dict(color=cor, width=2), name=f'{q} (n={n_q})'
                                    ), row=1, col=col_idx)
                            fig_radar.update_polars(radialaxis=dict(range=[0,100], tickvals=[20,40,60,80]))
                            fig_radar.update_layout(height=500, title_text='Perfil Médio de Atributos por Quadrante 9-Box')
                            st.plotly_chart(fig_radar, use_container_width=True)

                    # Correlação atributos × performance por área
                    if 'Área' in df.columns:
                        df_corr = df[cols_atr + ['Área']].copy()
                        df_corr['perf_media'] = df[cols_perf].mean(axis=1)
                        df_corr = df_corr.dropna(subset=['perf_media'] + cols_atr)
                        corr_area = (df_corr.groupby('Área')
                                     .apply(lambda g: g[cols_atr].corrwith(g['perf_media']))
                                     .rename(columns=lambda c: c.replace('atributo-','')))
                        areas_list = corr_area.index.tolist()
                        fig_corr = make_subplots(rows=1, cols=len(areas_list), subplot_titles=areas_list)
                        for i, area in enumerate(areas_list, 1):
                            v = corr_area.loc[area].sort_values()
                            fig_corr.add_trace(go.Bar(
                                x=v.values, y=v.index, orientation='h',
                                marker_color=['#e74c3c' if x < 0 else '#2ecc71' for x in v],
                                showlegend=False, name=area
                            ), row=1, col=i)
                            fig_corr.update_xaxes(range=[-0.5,0.5], row=1, col=i)
                        fig_corr.update_layout(height=420, title_text='Correlação Atributos × Performance por Área')
                        st.plotly_chart(fig_corr, use_container_width=True)

            # ── Tab 5: Assessments ───────────────────────────────────────
            with tab_assess:
                assessments_cfg = [
                    ('Raciocínio',   'Raciocínio',       'Início - Raciocínio',   'Fim - Raciocínio',   0.90),
                    ('Social',       'Social',           'Início - Social',       'Fim - Social',       0.95),
                    ('Motivacional', 'Motivacional',     'Início - Motivacional', 'Fim - Motivacional', 0.95),
                    ('Cultura',      'Cultura pontuação','Início - Cultura',      'Fim - Cultura',      0.95),
                ]
                valid_ass = [(n, sc, ini, fim, p) for n, sc, ini, fim, p in assessments_cfg
                             if sc in df.columns and ini in df.columns and fim in df.columns]
                if not valid_ass:
                    st.info("Colunas de assessment (Início/Fim) não encontradas.")
                else:
                    n_ass = len(valid_ass)
                    rows_ass = (n_ass + 1) // 2
                    fig_ass = make_subplots(rows=rows_ass, cols=2,
                                           subplot_titles=[a[0] for a in valid_ass])
                    for idx, (nome, score_col, ini_col, fim_col, pct_corte) in enumerate(valid_ass):
                        r_a = idx // 2 + 1
                        c_a = idx % 2 + 1
                        dur = (pd.to_datetime(df[fim_col], errors='coerce') -
                               pd.to_datetime(df[ini_col], errors='coerce')).dt.total_seconds() / 60
                        dados_a = pd.DataFrame({'dur': dur, 'score': df[score_col]}).dropna()
                        dados_a = dados_a[dados_a['dur'] > 0]
                        corte_a = dados_a['dur'].quantile(pct_corte)
                        dados_a = dados_a[dados_a['dur'] <= corte_a]
                        if len(dados_a) > 1:
                            r_val = dados_a['dur'].corr(dados_a['score'])
                            m_a, b_a = np.polyfit(dados_a['dur'], dados_a['score'], 1)
                            x_a = np.linspace(dados_a['dur'].min(), dados_a['dur'].max(), 100)
                            fig_ass.add_trace(go.Scatter(
                                x=dados_a['dur'], y=dados_a['score'], mode='markers',
                                marker=dict(opacity=0.35, size=5, color='#3498db'),
                                name=nome, showlegend=False
                            ), row=r_a, col=c_a)
                            fig_ass.add_trace(go.Scatter(
                                x=x_a, y=m_a*x_a+b_a, mode='lines',
                                line=dict(color='black', dash='dash', width=1.5), showlegend=False
                            ), row=r_a, col=c_a)
                            fig_ass.add_annotation(
                                text=f'r = {r_val:.2f}  n = {len(dados_a)}',
                                xref='paper', yref='paper',
                                x=(c_a - 0.5) / 2,
                                y=1.0 - (r_a - 1) / rows_ass - 0.05,
                                showarrow=False, font=dict(size=11),
                                bgcolor='white', bordercolor='gray'
                            )
                    fig_ass.update_layout(height=420 * rows_ass,
                                          title_text='Tempo de Conclusão vs Score por Assessment')
                    st.plotly_chart(fig_ass, use_container_width=True)

                    # Score do assessment vs performance no trabalho
                    st.markdown("---")
                    perf_m_ass = df[cols_perf].mean(axis=1)
                    ass_score_map = {n: sc for n, sc, ini, fim, p in assessments_cfg if sc in df.columns}
                    df_sp = pd.DataFrame({nome: df[col] for nome, col in ass_score_map.items()})
                    df_sp['perf_media'] = perf_m_ass
                    df_sp = df_sp.dropna()
                    if len(df_sp) > 1:
                        corrs_sp = {nome: df_sp[nome].corr(df_sp['perf_media']) for nome in ass_score_map}
                        fig_csp = px.bar(
                            x=list(corrs_sp.keys()), y=list(corrs_sp.values()),
                            text=[f'{v:.2f}' for v in corrs_sp.values()],
                            color=list(corrs_sp.values()), color_continuous_scale='RdYlGn',
                            range_color=[-0.5, 0.5],
                            title=f'Correlação: Score do Assessment vs Performance no Trabalho  (n={len(df_sp)})',
                            labels={'x': 'Assessment', 'y': 'r de Pearson'},
                        )
                        fig_csp.update_layout(yaxis_range=[-0.5, 0.5], coloraxis_showscale=False)
                        fig_csp.add_hline(y=0, line_dash='dash', line_color='gray')
                        st.plotly_chart(fig_csp, use_container_width=True)

                # Fit Cultural
                if 'Cultura classificação' in df.columns:
                    st.markdown("---")
                    st.markdown("#### Fit Cultural — distribuição e impacto na performance")
                    ordem_cult = ['Baixo','Medio-Baixo','Medio','Medio-Alto','Alto','Muito-Alto']
                    df_cult = df[['Cultura classificação']].copy()
                    df_cult['perf_media'] = df[cols_perf].mean(axis=1)
                    df_cult = df_cult.dropna(subset=['Cultura classificação'])
                    df_cult['Cultura classificação'] = pd.Categorical(
                        df_cult['Cultura classificação'], categories=ordem_cult, ordered=True)
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        dist_cult = df_cult['Cultura classificação'].value_counts().sort_index()
                        fig_cd = px.bar(x=dist_cult.index.astype(str), y=dist_cult.values,
                                        title='Distribuição de Fit Cultural',
                                        labels={'x':'Classificação','y':'Funcionários'})
                        st.plotly_chart(fig_cd, use_container_width=True)
                    with col_c2:
                        df_cp = df_cult.dropna(subset=['perf_media'])
                        if len(df_cp) > 5:
                            fig_cb = px.box(df_cp, x='Cultura classificação', y='perf_media',
                                            category_orders={'Cultura classificação': ordem_cult},
                                            title='Performance por Fit Cultural',
                                            labels={'perf_media':'Média de Performance'})
                            fig_cb.update_yaxes(range=[0.5, 3.5])
                            st.plotly_chart(fig_cb, use_container_width=True)
                    # Média de performance por nível cultural (tabela)
                    if len(df_cult.dropna(subset=['perf_media'])) > 5:
                        tbl_cult = (df_cult.dropna(subset=['perf_media'])
                                    .groupby('Cultura classificação', observed=True)['perf_media']
                                    .agg(['mean','count']).rename(columns={'mean':'Perf Média','count':'n'})
                                    .round(2).reset_index())
                        st.dataframe(tbl_cult, use_container_width=True, hide_index=True)

            # ── Tab 6: K-Means Clustering ────────────────────────────────
            with tab_km:
                cols_atr_km = [c for c in df.columns if c.startswith('atributo-')]
                if not cols_atr_km:
                    st.info("Nenhuma coluna 'atributo-' encontrada para clustering.")
                else:
                    try:
                        from sklearn.preprocessing import StandardScaler
                        from sklearn.cluster import KMeans
                        from sklearn.metrics import silhouette_score
                    except ImportError:
                        st.error("scikit-learn não instalado. Execute: pip install scikit-learn")
                        cols_atr_km = []

                if cols_atr_km:
                    nomes_km = [c.replace('atributo-','') for c in cols_atr_km]
                    df_cl = df[cols_atr_km + (['Área'] if 'Área' in df.columns else [])].copy()
                    df_cl['perf_media'] = df[cols_perf].mean(axis=1)
                    df_cl = df_cl.dropna(subset=cols_atr_km)

                    if len(df_cl) >= 8:
                        X_km = df_cl[cols_atr_km].values
                        Xs_km = StandardScaler().fit_transform(X_km)

                        ks = range(2, 9)
                        inertias, silhouettes = [], []
                        for k in ks:
                            km_k = KMeans(n_clusters=k, random_state=42, n_init=10)
                            labs = km_k.fit_predict(Xs_km)
                            inertias.append(km_k.inertia_)
                            silhouettes.append(silhouette_score(Xs_km, labs))

                        fig_elbow = make_subplots(rows=1, cols=2,
                                                  subplot_titles=['Método do Cotovelo','Silhouette por k'])
                        fig_elbow.add_trace(go.Scatter(x=list(ks), y=inertias, mode='lines+markers',
                                                       line=dict(color='#3498db'), name='Inércia'), row=1, col=1)
                        fig_elbow.add_trace(go.Scatter(x=[4,4], y=[min(inertias), max(inertias)],
                                                       mode='lines', line=dict(color='red', dash='dash'),
                                                       name='k=4', showlegend=False), row=1, col=1)
                        fig_elbow.add_trace(go.Scatter(x=list(ks), y=silhouettes, mode='lines+markers',
                                                       line=dict(color='#2ecc71'), name='Silhouette'), row=1, col=2)
                        fig_elbow.add_trace(go.Scatter(x=[4,4], y=[min(silhouettes), max(silhouettes)],
                                                       mode='lines', line=dict(color='red', dash='dash'),
                                                       showlegend=False), row=1, col=2)
                        fig_elbow.update_layout(height=350, showlegend=False,
                                                title_text='Escolha do número de clusters')
                        st.plotly_chart(fig_elbow, use_container_width=True)

                        K = 4
                        km4 = KMeans(n_clusters=K, random_state=42, n_init=10)
                        df_cl['cluster'] = km4.fit_predict(Xs_km)
                        nomes_cl = [f'Perfil {i+1}' for i in range(K)]
                        df_cl['perfil'] = df_cl['cluster'].map(dict(enumerate(nomes_cl)))
                        centros = df_cl.groupby('perfil')[cols_atr_km].mean()
                        centros.columns = nomes_km
                        cores_cl = ['#3498db','#2ecc71','#e74c3c','#e67e22']

                        fig_rad_km = make_subplots(rows=2, cols=2,
                                                   specs=[[{'type':'polar'},{'type':'polar'}],
                                                          [{'type':'polar'},{'type':'polar'}]],
                                                   subplot_titles=nomes_cl)
                        positions = [(1,1),(1,2),(2,1),(2,2)]
                        for idx, (perfil, cor) in enumerate(zip(nomes_cl, cores_cl)):
                            rp, cp = positions[idx]
                            vals_km = centros.loc[perfil].tolist()
                            n_km = int((df_cl['perfil'] == perfil).sum())
                            fig_rad_km.add_trace(go.Scatterpolar(
                                r=vals_km+[vals_km[0]], theta=nomes_km+[nomes_km[0]],
                                fill='toself', fillcolor=cor, opacity=0.2,
                                line=dict(color=cor, width=2), name=f'{perfil} (n={n_km})'
                            ), row=rp, col=cp)
                        fig_rad_km.update_polars(radialaxis=dict(range=[0,100], tickvals=[25,50,75]))
                        fig_rad_km.update_layout(height=700,
                                                 title_text='Arquétipos Comportamentais — K-Means (k=4)')
                        st.plotly_chart(fig_rad_km, use_container_width=True)


                        if 'Área' in df.columns:
                            df_vk = df_cl.dropna(subset=['perf_media'])
                            perf_ap = (df_vk.groupby(['Área','perfil'])['perf_media']
                                       .mean().unstack().reindex(columns=nomes_cl))
                            n_ap = (df_vk.groupby(['Área','perfil']).size()
                                    .unstack(fill_value=0).reindex(columns=nomes_cl))
                            perfil_ideal = perf_ap.idxmax(axis=1)
                            annot_heat = []
                            for area in perf_ap.index:
                                row_ann = []
                                for perfil in nomes_cl:
                                    val_h = perf_ap.loc[area, perfil]
                                    n_h = n_ap.loc[area, perfil]
                                    star = ' *' if perfil == perfil_ideal.get(area) else ''
                                    row_ann.append(f'{val_h:.2f}{star}<br>n={n_h}' if not pd.isna(val_h) else '')
                                annot_heat.append(row_ann)
                            fig_heat = go.Figure(data=go.Heatmap(
                                z=perf_ap.values, x=nomes_cl,
                                y=perf_ap.index.tolist(),
                                text=annot_heat, texttemplate='%{text}',
                                colorscale='RdYlGn', zmin=1.5, zmax=2.5,
                                colorbar=dict(title='Perf Média')
                            ))
                            fig_heat.update_layout(height=300,
                                                   title='Performance Média por Perfil e Área  (* = perfil ideal)',
                                                   xaxis_title='Perfil Comportamental')
                            st.plotly_chart(fig_heat, use_container_width=True)

            # ── Tab 7: Evolução Individual ────────────────────────────────
            with tab_evol:
                if not cols_perf:
                    st.info("Sem colunas de performance para análise individual.")
                else:
                    nomes_evol = sorted(df['Nome Completo'].dropna().unique().tolist()) \
                                 if 'Nome Completo' in df.columns else []
                    if not nomes_evol:
                        st.info("Coluna 'Nome Completo' não disponível.")
                    else:
                        nome_sel = st.selectbox("Selecione o funcionário", nomes_evol, key='evol_sel')
                        row_e = df[df['Nome Completo'] == nome_sel].iloc[0]

                        # Métricas rápidas
                        ce1, ce2, ce3 = st.columns(3)
                        with ce1:
                            st.metric("Área", row_e.get('Área', 'N/A'))
                        with ce2:
                            pot_e = row_e.get('Potencial Bruto')
                            st.metric("Potencial Bruto", f"{pot_e:.0f}" if pd.notna(pot_e) else 'N/A')
                        with ce3:
                            cultura_e = row_e.get('Cultura classificação', np.nan)
                            st.metric("Fit Cultural", str(cultura_e) if pd.notna(cultura_e) else 'N/A')

                        # Linha de performance ao longo dos semestres
                        ordem_e = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
                        lbl_e = {c: f"{c.split('_')[2]}-{c.split('_')[1]}º" for c in ordem_e}
                        pts_e = [(lbl_e[c], row_e[c]) for c in ordem_e if pd.notna(row_e.get(c))]
                        if pts_e:
                            df_le = pd.DataFrame(pts_e, columns=['Semestre', 'Score'])
                            fig_le = px.line(df_le, x='Semestre', y='Score', markers=True,
                                             title=f'Evolução de Performance — {nome_sel}',
                                             labels={'Score':'Score de Performance'})
                            fig_le.update_yaxes(range=[0.5, 3.5], tickvals=[1, 2, 3])
                            media_e = df_le['Score'].mean()
                            fig_le.add_hline(y=media_e, line_dash='dot', line_color='gray',
                                             annotation_text=f'média {media_e:.2f}', annotation_position='top right')
                            st.plotly_chart(fig_le, use_container_width=True)
                        else:
                            st.info("Funcionário sem avaliações de performance registradas.")

                        # Assessments do funcionário
                        ass_e_map = [('Raciocínio','Raciocínio'),('Social','Social'),
                                     ('Motivacional','Motivacional'),('Cultura','Cultura pontuação')]
                        ass_e = {n: row_e[c] for n, c in ass_e_map if c in df.columns and pd.notna(row_e.get(c))}
                        if ass_e:
                            fig_ae = px.bar(x=list(ass_e.keys()), y=list(ass_e.values()),
                                            text=[f'{v:.0f}' for v in ass_e.values()],
                                            title='Scores de Assessment',
                                            labels={'x':'Assessment','y':'Score'})
                            st.plotly_chart(fig_ae, use_container_width=True)

                        # Radar de atributos
                        cols_atr_e = [c for c in df.columns if c.startswith('atributo-')]
                        vals_ae = {c.replace('atributo-',''): row_e[c] for c in cols_atr_e if pd.notna(row_e.get(c))}
                        if vals_ae:
                            nms_ae = list(vals_ae.keys())
                            vls_ae = list(vals_ae.values())
                            fig_re = go.Figure(go.Scatterpolar(
                                r=vls_ae+[vls_ae[0]], theta=nms_ae+[nms_ae[0]],
                                fill='toself', line=dict(color='#3498db', width=2),
                                fillcolor='rgba(52,152,219,0.2)', name=nome_sel))
                            fig_re.update_polars(radialaxis=dict(range=[0,100], tickvals=[25,50,75]))
                            fig_re.update_layout(title=f'Perfil de Atributos — {nome_sel}', height=420)
                            st.plotly_chart(fig_re, use_container_width=True)

            # ── Tab 8: Recomendações ──────────────────────────────────────
            with tab_rec:
                st.markdown("Esta aba sintetiza as análises anteriores em recomendações acionáveis para contratação e movimentação interna.")

                # ── Bloco 1: assessments que predizem performance ─────────
                st.subheader("1. Quais assessments predizem melhor a performance?")
                assessments_cfg_rec = [
                    ('Raciocínio',   'Raciocínio'),
                    ('Social',       'Social'),
                    ('Motivacional', 'Motivacional'),
                    ('Cultura',      'Cultura pontuação'),
                ]
                perf_m_rec = df[cols_perf].mean(axis=1)
                ass_rec = {n: df[c] for n, c in assessments_cfg_rec if c in df.columns}
                df_rec_ass = pd.DataFrame(ass_rec)
                df_rec_ass['perf_media'] = perf_m_rec
                df_rec_ass = df_rec_ass.dropna()
                if len(df_rec_ass) > 1:
                    corrs_rec = pd.Series(
                        {n: df_rec_ass[n].corr(df_rec_ass['perf_media']) for n in ass_rec},
                        name='correlação'
                    ).sort_values(ascending=False)
                    col_ra1, col_ra2 = st.columns([1, 2])
                    with col_ra1:
                        rows_ass_rec = []
                        for nome, r in corrs_rec.items():
                            direcao = "positiva" if r > 0 else "negativa"
                            forca = "forte" if abs(r) >= 0.4 else "moderada" if abs(r) >= 0.2 else "fraca"
                            rows_ass_rec.append({'Assessment': nome, 'r': round(r, 2), 'Associação': f"{forca} {direcao}"})
                        st.dataframe(pd.DataFrame(rows_ass_rec), use_container_width=True, hide_index=True)
                    with col_ra2:
                        melhor_ass = corrs_rec.index[0]
                        r_melhor = corrs_rec.iloc[0]
                        positivos = corrs_rec[corrs_rec > 0.1].index.tolist()
                        negativos = corrs_rec[corrs_rec < -0.1].index.tolist()
                        msg_ass = f"**{melhor_ass}** é o assessment com maior associação com performance no trabalho (r = {r_melhor:.2f})."
                        if positivos:
                            msg_ass += f" Candidatos com scores mais altos em **{', '.join(positivos)}** tendem a apresentar melhor desempenho."
                        if negativos:
                            msg_ass += f" **{', '.join(negativos)}** apresenta correlação negativa — scores muito altos podem estar associados a perfis menos adaptados ao ambiente de trabalho avaliado."
                        st.info(msg_ass)
                else:
                    st.info("Dados insuficientes para calcular correlações entre assessments e performance.")

                # ── Bloco 2: atributos que predizem performance por área ──
                st.subheader("2. Quais atributos comportamentais predizem performance por área?")
                cols_atr_rec = [c for c in df.columns if c.startswith('atributo-')]
                if cols_atr_rec and 'Área' in df.columns:
                    df_atr_rec = df[cols_atr_rec + ['Área']].copy()
                    df_atr_rec['perf_media'] = perf_m_rec
                    df_atr_rec = df_atr_rec.dropna()
                    if len(df_atr_rec) > 10:
                        rec_rows = []
                        for area, grp in df_atr_rec.groupby('Área'):
                            if len(grp) < 5:
                                continue
                            corrs_a = grp[cols_atr_rec].corrwith(grp['perf_media']).sort_values(ascending=False)
                            top3 = [c.replace('atributo-', '') for c in corrs_a.head(3).index]
                            top3_r = [round(v, 2) for v in corrs_a.head(3).values]
                            rec_rows.append({
                                'Área': area,
                                'Top atributos preditivos': ', '.join(f'{a} (r={r})' for a, r in zip(top3, top3_r)),
                                'Recomendação de contratação': f"Priorizar candidatos com alto score em {top3[0]}" + (f" e {top3[1]}" if len(top3) > 1 else ""),
                            })
                        if rec_rows:
                            st.dataframe(pd.DataFrame(rec_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Dados de atributos insuficientes para análise por área.")

                # ── Bloco 3: perfil ideal de contratação (clustering) ─────
                st.subheader("3. Perfil comportamental ideal por área")
                cols_atr_km_rec = [c for c in df.columns if c.startswith('atributo-')]
                if cols_atr_km_rec and 'Área' in df.columns:
                    try:
                        from sklearn.preprocessing import StandardScaler
                        from sklearn.cluster import KMeans
                        df_cl_rec = df[cols_atr_km_rec + ['Área']].copy()
                        df_cl_rec['perf_media'] = perf_m_rec
                        df_cl_rec = df_cl_rec.dropna(subset=cols_atr_km_rec)
                        if len(df_cl_rec) >= 8:
                            Xs_rec = StandardScaler().fit_transform(df_cl_rec[cols_atr_km_rec].values)
                            km_rec = KMeans(n_clusters=4, random_state=42, n_init=10)
                            df_cl_rec['perfil'] = km_rec.fit_predict(Xs_rec)
                            df_cl_rec['perfil'] = df_cl_rec['perfil'].map({i: f'Perfil {i+1}' for i in range(4)})
                            nomes_km_rec = [c.replace('atributo-', '') for c in cols_atr_km_rec]
                            centros_rec = df_cl_rec.groupby('perfil')[cols_atr_km_rec].mean()
                            centros_rec.columns = nomes_km_rec

                            df_cl_rec_v = df_cl_rec.dropna(subset=['perf_media'])
                            perf_ap_rec = (df_cl_rec_v.groupby(['Área', 'perfil'])['perf_media']
                                           .mean().unstack())
                            n_ap_rec = (df_cl_rec_v.groupby(['Área', 'perfil']).size()
                                        .unstack(fill_value=0))
                            perfil_ideal_rec = perf_ap_rec.idxmax(axis=1)

                            ideal_rows = []
                            for area in perf_ap_rec.index:
                                ideal = perfil_ideal_rec.get(area)
                                if ideal and ideal in centros_rec.index:
                                    top_attrs = centros_rec.loc[ideal].sort_values(ascending=False).head(4)
                                    n_total_area = int(n_ap_rec.loc[area].sum()) if area in n_ap_rec.index else 0
                                    n_ideal = int(n_ap_rec.loc[area, ideal]) if ideal in n_ap_rec.columns else 0
                                    ideal_rows.append({
                                        'Área': area,
                                        'Perfil ideal': ideal,
                                        'Score médio do perfil ideal': round(perf_ap_rec.loc[area, ideal], 2),
                                        'Atributos mais elevados': ', '.join(top_attrs.index.tolist()),
                                        'n no perfil ideal': f"{n_ideal} de {n_total_area}",
                                    })
                            if ideal_rows:
                                st.markdown("**Perfil ideal por área:**")
                                for row in ideal_rows:
                                    attrs_pipe = ' | '.join(row['Atributos mais elevados'].split(', '))
                                    st.markdown(f"- **{row['Área']}:** {row['Perfil ideal']} — atributos dominantes: {attrs_pipe}")
                    except ImportError:
                        st.info("scikit-learn não instalado.")
                else:
                    st.info("Dados de atributos insuficientes para análise de perfil ideal.")

                # ── Bloco 4: candidatos a movimentação interna ────────────
                st.subheader("4. Candidatos prioritários para movimentação interna")
                if 'Potencial Bruto' in df.columns and cols_perf:
                    n_aval_rec = df[cols_perf].notna().sum(axis=1)
                    pm_rec = df[cols_perf].mean(axis=1)
                    df_mov = pd.DataFrame({
                        'Nome Completo': df.get('Nome Completo', df['CPF']),
                        'Área': df['Área'] if 'Área' in df.columns else 'N/A',
                        'Potencial Bruto': df['Potencial Bruto'],
                        'perf_media': pm_rec.round(2),
                        'n_avaliacoes': n_aval_rec,
                    })
                    df_mov = df_mov[(df_mov['n_avaliacoes'] >= 2) & (df_mov['Potencial Bruto'].notna())].copy()
                    if len(df_mov) > 0:
                        q33_rec = df_mov['Potencial Bruto'].quantile(0.33)
                        q66_rec = df_mov['Potencial Bruto'].quantile(0.66)
                        df_mov['perf_cat'] = pd.cut(df_mov['perf_media'], bins=[0, 1.5, 2.5, 3.01],
                                                    labels=['Baixa', 'Média', 'Alta'], include_lowest=True)
                        df_mov['pot_cat'] = pd.cut(df_mov['Potencial Bruto'], bins=[0, q33_rec, q66_rec, 101],
                                                   labels=['Baixo', 'Médio', 'Alto'], include_lowest=True)

                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.markdown("**Promoção / desafios maiores**")
                            st.caption("Alto potencial com performance média ou baixa — podem estar subalocados.")
                            promovíveis = df_mov[
                                (df_mov['pot_cat'] == 'Alto') & (df_mov['perf_cat'].isin(['Baixa', 'Média']))
                            ][['Nome Completo', 'Área', 'Potencial Bruto', 'perf_media']].sort_values('Potencial Bruto', ascending=False)
                            st.dataframe(promovíveis.reset_index(drop=True), use_container_width=True, hide_index=True)

                        with col_m2:
                            st.markdown("**Atenção / suporte imediato**")
                            st.caption("Baixo potencial e baixa performance — risco de saída ou necessidade de intervenção.")
                            em_risco = df_mov[
                                (df_mov['pot_cat'] == 'Baixo') & (df_mov['perf_cat'] == 'Baixa')
                            ][['Nome Completo', 'Área', 'Potencial Bruto', 'perf_media']].sort_values('perf_media')
                            st.dataframe(em_risco.reset_index(drop=True), use_container_width=True, hide_index=True)
                else:
                    st.info("Coluna 'Potencial Bruto' não encontrada — análise de movimentação indisponível.")

                # ── Bloco 5: Regressão múltipla ──────────────────────────────────────────────
                st.subheader("5. O que mais explica a performance? (Regressão Múltipla)")
                try:
                    from sklearn.linear_model import LinearRegression
                    from sklearn.preprocessing import StandardScaler

                    features_reg = [c for c in ['Raciocínio','Social','Motivacional','Cultura pontuação']
                                    if c in df.columns]
                    cols_atr_reg = [c for c in df.columns if c.startswith('atributo-')]
                    features_reg += cols_atr_reg

                    if features_reg:
                        df_reg = df[features_reg].copy()
                        df_reg['perf_media'] = df[cols_perf].mean(axis=1)
                        df_reg = df_reg.dropna()

                        if len(df_reg) > 20:
                            X_reg = df_reg[features_reg].values
                            y_reg = df_reg['perf_media'].values
                            Xs_reg = StandardScaler().fit_transform(X_reg)
                            reg = LinearRegression().fit(Xs_reg, y_reg)
                            r2 = reg.score(Xs_reg, y_reg)

                            coef_df = pd.DataFrame({
                                'Variável': [f.replace('atributo-','') for f in features_reg],
                                'Coeficiente padronizado': reg.coef_
                            }).sort_values('Coeficiente padronizado', key=abs, ascending=False)

                            col_r1, col_r2 = st.columns([1, 2])
                            with col_r1:
                                st.metric("R² — variância explicada", f"{r2:.3f}")
                                st.caption(f"n = {len(df_reg):,} funcionários com todos os dados disponíveis.\n\n"
                                           "Coeficientes padronizados permitem comparar o peso de cada variável "
                                           "independentemente da escala original.")
                            with col_r2:
                                fig_coef = px.bar(coef_df, x='Coeficiente padronizado', y='Variável',
                                                   orientation='h',
                                                   color='Coeficiente padronizado',
                                                   color_continuous_scale='RdYlGn',
                                                   range_color=[-0.3, 0.3],
                                                   title=f'Coeficientes da Regressão (R² = {r2:.3f})',
                                                   labels={'Variável':'Variável'})
                                fig_coef.add_vline(x=0, line_dash='dash', line_color='gray')
                                fig_coef.update_layout(coloraxis_showscale=False)
                                st.plotly_chart(fig_coef, use_container_width=True)
                        else:
                            st.info("Dados insuficientes para regressão (menos de 20 funcionários com todas as variáveis).")
                except ImportError:
                    st.info("scikit-learn não instalado. Execute: pip install scikit-learn")

            # ── Qualidade dos Dados ──────────────────────────────────────
            st.markdown("---")
            with st.expander("⚠️ Qualidade dos Dados — Limitações da Análise"):
                total = len(df)
                ordem_q = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))

                cob_rows = []
                for col in ordem_q:
                    n = int(df[col].notna().sum())
                    lbl = f"{col.split('_')[2]}-{col.split('_')[1]}º"
                    cob_rows.append({'Semestre': lbl, 'Avaliados': n, '% do total': f"{n/total*100:.1f}%"})

                com_qualquer_perf = int(df[cols_perf].notna().any(axis=1).sum())
                sem_perf = total - com_qualquer_perf

                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    st.markdown("**Cobertura de performance por semestre**")
                    st.caption(f"{sem_perf:,} de {total:,} funcionários ({sem_perf/total*100:.1f}%) não têm nenhum semestre avaliado e ficam fora das análises de score.")
                    if ordem_q:
                        primeiro = ordem_q[0]
                        pct_primeiro = df[primeiro].notna().sum() / total
                        if pct_primeiro < 0.15:
                            lbl_p = f"{primeiro.split('_')[2]}-{primeiro.split('_')[1]}º"
                            st.warning(f"**{lbl_p}** tem {pct_primeiro*100:.1f}% de cobertura — tendências envolvendo esse semestre devem ser interpretadas com cautela.")
                    st.dataframe(pd.DataFrame(cob_rows), use_container_width=True, hide_index=True)

                with col_q2:
                    st.markdown("**Cobertura por dimensão analítica**")
                    limitacoes = []
                    if 'Potencial Bruto' in df.columns:
                        n_pot = int(df['Potencial Bruto'].notna().sum())
                        limitacoes.append({'Dimensão': 'Potencial Bruto', 'n disponível': f"{n_pot:,} ({n_pot/total*100:.1f}%)", 'Afeta': 'Matriz 9-Box, correlação'})
                    cols_atr_q = [c for c in df.columns if c.startswith('atributo-')]
                    if cols_atr_q:
                        n_atr = int(df[cols_atr_q].notna().all(axis=1).sum())
                        limitacoes.append({'Dimensão': 'Atributos (completos)', 'n disponível': f"{n_atr:,} ({n_atr/total*100:.1f}%)", 'Afeta': 'Radar, clustering'})
                    for ass in ['Raciocínio', 'Social', 'Motivacional', 'Cultura pontuação']:
                        if ass in df.columns:
                            n_a = int(df[ass].notna().sum())
                            limitacoes.append({'Dimensão': ass, 'n disponível': f"{n_a:,} ({n_a/total*100:.1f}%)", 'Afeta': 'Tab Assessments'})
                    limitacoes.append({
                        'Dimensão': 'Match',
                        'n disponível': '0 (0.0%)',
                        'Afeta': 'Não disponível — 100% nulo na base'
                    })
                    if limitacoes:
                        st.dataframe(pd.DataFrame(limitacoes), use_container_width=True, hide_index=True)
                    st.caption("Análises que cruzam múltiplas dimensões (ex: 9-Box + Área) operam sobre a interseção dos subconjuntos disponíveis e podem representar uma parcela pequena do total.")

            # ── Conclusões ───────────────────────────────────────────────
            st.markdown("---")
            st.subheader("Conclusões")
            st.caption(
                "Síntese dos principais achados para subsidiar decisões de **contratação** e "
                "**movimentação interna** com foco em melhoria de performance."
            )

            # ── Pré-computação ───────────────────────────────────────────
            ordem_conc    = sorted(cols_perf, key=lambda c: (int(c.split('_')[2]), int(c.split('_')[1])))
            lbl_conc      = lambda c: f"{c.split('_')[2]}-{c.split('_')[1]}º"
            total_conc    = len(df)
            n_com_perf    = int(df[cols_perf].notna().any(axis=1).sum())
            scores_todos  = df[cols_perf].stack()
            score_modal   = int(scores_todos.mode()[0]) if len(scores_todos) > 0 else None
            pct_modal     = (scores_todos == score_modal).mean() * 100 if score_modal else None
            medias_sem    = [(lbl_conc(c), df[c].mean()) for c in ordem_conc if df[c].notna().sum() > 10]
            media_area    = df.groupby('Área')[cols_perf].mean().mean(axis=1).dropna() if 'Área' in df.columns else pd.Series(dtype=float)
            perf_m_conc   = df[cols_perf].mean(axis=1)
            cols_atr_conc = [c for c in df.columns if c.startswith('atributo-')]

            # Potencial vs performance
            r_pot_conc = None
            if 'Potencial Bruto' in df.columns:
                n_pot_conc = int(df['Potencial Bruto'].notna().sum())
                if n_pot_conc > 1:
                    r_pot_conc = df['Potencial Bruto'].corr(perf_m_conc)

            # Atributos vs performance
            atr_mais_corr, r_atr_top, n_atr_conc = None, None, 0
            if cols_atr_conc:
                n_atr_conc = int(df[cols_atr_conc].notna().all(axis=1).sum())
                df_atr_perf = df[cols_atr_conc].copy()
                df_atr_perf['perf'] = perf_m_conc
                df_atr_perf = df_atr_perf.dropna()
                if len(df_atr_perf) > 1:
                    corrs_atr = df_atr_perf[cols_atr_conc].corrwith(df_atr_perf['perf']).sort_values(ascending=False)
                    atr_mais_corr = corrs_atr.index[0].replace('atributo-', '')
                    r_atr_top = corrs_atr.iloc[0]

            # Fit Cultural
            r_cult_perf, med_cult, pct_baixo_cult = None, None, None
            if 'Cultura pontuação' in df.columns:
                med_cult = df['Cultura pontuação'].median()
                r_cult_perf = df['Cultura pontuação'].corr(perf_m_conc)
            if 'Cultura classificação' in df.columns:
                ordem_cult_c = ['Baixo','Medio-Baixo','Medio','Medio-Alto','Alto','Muito-Alto']
                baixo_cult = df['Cultura classificação'].isin(['Baixo', 'Medio-Baixo', 'Muito-Baixo'])
                n_cult_tot = df['Cultura classificação'].notna().sum()
                pct_baixo_cult = baixo_cult.sum() / n_cult_tot * 100 if n_cult_tot > 0 else None

            # Assessment mais preditivo
            ass_map_conc = [('Raciocínio','Raciocínio'),('Social','Social'),
                            ('Motivacional','Motivacional'),('Cultura','Cultura pontuação')]
            df_ass_conc = pd.DataFrame({n: df[c] for n, c in ass_map_conc if c in df.columns})
            df_ass_conc['perf_media'] = perf_m_conc
            df_ass_conc = df_ass_conc.dropna()
            corrs_ass_conc = pd.Series(dtype=float)
            if len(df_ass_conc) > 1:
                cols_ass = [n for n, _ in ass_map_conc if n in df_ass_conc.columns]
                corrs_ass_conc = pd.Series(
                    {n: df_ass_conc[n].corr(df_ass_conc['perf_media']) for n in cols_ass}
                ).sort_values(ascending=False)

            # Regressão múltipla (coeficiente top)
            reg_r2, reg_top_var, reg_top_coef = None, None, None
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.preprocessing import StandardScaler as _SS
                _feats = [c for c in ['Raciocínio','Social','Motivacional','Cultura pontuação'] if c in df.columns] + cols_atr_conc
                if _feats:
                    _dr = df[_feats].copy()
                    _dr['perf_media'] = perf_m_conc
                    _dr = _dr.dropna()
                    if len(_dr) > 20:
                        _Xs = _SS().fit_transform(_dr[_feats].values)
                        _reg = LinearRegression().fit(_Xs, _dr['perf_media'].values)
                        reg_r2 = _reg.score(_Xs, _dr['perf_media'].values)
                        _coefs = sorted(zip([f.replace('atributo-','') for f in _feats], _reg.coef_),
                                        key=lambda x: abs(x[1]), reverse=True)
                        reg_top_var, reg_top_coef = _coefs[0]
            except ImportError:
                pass

            # Movimentação interna
            subalocados_c, em_risco_c = 0, 0
            if 'Potencial Bruto' in df.columns and cols_perf:
                _n_av = df[cols_perf].notna().sum(axis=1)
                _pm   = perf_m_conc
                _dmov = pd.DataFrame({'Pot': df['Potencial Bruto'], 'perf': _pm, 'nav': _n_av})
                _dmov = _dmov[(_dmov['nav'] >= 2) & (_dmov['Pot'].notna())]
                if len(_dmov) > 0:
                    _q66 = _dmov['Pot'].quantile(0.66)
                    _q33 = _dmov['Pot'].quantile(0.33)
                    subalocados_c = int(((_dmov['Pot'] > _q66) & (_dmov['perf'] < 2.0)).sum())
                    em_risco_c    = int(((_dmov['Pot'] <= _q33) & (_dmov['perf'] < 1.5)).sum())

            # ── Métricas rápidas ─────────────────────────────────────────
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Funcionários avaliados",
                          f"{n_com_perf/total_conc*100:.0f}%",
                          f"{n_com_perf:,} de {total_conc:,}")
            with mc2:
                if score_modal is not None:
                    st.metric("Score dominante", f"{score_modal} (Atende)",
                              f"{pct_modal:.0f}% das avaliações")
            with mc3:
                if r_pot_conc is not None:
                    st.metric("Potencial prediz perf?",
                              f"r = {r_pot_conc:.2f}",
                              "Correlação praticamente nula")
            with mc4:
                if med_cult is not None:
                    st.metric("Fit Cultural mediano",
                              f"{med_cult:.0f}/100",
                              f"{pct_baixo_cult:.0f}% nas faixas baixas" if pct_baixo_cult is not None else "")

            st.markdown("")

            # ── Achado central (banner) ──────────────────────────────────
            st.error(
                "**O principal instrumento de avaliação — Potencial Bruto — não prediz performance** "
                + (f"(r = {r_pot_conc:.2f}, praticamente nulo). " if r_pot_conc is not None else "")
                + "Se esse score é usado para contratar ou promover, as decisões estão sendo tomadas "
                "com uma régua que não mede o que importa. "
                "Os dados mostram que **atributos comportamentais por área** e **fit cultural** "
                "têm mais sinal e devem substituir ou complementar o Potencial Bruto como critério primário."
            )

            # ── Blocos temáticos ─────────────────────────────────────────
            bl1, bl2 = st.columns(2)

            with bl1:
                # O que explica performance (regressão)
                if reg_r2 is not None:
                    st.info(
                        f"**O que de fato explica a performance? (Regressão Múltipla)**\n\n"
                        f"Combinando todos os assessments e os 16 atributos comportamentais, "
                        f"o modelo explica **{reg_r2*100:.1f}% da variância de performance** (R² = {reg_r2:.3f}). "
                        f"O preditor de maior peso é **{reg_top_var}** "
                        f"(coeficiente padronizado = {reg_top_coef:+.3f}). "
                        f"R² baixo é esperado — performance é multifatorial — mas os preditores "
                        f"identificados são os melhores critérios quantitativos disponíveis na base. "
                        f"Detalhes na aba **Recomendações → Bloco 5**."
                    )
                elif atr_mais_corr is not None:
                    st.info(
                        f"**Atributos comportamentais** ({n_atr_conc:,} func. — {n_atr_conc/total_conc*100:.1f}%)\n\n"
                        f"**{atr_mais_corr}** tem a maior correlação positiva com performance "
                        f"(r = {r_atr_top:.2f}). "
                        f"A correlação varia por área — o perfil ideal de cada departamento "
                        f"está na aba **Recomendações → Bloco 3**."
                    )

                # Fit Cultural
                if med_cult is not None:
                    cult_msg = (
                        f"**Fit Cultural — diagnóstico e impacto**\n\n"
                        f"A mediana de fit cultural é **{med_cult:.0f}/100**, com "
                        + (f"**{pct_baixo_cult:.0f}% dos funcionários nas faixas baixas** (Baixo/Médio-Baixo). " if pct_baixo_cult else "")
                        + "Funcionários com baixo alinhamento cultural tendem a se engajar menos e "
                        "colaborar menos, independentemente de capacidade técnica — um **teto silencioso de performance**. "
                    )
                    if r_cult_perf is not None:
                        cult_msg += (
                            f"A correlação entre pontuação de Cultura e performance é "
                            f"**r = {r_cult_perf:.2f}** "
                            + ("— sinal presente, mas fraco no curto prazo." if abs(r_cult_perf) < 0.3 else "— correlação relevante.")
                        )
                    st.info(cult_msg)

                # Tendência temporal
                if len(medias_sem) >= 2:
                    pr_lbl, pr_val = medias_sem[0]
                    ul_lbl, ul_val = medias_sem[-1]
                    delta_t = ul_val - pr_val
                    st.info(
                        f"**Tendência de performance ao longo do tempo**\n\n"
                        f"De **{pr_lbl}** ({pr_val:.2f}) a **{ul_lbl}** ({ul_val:.2f}) — "
                        f"variação de **{delta_t:+.2f}**. "
                        + ("A tendência de alta é sinal de que as intervenções têm efeito; "
                           "manter a pressão é essencial." if delta_t > 0.05
                           else "A estabilidade indica ausência de melhora sistêmica — "
                                "o status quo não se resolve sozinho.")
                    )

            with bl2:
                # Distribuição de scores — sinal de avaliação viciada
                if score_modal is not None:
                    st.warning(
                        f"**Aviso: avaliação sem poder discriminatório**\n\n"
                        f"**{pct_modal:.0f}% de todas as avaliações** são score {score_modal} "
                        f"(Atende expectativas). Essa concentração é estatisticamente improvável "
                        f"numa distribuição real de performance — o mais provável é que gestores "
                        f"evitem os extremos por pressão social ou falta de critérios claros. "
                        f"Quando a avaliação perde discriminação, ela deixa de subsidiar decisões "
                        f"de promoção, desenvolvimento e desligamento."
                    )

                # Performance por área
                if len(media_area) > 0:
                    area_melhor = media_area.idxmax()
                    area_pior   = media_area.idxmin()
                    dist_area   = df['Área'].value_counts() if 'Área' in df.columns else pd.Series(dtype=int)
                    areas_peq   = dist_area[dist_area / total_conc < 0.05].index.tolist()
                    msg_area = (
                        f"**Performance por área**\n\n"
                        f"**{area_melhor}** lidera (média {media_area[area_melhor]:.2f}); "
                        f"**{area_pior}** registra a menor média ({media_area[area_pior]:.2f}). "
                        f"A diferença entre as áreas é pequena (faixa 1.9–2.1) — "
                        f"o problema não é desigualdade entre áreas, mas o teto coletivo baixo. "
                    )
                    if areas_peq:
                        msg_area += f"{', '.join(areas_peq)}: amostras pequenas (<5%) — interpretar com cautela."
                    st.info(msg_area)

                # Assessment mais preditivo
                if len(corrs_ass_conc) > 0:
                    top_ass = corrs_ass_conc.index[0]
                    r_top_ass = corrs_ass_conc.iloc[0]
                    st.info(
                        f"**Assessment com maior sinal para contratação**\n\n"
                        f"Entre os 4 assessments, **{top_ass}** tem a maior correlação com performance "
                        f"(r = {r_top_ass:.2f}). "
                        f"Mesmo correlações fracas justificam maior peso no processo seletivo "
                        f"quando são o melhor preditor disponível. "
                        f"Lembrete: todos os assessments têm sinal limitado — "
                        f"os **atributos comportamentais por área** são mais informativos."
                    )

                # Composição da base
                if 'Área' in df.columns:
                    dist_conc = df['Área'].value_counts()
                    top2 = dist_conc.head(2)
                    pct_top2 = top2.sum() / total_conc * 100
                    st.info(
                        f"**Composição da base**\n\n"
                        f"**{top2.index[0]}** ({top2.iloc[0]/total_conc*100:.0f}%) e "
                        f"**{top2.index[1]}** ({top2.iloc[1]/total_conc*100:.0f}%) concentram "
                        f"**{pct_top2:.0f}%** dos funcionários. "
                        f"Conclusões globais refletem majoritariamente essas duas áreas. "
                        f"Analise cada área separadamente antes de aplicar políticas uniformes."
                    )

            # ── Recomendações ─────────────────────────────────────────────
            st.markdown("---")
            st.subheader("O que fazer com isso? — Recomendações prioritárias")
            st.caption(
                "Ordenadas por **impacto estimado × facilidade de implementação**. "
                "Detalhes, tabelas e listas nominais na aba **Recomendações**."
            )

            rec1, rec2 = st.columns(2)
            with rec1:
                st.error(
                    "**1. Substituir o Potencial Bruto como critério principal de contratação**\n\n"
                    "O Potencial Bruto não prediz performance. Continuar usando-o como régua principal "
                    "de seleção é desperdiçar capacidade preditiva disponível. "
                    "**Substituir por:** perfil comportamental ideal por área (atributos com maior correlação "
                    "com performance em cada departamento) + pontuação de fit cultural como filtro. "
                    "Ver aba **Recomendações → Blocos 2, 3 e 5**."
                )

                if len(media_area) > 0:
                    area_pior_rec = media_area.idxmin()
                    st.warning(
                        f"**2. Intervenção prioritária em {area_pior_rec}**\n\n"
                        f"{area_pior_rec} registra o menor score médio de performance ({media_area[area_pior_rec]:.2f}). "
                        f"Ação dupla: (a) revisar o critério de contratação usando o perfil comportamental "
                        f"dos funcionários de melhor performance nessa área; "
                        f"(b) mapear se há padrão de gestão ou contexto que explique o resultado baixo."
                    )

                st.warning(
                    "**3. Calibrar o processo de avaliação de performance**\n\n"
                    f"Com {pct_modal:.0f}% das avaliações concentradas no score {score_modal}, "
                    "a avaliação atual não diferencia quem performa bem de quem está estagnado. "
                    "Sem discriminação, não há como identificar quem desenvolver, promover ou desligar. "
                    "Treinar gestores em calibração e usar comitês de revisão nos extremos "
                    "é pré-requisito para que qualquer outra intervenção funcione."
                )

            with rec2:
                st.warning(
                    "**4. Incorporar fit cultural como filtro de seleção**\n\n"
                    + (f"Mediana atual de {med_cult:.0f}/100 — a maioria dos funcionários avaliados "
                       f"está nas faixas de baixo alinhamento. " if med_cult is not None else "")
                    + "Usar a pontuação de Cultura como critério eliminatório (acima do percentil 50) "
                    "tende a reduzir desengajamento e fricção cultural — fatores que limitam "
                    "performance independentemente de capacidade técnica."
                )

                if subalocados_c > 0 or em_risco_c > 0:
                    st.warning(
                        f"**5. Agir sobre os quadrantes críticos da Matriz 9-Box**\n\n"
                        + (f"**{subalocados_c} funcionários** com alto potencial e performance abaixo de 2.0 "
                           f"podem estar subalocados — candidatos a novos desafios ou mudança de área. "
                           f"Entrevista estruturada com cada um pode revelar o que os trava. " if subalocados_c > 0 else "")
                        + (f"\n\n**{em_risco_c} funcionários** com baixo potencial e performance abaixo de 1.5 "
                           f"demandam atenção imediata: plano de 90 dias com metas claras e reavaliação. " if em_risco_c > 0 else "")
                        + "\n\nLista nominal na aba **Recomendações → Bloco 4**."
                    )

                if reg_r2 is not None:
                    st.info(
                        f"**6. Usar a regressão múltipla como bússola de seleção**\n\n"
                        f"O modelo identificou **{reg_top_var}** como o preditor de maior peso "
                        f"(coeficiente = {reg_top_coef:+.3f}). "
                        f"Candidatos com score elevado nesse atributo têm, em média, maior performance esperada. "
                        f"R² = {reg_r2:.3f} — o modelo explica {reg_r2*100:.1f}% da variância de performance "
                        f"com os dados disponíveis. "
                        f"Expandir a base de assessments aumentaria o poder preditivo."
                    )
                else:
                    st.info(
                        "**6. Expandir cobertura de assessments**\n\n"
                        "Apenas ~22% da base tem Potencial Bruto e ~22% tem perfil completo de atributos. "
                        "Ampliar a coleta de dados psicométricos aumenta o poder de análise e "
                        "viabiliza modelos preditivos mais robustos para contratação e movimentação."
                    )
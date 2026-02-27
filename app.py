import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DE ACESSO ---
# Suas URLs estão corretas, apontando para o CSV na nuvem
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=375511285&single=true&output=csv"
URL_VENDAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=1146959211&single=true&output=csv"
URL_METAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=430597826&single=true&output=csv"

st.set_page_config(page_title="SDR Intelligence | Global Performance", layout="wide")

# --- CSS PARA OS CARDS ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {font-size: 1.6vw !important;}
    [data-testid="stMetricLabel"] {font-size: 0.85vw !important;}
    .block-container {padding-top: 2rem; padding-bottom: 0rem;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=5)
def load_all_data():
    try:
        # Lê os CSVs direto da nuvem
        df_sdr = pd.read_csv(URL_BASE).fillna(0)
        df_vendas = pd.read_csv(URL_VENDAS).fillna(0)
        df_metas = pd.read_csv(URL_METAS).fillna(0)
        
        # Limpeza de espaços em branco nos nomes das colunas
        for df in [df_sdr, df_vendas, df_metas]:
            df.columns = df.columns.str.strip()
            if 'SDR' in df.columns: df['SDR'] = df['SDR'].astype(str).str.strip()
            if 'Mês' in df.columns: df['Mês'] = df['Mês'].astype(str).str.strip()
            
        return df_sdr, df_vendas, df_metas
    except Exception as e:
        st.error(f"Erro ao sincronizar dados: {e}")
        return None, None, None

df_sdr, df_vendas, df_metas = load_all_data()

if df_sdr is not None:
    # --- FILTROS ---
    st.sidebar.header("Filtros de Visão")
    meses_disponiveis = sorted([str(m) for m in df_sdr['Mês'].unique() if pd.notna(m) and m != '0'])
    mes_padrao = [meses_disponiveis[-1]] if meses_disponiveis else []
    meses_sel = st.sidebar.multiselect("Selecionar Meses", options=meses_disponiveis, default=mes_padrao)
    
    todos_sdrs = pd.concat([df_sdr['SDR'], df_metas['SDR'], df_vendas['SDR']]).unique()
    sdrs_globais = sorted([str(s) for s in todos_sdrs if pd.notna(s) and s not in ['0', 'nan', '0.0']])
    sdr_sel = st.sidebar.multiselect("Selecionar SDRs", options=sdrs_globais, default=sdrs_globais)
    
    # --- PROCESSAMENTO AGREGADO E CÁLCULO DE NÃO REALIZADAS ---
    
    # Filtra dados
    fsdr = df_sdr[(df_sdr['Mês'].isin(meses_sel)) & (df_sdr['SDR'].isin(sdr_sel))].copy()
    fvendas = df_vendas[(df_vendas['Mês'].isin(meses_sel)) & (df_vendas['SDR'].isin(sdr_sel))].groupby('SDR')['Valor'].sum().reset_index()
    fmetas = df_metas[(df_metas['Mês'].isin(meses_sel)) & (df_metas['SDR'].isin(sdr_sel))].groupby('SDR')[['Meta_Receita', 'Meta_Reunioes']].sum().reset_index()

    # Lógica: Não realizadas = Canceladas + No-show
    # Verifica se as colunas existem antes de calcular para evitar erro
    cols_necessarias = ['Previstas', 'Agendadas', 'Realizadas', 'Canceladas', 'No-show']
    if all(col in fsdr.columns for col in cols_necessarias):
        fsdr['Não Realizadas'] = fsdr['Canceladas'] + fsdr['No-show']
        # Agrupa após calcular a nova coluna
        fsdr_grouped = fsdr.groupby('SDR')[['Previstas', 'Agendadas', 'Realizadas', 'Não Realizadas']].sum().reset_index()
    else:
        st.error(f"Colunas faltantes no Sheets: {cols_necessarias}")
        st.stop()

    # --- CÁLCULOS TOTAIS AGREGADOS ---
    receita_atual = fvendas['Valor'].sum()
    meta_receita_total = fmetas['Meta_Receita'].sum()
    meta_agendamentos_total = fmetas['Meta_Reunioes'].sum()
    
    total_previstas = fsdr_grouped['Previstas'].sum()
    total_agendadas = fsdr_grouped['Agendadas'].sum()
    total_realizadas = fsdr_grouped['Realizadas'].sum()
    total_nao_realizadas = fsdr_grouped['Não Realizadas'].sum()

    # --- DASHBOARD PRINCIPAL ---
    st.title(f"SDR Global Performance - {', '.join(meses_sel)}")
    
    # Ajuste nas colunas para caber a nova métrica
    m1, m2, m3, m4, m5, m6, m7, m8 = st.columns(8)
    
    m1.metric("Meta Receita", f"$ {meta_receita_total:,.2f}")
    m2.metric("Receita Atual", f"$ {receita_atual:,.2f}")
    m3.metric("Meta Reuniões", int(meta_agendamentos_total))
    m4.metric("Previstas", int(total_previstas))
    m5.metric("Agendadas", int(total_agendadas))
    m6.metric("Realizadas", int(total_realizadas))
    m7.metric("Não Realizadas", int(total_nao_realizadas)) # Nova métrica
    
    taxa_conv = (total_realizadas / total_previstas * 100) if total_previstas > 0 else 0
    m8.metric("Eficiência %", f"{taxa_conv:.1f}%")

    st.divider()

    # Linha 2: Gráficos
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Receita por SDR (USD)")
        st.plotly_chart(px.bar(fvendas, x='SDR', y='Valor', text_auto='$.2s', color_discrete_sequence=['#00CC96']), use_container_width=True)
        
    with col_r:
        st.subheader("Funil de Atividades (Volume)")
        # Gráfico atualizado para incluir "Não Realizadas"
        fig_funil = px.bar(fsdr_grouped, x='SDR', y=['Previstas', 'Agendadas', 'Realizadas', 'Não Realizadas'], 
                           barmode='group',
                           color_discrete_map={
                               'Previstas': '#94A3B8', 
                               'Agendadas': '#6366F1', 
                               'Realizadas': '#48BB78',
                               'Não Realizadas': '#EF4444' # Cor vermelha para não realizadas
                           })
        st.plotly_chart(fig_funil, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.subheader("Detalhamento de Performance")
    tabela_final = fmetas.merge(fsdr_grouped, on='SDR', how='outer').merge(fvendas, on='SDR', how='outer').fillna(0)
    tabela_final = tabela_final[tabela_final['SDR'].isin(sdr_sel)]
    tabela_final['% Conv.'] = (tabela_final['Realizadas'] / tabela_final['Previstas'] * 100).fillna(0)
    
    tabela_disp = tabela_final.copy()
    for col in ['Meta_Receita', 'Valor']:
        tabela_disp[col] = tabela_disp[col].apply(lambda x: f"$ {x:,.2f}")
    tabela_disp['% Conv.'] = tabela_disp['% Conv.'].apply(lambda x: f"{x:.1f}%")
    
    # Atualizado para incluir Não Realizadas na tabela
    cols_view = ['SDR', 'Meta_Reunioes', 'Previstas', 'Agendadas', 'Realizadas', 'Não Realizadas', '% Conv.', 'Meta_Receita', 'Valor']
    st.dataframe(tabela_disp[cols_view], use_container_width=True, hide_index=True)

else:
    st.info("Conectando aos dados...")
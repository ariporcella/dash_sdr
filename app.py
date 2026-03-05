import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import calendar

# --- CONFIGURAÇÃO DE ACESSO ---
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=375511285&single=true&output=csv"
URL_VENDAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=1146959211&single=true&output=csv"
URL_METAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=430597826&single=true&output=csv"
URL_MQL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ00MvebmbtmiDkGcz4OTxtGwrmmgEkJGLXARJRg6UDM001IXQRyxcMcjS35ACbN9JOF2cEzglaUZGL/pub?gid=1454439067&single=true&output=csv"

st.set_page_config(page_title="SDR Intelligence", layout="wide")

# --- CSS PARA VISUAL HIGH-TECH DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 1.8vw !important; color: #FFFFFF !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.9vw !important; color: #8B949E !important; }
    div[data-testid="stMetric"] { background-color: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; }
    h1, h2, h3 { color: #FFFFFF !important; }
    .block-container { padding-top: 1rem; }
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #30363D; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_all_data():
    try:
        df_sdr = pd.read_csv(URL_BASE).fillna(0)
        df_vendas = pd.read_csv(URL_VENDAS).fillna(0)
        df_metas = pd.read_csv(URL_METAS).fillna(0)
        df_mql = pd.read_csv(URL_MQL).fillna(0)
        
        for df in [df_sdr, df_vendas, df_metas, df_mql]:
            df.columns = df.columns.str.strip()
            if 'Mês' in df.columns:
                df['Mês'] = df['Mês'].astype(str).str.strip()
            if 'SDR' in df.columns:
                df['SDR'] = df['SDR'].astype(str).str.strip()

        if 'Entrada MQL' in df_mql.columns:
            df_mql['Entrada MQL'] = pd.to_numeric(df_mql['Entrada MQL'], errors='coerce').fillna(0)
        if 'Meta_Reunioes' in df_metas.columns:
            df_metas['Meta_Reunioes'] = pd.to_numeric(df_metas['Meta_Reunioes'], errors='coerce').fillna(0)
            
        if 'Motivo da perda' in df_mql.columns:
            df_mql['Motivo da perda'] = df_mql['Motivo da perda'].astype(str).str.strip().str.capitalize()
            
        return df_sdr, df_vendas, df_metas, df_mql
    except Exception as e:
        st.error(f"Erro ao sincronizar dados: {e}")
        return None, None, None, None

df_sdr, df_vendas, df_metas, df_mql = load_all_data()

meses_dict = {
    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
    'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
}

if df_sdr is not None:
    # --- FILTROS LATERAIS ---
    st.sidebar.markdown("## ⚙️ Configurações")
    meses_disponiveis = sorted([str(m) for m in df_sdr['Mês'].unique() if pd.notna(m) and m not in ['0', 'nan']])
    meses_sel = st.sidebar.multiselect("Selecionar Meses", options=meses_disponiveis, default=[meses_disponiveis[-1]] if meses_disponiveis else [])
    
    todos_sdrs = pd.concat([df_sdr['SDR'], df_metas['SDR'], df_vendas['SDR']]).unique()
    sdrs_globais = sorted([str(s) for s in todos_sdrs if pd.notna(s) and s not in ['0', 'nan', '0.0']])
    sdr_sel = st.sidebar.multiselect("Selecionar SDRs", options=sdrs_globais, default=sdrs_globais)
    
    # --- PROCESSAMENTO ---
    fsdr = df_sdr[(df_sdr['Mês'].isin(meses_sel)) & (df_sdr['SDR'].isin(sdr_sel))].groupby('SDR')[['Previstas', 'Agendadas', 'Realizadas']].sum().reset_index()
    fvendas = df_vendas[(df_vendas['Mês'].isin(meses_sel)) & (df_vendas['SDR'].isin(sdr_sel))].groupby('SDR')['Valor'].sum().reset_index()
    fmetas = df_metas[(df_metas['Mês'].isin(meses_sel)) & (df_metas['SDR'].isin(sdr_sel))].groupby('SDR')[['Meta_Receita', 'Meta_Reunioes']].sum().reset_index()
    df_mql_filtrado = df_mql[df_mql['Mês'].isin(meses_sel)]

    # --- DIAS ÚTEIS ---
    total_dias_uteis = 0
    for m in meses_sel:
        if m in meses_dict:
            ano_atual = datetime.now().year
            mes_num = meses_dict[m]
            ultimo_dia = calendar.monthrange(ano_atual, mes_num)[1]
            total_dias_uteis += np.busday_count(f'{ano_atual}-{mes_num:02d}-01', 
                                                datetime(ano_atual, mes_num, ultimo_dia).strftime('%Y-%m-%d')) + 1
    total_dias_uteis = max(total_dias_uteis, 1)

    # --- DASHBOARD PRINCIPAL ---
    st.title("⚡ SDR Global Performance")
    st.markdown("---")
    
    # --- SEÇÃO 1: MÉTRICAS PRINCIPAIS ---
    st.subheader("Visão Geral")
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    
    receita_atual = fvendas['Valor'].sum()
    meta_receita_total = fmetas['Meta_Receita'].sum()
    total_agendadas = fsdr['Agendadas'].sum()
    total_realizadas = fsdr['Realizadas'].sum()
    total_previstas = fsdr['Previstas'].sum()
    total_meta_reunioes = fmetas['Meta_Reunioes'].sum() 
    
    # ATUALIZAÇÃO DA TAXA: Agora Realizadas / Agendadas
    taxa_showup = (total_realizadas / total_agendadas * 100) if total_agendadas > 0 else 0

    m1.metric("Meta Receita", f"$ {meta_receita_total:,.2f}")
    m2.metric("Receita Atual", f"$ {receita_atual:,.2f}")
    m3.metric("Meta Agend.", int(total_meta_reunioes))
    m4.metric("Previstas", int(total_previstas))
    m5.metric("Agendamentos", int(total_agendadas))
    m6.metric("Realizadas", int(total_realizadas))
    m7.metric("Show-up %", f"{taxa_showup:.1f}%")

    st.markdown("---")
    
    # --- SEÇÃO 2: TOP PERFORMERS ---
    st.markdown("## 🏆 Top Performers - Player Cards")
    top3_data = fmetas.merge(fsdr, on='SDR', how='outer').merge(fvendas, on='SDR', how='outer').fillna(0)
    
    max_realizadas = max(top3_data['Realizadas'].max(), 1)
    max_agendadas = max(top3_data['Agendadas'].max(), 1)
    max_valor = max(top3_data['Valor'].max(), 1)
    
    top3_data['Pitch'] = (top3_data['Realizadas'] / max_realizadas * 100)
    top3_data['Qualif'] = (top3_data['Agendadas'] / max_agendadas * 100)
    # ATUALIZAÇÃO: Conversão interna baseada em Agendadas
    top3_data['Conversão'] = (top3_data['Realizadas'] / top3_data['Agendadas'].replace(0, 1) * 100)
    top3_data['Fechamento'] = (top3_data['Valor'] / max_valor * 100)
    top3_data['ScoreGeral'] = (top3_data['Pitch'] * 0.3 + top3_data['Qualif'] * 0.2 + top3_data['Conversão'] * 0.3 + top3_data['Fechamento'] * 0.2).astype(int)
    
    top3 = top3_data.sort_values(by='ScoreGeral', ascending=False).head(3)
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, (_, row) in enumerate(top3.iterrows()):
        if i < len(cols):
            with cols[i]:
                st.markdown(f"""<div style="background: linear-gradient(135deg, #161B22 0%, #30363D 100%); padding: 20px; border-radius: 20px; text-align: center; border: 3px solid {'#FFD700' if i==0 else '#C0C0C0' if i==1 else '#CD7F32'}; box-shadow: 5px 5px 15px rgba(0,0,0,0.5);"><div style="display: flex; justify-content: space-between; color: white; font-weight: bold; font-size: 1.2vw;"><span>{row['ScoreGeral']}</span><span>ST</span></div><div style="font-size: 1.5vw; font-weight: bold; color: white; margin-top: 10px;">{row['SDR']}</div><hr style="border-color: #4D4D4D; margin: 10px 0;"></div>""", unsafe_allow_html=True)
                categories = ['Pitch', 'Qualif', 'Conversão', 'Fechamento']
                fig = go.Figure(go.Scatterpolar(r=[row['Pitch'], row['Qualif'], row['Conversão'], row['Fechamento']], theta=categories, fill='toself', fillcolor='rgba(0, 204, 150, 0.5)', line=dict(color='#00CC96')))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#30363D'), bgcolor='#161B22'), paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=300, margin=dict(l=40, r=40, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- SEÇÃO 3: TABELA DETALHADA ---
    st.subheader(f"Detalhamento de Performance SDRs (Base: {total_dias_uteis} dias úteis)")
    tabela_final = top3_data[top3_data['SDR'].isin(sdr_sel)].copy()
    
    # ATUALIZAÇÃO DA TABELA: Realizadas / Agendadas
    tabela_final['% Show-up'] = (tabela_final['Realizadas'] / tabela_final['Agendadas'].replace(0, 1) * 100).apply(lambda x: f"{x:.1f}%")
    tabela_final['Média Diária'] = (tabela_final['Agendadas'] / total_dias_uteis).apply(lambda x: f"{x:.2f}")
    
    tabela_disp = tabela_final.copy()
    tabela_disp['Meta_Receita'] = tabela_disp['Meta_Receita'].apply(lambda x: f"$ {x:,.2f}")
    tabela_disp['Valor'] = tabela_disp['Valor'].apply(lambda x: f"$ {x:,.2f}")
    
    cols_view = ['SDR', 'Meta_Reunioes', 'Previstas', 'Agendadas', 'Realizadas', '% Show-up', 'Média Diária', 'Meta_Receita', 'Valor']
    st.dataframe(tabela_disp[cols_view], use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # --- SEÇÃO 4: RAIOX MQL ---
    # (Mantido igual, pois o cálculo de qualidade de MQL não mudou)
    st.header(f"🎯 RaioX MQL: Qualidade do Marketing")
    mql_total = df_mql_filtrado['Entrada MQL'].sum()
    termos_lost = ['Perfil fraco', 'Curioso', 'Sem interesse', 'Cold', 'Não estava interessado']
    df_lost = df_mql_filtrado[df_mql_filtrado['Motivo da perda'].str.contains('|'.join(termos_lost), na=False, case=False)]
    lost_total = len(df_lost)
    qualidade_mkt = ((mql_total - lost_total) / mql_total * 100) if mql_total > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Entrada MQL", int(mql_total))
    k2.metric("Total Leads Lost", lost_total)
    k3.metric("Indice de Aproveitamento", f"{qualidade_mkt:.1f}%")

    st.subheader("Entrada de Ops por Mês")
    if not df_mql_filtrado.empty:
        ops_por_mes = df_mql_filtrado.groupby('Mês')['Entrada MQL'].sum().reset_index()
        cols_meses = st.columns(max(len(ops_por_mes), 1))
        for idx, row in ops_por_mes.iterrows():
            with cols_meses[idx]:
                st.metric(label=f"Ops em {row['Mês']}", value=int(row['Entrada MQL']))
    
    st.subheader("Detalhamento Perdas (Qtd)")
    if not df_lost.empty:
        contagem_motivos = df_lost['Motivo da perda'].value_counts()
        cols_p = st.columns(len(contagem_motivos))
        for i, (motivo, quantidade) in enumerate(contagem_motivos.items()):
            with cols_p[i]:
                st.metric(label=motivo, value=int(quantidade))
else:
    st.info("Conectando aos dados...")
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Metas", layout="wide")

# --- TÍTULO E DESCRIÇÃO ---
st.title("📊 Dashboard de Consolidação de Metas")
st.markdown("Este dashboard lê automaticamente as abas de meses da sua planilha Excel.")

# --- 1. LER E PROCESSAR OS DADOS ---
@st.cache_data # Cache para carregar mais rápido
def carregar_e_processar_dados():
    try:
        # Substitua 'seu_arquivo.xlsx' pelo nome real do seu arquivo
        # sheet_name=None lê todas as abas
        todos_os_meses = pd.read_excel('seu_arquivo.xlsx', sheet_name=None)
        
        lista_resumo = []
        
        for nome_aba, df in todos_os_meses.items():
            # Calcula as métricas somando as colunas
            # .fillna(0) garante que células vazias sejam tratadas como zero
            total_previstas = df['Previstas'].sum()
            total_agendadas = df['Agendadas'].sum()
            total_canceladas = df['Canceladas'].sum()
            total_noshow = df['No-show'].sum()
            total_realizadas = df['Realizadas'].sum()
            
            # Lógica: Não realizadas = Canceladas + No-show
            total_nao_realizadas = total_canceladas + total_noshow
            
            lista_resumo.append({
                'Mês': nome_aba,
                'Previstas': total_previstas,
                'Agendadas': total_agendadas,
                'Realizadas': total_realizadas,
                'Não Realizadas': total_nao_realizadas
            })
            
        return pd.DataFrame(lista_resumo)
    
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return pd.DataFrame() # Retorna um DF vazio em caso de erro

# --- 2. EXIBIR NO DASHBOARD ---
df_consolidado = carregar_e_processar_dados()

if not df_consolidado.empty:
    st.subheader("Resumo Consolidado por Mês")
    
    # Exibe a tabela formatada
    st.dataframe(df_consolidado.style.format({
        'Previstas': '{:,.0f}',
        'Agendadas': '{:,.0f}',
        'Realizadas': '{:,.0f}',
        'Não Realizadas': '{:,.0f}'
    }), use_container_width=True)
    
    # Exemplo de gráfico agrupado
    st.subheader("Visualização Gráfica")
    st.bar_chart(df_consolidado.set_index('Mês'))
else:
    st.warning("Verifique se o arquivo Excel está na mesma pasta que o app.py.")
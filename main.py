import streamlit as st
import pandas as pd
from backend.services.data_engine import DataEngine

# Importa a visualização que acabamos de criar
from views.vis_panorama import render_panorama_mercado

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Painel Estratégico ANS",
    layout="wide",
    initial_sidebar_state="collapsed" # Começa fechado para dar foco ao Top 1
)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(show_spinner="Consolidando dados do mercado...")
def carregar_dados():
    engine = DataEngine()
    return engine.gerar_dataset_mestre()

def main():
    # 1. Carrega Dados
    df_mestre = carregar_dados()
    
    if df_mestre.empty:
        st.error("Erro: Base de dados vazia.")
        st.stop()

    # --- CABEÇALHO ---
    st.title("📊 Monitoramento de Mercado ANS")
    st.markdown("Analise a performance das operadoras de planos de saúde do Brasil.")
    
    # --- NAVEGAÇÃO ENTRE ABAS ---
    # Aqui vamos criando as abas conforme formos desenvolvendo as próximas etapas
    tab1, tab2, tab3 = st.tabs([
        "🌍 Panorama de Mercado (Top Players)", 
        "🎯 Análise da Minha Operadora", 
        "📈 Comparativo de Evolução"
    ])

    # --- ABA 1: PANORAMA (O que fizemos hoje) ---
    with tab1:
        # Chamamos a função do arquivo vis_panorama.py
        # Passamos o DataFrame inteiro, a função lá dentro filtra o que precisa
        render_panorama_mercado(df_mestre)

    # --- ABA 2: Placeholder (Faremos depois) ---
    with tab2:
        st.info("🚧 Em construção: Aqui entrará a análise detalhada da Unimed Caruaru.")

    # --- ABA 3: Placeholder (Faremos depois) ---
    with tab3:
        st.info("🚧 Em construção: Aqui entrarão os gráficos de tendência.")

if __name__ == "__main__":
    main()
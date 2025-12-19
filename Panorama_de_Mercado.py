import streamlit as st
from backend.services.data_engine import DataEngine
from views.vis_panorama import render_panorama_mercado

# Configuração da Página Principal
st.set_page_config(
    page_title="Panorama de Mercado",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARREGAMENTO DE DADOS (CACHEADO) ---
@st.cache_data(show_spinner="Carregando dados do mercado...")
def carregar_dados():
    engine = DataEngine()
    return engine.gerar_dataset_mestre()

def main():
    # 1. Carrega os dados uma única vez
    df_mestre = carregar_dados()

    if df_mestre.empty:
        st.error("Erro crítico: A base de dados retornou vazia. Verifique a conexão.")
        st.stop()

    # 2. Renderiza a Visualização de Panorama (Home Page)
    # O Streamlit detectará automaticamente a pasta 'pages/' e criará o menu lateral
    # colocando este arquivo (main.py) como o primeiro item do menu.
    render_panorama_mercado(df_mestre)

if __name__ == "__main__":
    main()
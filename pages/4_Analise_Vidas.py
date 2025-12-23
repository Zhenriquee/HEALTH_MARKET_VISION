import streamlit as st
from backend.services.data_engine import DataEngine
from views.vis_vidas import render_analise_vidas

st.set_page_config(
    page_title="Análise de Vidas",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados():
    engine = DataEngine()
    return engine.gerar_dataset_mestre()

def main():
    df_mestre = carregar_dados()
    
    if not df_mestre.empty:
        render_analise_vidas(df_mestre)
    else:
        st.error("Erro ao carregar dados.")

if __name__ == "__main__":
    main()
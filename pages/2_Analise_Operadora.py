import streamlit as st
from backend.services.data_engine import DataEngine
from views.vis_analise import render_analise

# Configuração da Página Secundária
st.set_page_config(
    page_title="Análise Detalhada",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reutiliza o cache do main.py (Streamlit compartilha cache entre páginas)
@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados():
    engine = DataEngine()
    return engine.gerar_dataset_mestre()

def main():
    df_mestre = carregar_dados()
    
    if not df_mestre.empty:
        # Chama a função de visualização que criamos no passo anterior
        render_analise(df_mestre)
    else:
        st.error("Erro ao carregar dados.")

if __name__ == "__main__":
    main()
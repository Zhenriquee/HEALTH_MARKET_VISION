import streamlit as st

def render_header(operadora_data, rank_geral, score):
    """Renderiza o cabeçalho padrão com Rank, Dados Cadastrais e Barra de Score."""
    
    rep_nome = str(operadora_data.get('representante') or 'Não Informado').title()
    modalidade = operadora_data.get('modalidade', 'N/A')
    cnpj = operadora_data.get('cnpj', 'N/A')
    razao_social = operadora_data.get('razao_social', 'Operadora')

    with st.container():
        c_rank, c_info = st.columns([1, 6])
        
        with c_rank:
            # Cor Dourada para Top 3, Azul para o resto
            if isinstance(rank_geral, int) and rank_geral <= 3:
                cor_rank = "#DAA520" 
            else:
                cor_rank = "#1f77b4"
            
            rank_display = f"#{rank_geral}" if rank_geral != "-" else "-"
            st.markdown(f"<h1 style='text-align: center; color: {cor_rank}; font-size: 60px; margin: 0;'>{rank_display}</h1>", unsafe_allow_html=True)
            st.caption("Rank Geral")
            
        with c_info:
            st.markdown(f"## {razao_social}")
            st.markdown(f"""
            **CNPJ:** {cnpj} | **Modalidade:** {modalidade}  
            👤 **Gestão:** {rep_nome}
            """)
            st.progress(int(score) / 100, text=f"Power Score: {score:.1f}/100")
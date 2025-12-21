import streamlit as st

def render_glossary():
    with st.expander("📚 Glossário de Análise"):
        t_kpi, t_comp, t_estr = st.tabs(["KPIs", "Comparativos", "Estratégia"])
        
        with t_kpi:
            st.markdown("""
            **Entenda os Indicadores Básicos:**
            * **Power Score (0-100):** Nota geral de qualidade.
            * **Vidas (Carteira):** Total de beneficiários ativos.
            * **Receita (Financeiro):** Faturamento trimestral total.
            * **Ticket Médio:** Receita / Vidas.
            """)
        with t_comp:
            st.markdown("""
            **Entenda as Variações:**
            * **QoQ (Quarter over Quarter):** Comparação com o trimestre anterior.
            * **YoY (Year over Year):** Comparação com o mesmo trimestre do ano passado.
            """)
        with t_estr:
            st.markdown("""
            **Inteligência de Mercado:**
            * **Spread (Alpha):** Diferença entre crescimento da operadora e a média do mercado.
            * **Share of Brand:** Tamanho da operadora dentro do seu grupo econômico.
            """)
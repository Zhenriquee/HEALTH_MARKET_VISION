import streamlit as st

def render_glossary():
    with st.expander("📚 Glossário de Análise"):
        t_kpi, t_comp, t_estr, t_calc = st.tabs(["KPIs", "Comparativos", "Estratégia", "🧮 Cálculos (p.p.)"])
        
        with t_kpi:
            st.markdown("""
            **Entenda os Indicadores Básicos:**
            * **Power Score (0-100):** Nota geral de qualidade (40% Vidas, 40% Receita, 20% Performance).
            * **Vidas (Carteira):** Total de beneficiários ativos.
            * **Receita (Financeiro):** Faturamento trimestral total (Conta 31).
            * **Ticket Médio:** Receita / Vidas.
            """)
        with t_comp:
            st.markdown("""
            **Entenda as Variações:**
            * **QoQ (Quarter over Quarter):** Comparação com o trimestre imediatamente anterior.
            * **YoY (Year over Year):** Comparação com o mesmo trimestre do ano passado.
            """)
        with t_estr:
            st.markdown("""
            **Inteligência de Mercado:**
            * **Spread (Alpha):** Diferença entre crescimento da operadora e a média do mercado.
                * 🟩 **Verde:** Cresceu acima da média.
                * 🟥 **Vermelho:** Cresceu abaixo da média.
            * **Share of Brand:** Tamanho da operadora dentro do seu grupo econômico.
            """)
        
        # --- NOVO TÓPICO SOLICITADO ---
        with t_calc:
            st.markdown("""
            ### 📐 O que é Ponto Percentual (p.p.)?
            É a unidade usada para descrever a **diferença aritmética** entre duas porcentagens.
            
            **A Fórmula:**
            $$Spread = \% Crescimento Operadora - \% Crescimento Mercado$$ # type: ignore # pyright: ignore[reportInvalidStringEscapeSequence] # pyright: ignore[reportInvalidStringEscapeSequence] # pyright: ignore[reportInvalidStringEscapeSequence] # type: ignore # type: ignore
            
            **💡 Exemplo Prático:**
            Imagine o seguinte cenário no trimestre:
            1. O Mercado cresceu **10%**.
            2. Sua Operadora cresceu **15%**.
            
            * **Cálculo Errado:** Dizer que cresceu 50% a mais (15 é 50% maior que 10). Isso confunde.
            * **Cálculo Correto (p.p.):** $15\% - 10\% = 5 p.p.$ # type: ignore # pyright: ignore[reportInvalidStringEscapeSequence] # pyright: ignore[reportInvalidStringEscapeSequence]
            
            Isso significa que sua operadora ganhou **5 pontos percentuais** de vantagem ("terreno") sobre a média da concorrência.
            """)
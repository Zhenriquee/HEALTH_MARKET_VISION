import streamlit as st

def render_glossary():
    with st.expander("📚 Glossário de Análise"):
        t_kpi, t_comp, t_estr, t_calc = st.tabs(["KPIs", "Comparativos", "Estratégia", "🧮 Cálculos"])
        
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
            **Indicadores de Grupo:**
            * **Média Cresc. Receita (Grupo):** É a mediana do crescimento financeiro de todas as operadoras do mesmo grupo.
                * *Para que serve?* Define o ritmo "normal" do grupo. Se você cresceu 10% e a média do grupo foi 15%, você está puxando o grupo para baixo.
            """)
        
        # --- NOVO TÓPICO SOLICITADO ---
        with t_calc:
            st.markdown("""
            ### 📐 Ponto Percentual (p.p.)
            Diferença aritmética entre duas porcentagens.
            *Ex: Se você cresceu 15% e o mercado 10%, seu ganho real foi de 5 p.p.*
            
            ### ⚡ Volatilidade (Risco)
            Mede a instabilidade do fluxo de caixa da operadora.
            
            **Como é calculado:**
            Calculamos o **Desvio Padrão** das variações percentuais de receita dos últimos **8 trimestres (2 anos)**.
            
            **Interpretação:**
            * **Baixa (< 5%):** Receita previsível e estável.
            * **Alta (> 15%):** Receita oscila muito (sazonalidade forte ou perda/ganho brusco de contratos).
            """)
import streamlit as st
import pandas as pd

def aplicar_estilo_top30(df):
    """Aplica cores nas linhas do ranking."""
    def colorir_linhas(row):
        rank = row['Rank']
        if rank <= 10:
            color = '#d4edda' # Verde (Líderes)
        elif rank <= 20:
            color = '#fff3cd' # Amarelo (Intermediários)
        elif rank <= 30:
            color = '#ffeeba' # Laranja (Atenção)
        else:
            color = 'white'
        return [f'background-color: {color}; color: black'] * len(row)

    return df.style.apply(colorir_linhas, axis=1)

def calcular_power_score(df):
    """
    Cria um índice de 0 a 100 ponderando Vidas (50%) e Receita (50%).
    Calculado com base no MÁXIMO do contexto atual (filtro selecionado).
    """
    df_calc = df.copy()
    
    if df_calc.empty:
        return df_calc

    # Máximos do contexto atual (Se filtrou só cooperativa, o max será a maior cooperativa)
    max_vidas = df_calc['NR_BENEF_T'].max()
    max_receita = df_calc['VL_SALDO_FINAL'].max()
    
    # Evita divisão por zero
    if max_vidas == 0 or pd.isna(max_vidas): max_vidas = 1
    if max_receita == 0 or pd.isna(max_receita): max_receita = 1

    # Cálculo dos Scores Parciais
    df_calc['Score_Vidas'] = df_calc['NR_BENEF_T'] / max_vidas
    df_calc['Score_Receita'] = df_calc['VL_SALDO_FINAL'] / max_receita
    
    # Média Ponderada
    df_calc['Power_Score'] = (0.5 * df_calc['Score_Vidas'] + 0.5 * df_calc['Score_Receita']) * 100
    
    return df_calc.sort_values(by='Power_Score', ascending=False).reset_index(drop=True)

def render_panorama_mercado(df_mestre):
    """
    Renderiza a aba principal com Filtros, Explicação do Score e Ranking.
    """
    # 1. Preparação dos Dados (Último Trimestre)
    ultimo_trimestre = df_mestre['ID_TRIMESTRE'].max()
    df_atual = df_mestre[df_mestre['ID_TRIMESTRE'] == ultimo_trimestre].copy()

    # --- ÁREA DE CONTROLES (FILTROS) ---
    with st.container():
        col_filtro, col_info = st.columns([2, 1])
        
        with col_filtro:
            # Pega lista única de modalidades e remove nulos
            modalidades_disponiveis = sorted(df_atual['modalidade'].dropna().unique())
            
            sel_modalidade = st.multiselect(
                "📌 Filtrar por Modalidade:",
                options=modalidades_disponiveis,
                placeholder="Selecione para filtrar (Vazio = Todas)",
                help="Selecione uma ou mais modalidades para recalcular o ranking."
            )
        
        with col_info:
            # Explicação do Score (Dropdown para não poluir)
            with st.expander("ℹ️ Como o Score é calculado?"):
                st.markdown("""
                O **Power Score** (0 a 100) define a força da operadora equilibrando tamanho e faturamento.
                
                $$
                Score = (0.5 \\times \\frac{Vidas}{MaxVidas}) + (0.5 \\times \\frac{Receita}{MaxReceita}) \\times 100
                $$
                
                * **Vidas:** Quantidade de beneficiários ativos.
                * **Receita:** Faturamento trimestral (Conta 31).
                * **Max:** O maior valor encontrado **no filtro atual**.
                """)

    # 2. Aplicação do Filtro
    if sel_modalidade:
        df_atual = df_atual[df_atual['modalidade'].isin(sel_modalidade)]
        texto_contexto = f"Ranking: {', '.join(sel_modalidade)}"
    else:
        texto_contexto = "Ranking: Todo o Mercado"

    # Verifica se sobrou dado após filtro
    if df_atual.empty:
        st.warning("Nenhuma operadora encontrada com os filtros selecionados.")
        return

    # 3. Cálculo do Ranking (Recalcula Maximos e Scores baseados no filtro)
    df_ranqueado = calcular_power_score(df_atual)
    df_ranqueado['Rank'] = df_ranqueado.index + 1

    # --- VISUALIZAÇÃO DO LÍDER ---
    top_1 = df_ranqueado.iloc[0]
    
    st.divider()
    st.caption(f"📅 Dados referentes a: **{ultimo_trimestre}** | 🔍 {texto_contexto}")

    # Container estilizado
    with st.container():
        col_logo, col_nome = st.columns([1, 5])
        with col_logo:
            st.markdown(f"<h1 style='text-align: center; color: #DAA520; font-size: 50px;'>#1</h1>", unsafe_allow_html=True)
        with col_nome:
            st.markdown(f"### {top_1['razao_social']}")
            st.markdown(f"**Modalidade:** {top_1['modalidade']}")
            
            # Barra de progresso visual para o Score
            score_val = top_1['Power_Score']
            st.progress(int(score_val) / 100, text=f"Power Score: {score_val:.1f}/100")

        # Métricas do Líder
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 Vidas", f"{int(top_1['NR_BENEF_T']):,}".replace(",", "."))
        c2.metric("💰 Receita", f"R$ {top_1['VL_SALDO_FINAL']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        ticket = top_1['VL_SALDO_FINAL'] / top_1['NR_BENEF_T'] if top_1['NR_BENEF_T'] > 0 else 0
        c3.metric("📊 Ticket Médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Detalhes extras
        cidade_full = f"{str(top_1.get('cidade', '')).title()} - {top_1.get('uf', '')}"
        rep_full = str(top_1.get('representante', 'N/A')).title()
        c4.metric("📍 Sede", cidade_full, delta=rep_full, delta_color="off")

    st.divider()
    

    # --- TABELA TOP 30 ---
    st.subheader(f"🏆 Top 30 Operadoras - {texto_contexto}")
    
    # Seleção e Renomeação
    cols_view = ['Rank', 'razao_social', 'modalidade', 'Power_Score', 'NR_BENEF_T', 'VL_SALDO_FINAL']
    df_top30 = df_ranqueado.head(30)[cols_view].copy()
    df_top30.columns = ['Rank', 'Operadora', 'Modalidade', 'Score', 'Vidas', 'Receita (R$)']

    # Estilização
    styler = aplicar_estilo_top30(df_top30)
    styler.format({
        'Score': "{:.1f}",
        'Vidas': "{:,.0f}", 
        'Receita (R$)': "R$ {:,.2f}"
    })

    st.dataframe(styler, use_container_width=True, height=800, hide_index=True)
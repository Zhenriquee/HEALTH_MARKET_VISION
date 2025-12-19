import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Imports de Backend
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_power_score

def render_analise(df_mestre):
    # --- 1. CONFIGURAÇÃO (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Configuração da Análise")
        
        # A. Filtro de Trimestre
        opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
        sel_trimestre = st.selectbox("📅 Trimestre de Análise:", options=opcoes_trimestre)
        
        st.markdown("---")
        
        # B. Filtro de Modalidade
        st.subheader("🔍 Filtros de Busca")
        opcoes_modalidade = sorted(df_mestre['modalidade'].dropna().unique())
        sel_modalidade = st.selectbox(
            "1️⃣ Modalidade:",
            options=["Todas"] + opcoes_modalidade,
            index=0
        )
        
        # Cria DF base filtrado
        df_base_filtro = df_mestre.copy()
        if sel_modalidade != "Todas":
            df_base_filtro = df_base_filtro[df_base_filtro['modalidade'] == sel_modalidade]

        # C. Filtro de Grupo/Marca
        df_base_filtro['Marca'] = df_base_filtro['razao_social'].apply(extrair_marca)
        lista_marcas = sorted(df_base_filtro['Marca'].unique())
        
        sel_grupo = st.selectbox(
            "2️⃣ Filtrar por Grupo/Marca:",
            options=["Todos"] + lista_marcas,
            index=0
        )

        # D. Seleção de Operadora
        if sel_grupo != "Todos":
            df_base_filtro = df_base_filtro[df_base_filtro['Marca'] == sel_grupo]
            
        df_op_unicas = df_base_filtro[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()

        opcoes_map = {
            f"{row['razao_social']} ({row['cnpj']})": row['ID_OPERADORA'] 
            for _, row in df_op_unicas.iterrows()
        }
        
        # Default: Unimed Caruaru
        default_cnpj_root = "340952"
        index_default = 0
        lista_opcoes = sorted(list(opcoes_map.keys()))
        
        for i, op in enumerate(lista_opcoes):
            if default_cnpj_root in opcoes_map[op] or "UNIMED CARUARU" in op:
                index_default = i
                break
        
        if index_default >= len(lista_opcoes): index_default = 0

        if not lista_opcoes:
            st.warning("Nenhuma operadora encontrada com esses filtros.")
            return

        sel_operadora_nome = st.selectbox(
            "3️⃣ Selecione a Operadora:",
            options=lista_opcoes,
            index=index_default
        )
        
        id_operadora_sel = opcoes_map[sel_operadora_nome]
        
        st.markdown("---")

        with st.expander("📚 Glossário desta Tela"):
            st.markdown("""
            **Ranks:**
            * **Rank Geral:** Posição entre TODAS as operadoras do Brasil.
            * **Rank Grupo:** Posição dentro da marca selecionada.
            
            **Comparativos:**
            * **QoQ:** Trimestre atual vs Trimestre anterior.
            * **YoY:** Trimestre atual vs Mesmo trimestre do ano passado.
            """)

    # --- 2. PROCESSAMENTO ---
    
    # Dados do Trimestre Atual
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
    operadora_row = df_tri[df_tri['ID_OPERADORA'] == str(id_operadora_sel)]
    
    if operadora_row.empty:
        st.error(f"A operadora selecionada não possui dados no trimestre {sel_trimestre}.")
        return

    op_dados = operadora_row.iloc[0]
    
    # Cálculos de Score e Ranking Global
    df_tri_scored = calcular_power_score(df_tri)
    df_tri_scored['Rank_Geral'] = df_tri_scored['Power_Score'].rank(ascending=False, method='min')
    
    # Cálculos de Ranking no Grupo
    marca_atual = extrair_marca(op_dados['razao_social'])
    df_tri_scored['Marca_Temp'] = df_tri_scored['razao_social'].apply(extrair_marca)
    df_grupo_scored = df_tri_scored[df_tri_scored['Marca_Temp'] == marca_atual].copy()
    df_grupo_scored['Rank_Grupo'] = df_grupo_scored['Power_Score'].rank(ascending=False, method='min')

    # Recupera métricas finais
    try:
        dados_finais = df_tri_scored[df_tri_scored['ID_OPERADORA'] == str(id_operadora_sel)].iloc[0]
        rank_geral = int(dados_finais['Rank_Geral'])
        rank_grupo = int(df_grupo_scored[df_grupo_scored['ID_OPERADORA'] == str(id_operadora_sel)]['Rank_Grupo'].values[0])
        total_grupo = len(df_grupo_scored)
        score_real = dados_finais['Power_Score']
    except:
        score_real, rank_geral, rank_grupo = 0, 0, 0
        total_grupo = 0

    kpis = calcular_variacoes_operadora(df_mestre, id_operadora_sel, sel_trimestre)
    insights_marca = analisar_performance_marca(df_tri, op_dados)
    
    # Prepara strings de gestão
    rep_nome = str(op_dados.get('representante') or 'Não Informado').title()
    rep_cargo = str(op_dados.get('cargo_representante') or '').title()
    cidade = str(op_dados.get('cidade') or '').title()
    uf = str(op_dados.get('uf') or '').title()


    # --- 3. RENDERIZAÇÃO ---

    # --- CARD DE CABEÇALHO ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | Grupo: **{marca_atual}**")
    
    with st.container():
        c_rank, c_info = st.columns([1, 6])
        
        # Coluna do Rank (Big Number)
        with c_rank:
            cor_rank = "#DAA520" if rank_geral <= 3 else "#1f77b4"
            st.markdown(f"<h1 style='text-align: center; color: {cor_rank}; font-size: 60px; margin: 0;'>#{rank_geral}</h1>", unsafe_allow_html=True)
            st.caption("Rank Geral")
            
        # Coluna das Informações
        with c_info:
            st.markdown(f"## {op_dados['razao_social']}")
            
            # ATUALIZAÇÃO AQUI: Representante abaixo do CNPJ
            st.markdown(f"""
            **CNPJ:** {op_dados['cnpj']} | **Modalidade:** {op_dados['modalidade']}  
            👤 **Gestão:** {rep_nome} — *{rep_cargo}* |📍 **Sede**: {cidade} / {uf} 
            """)
            
            # Barra de Score
            st.progress(int(score_real) / 100, text=f"Power Score: {score_real:.1f}/100")

    st.divider()

    # --- LINHA DE KPIs ---
    k1, k2, k3, k4 = st.columns(4)

    # 1. Vidas
    k1.metric(
        "👥 Vidas", 
        f"{int(kpis['Vidas']):,}".replace(",", "."), 
        delta=f"{kpis['Var_Vidas_QoQ']:.1%} (QoQ)",
        delta_color="normal"
    )
    
    # 2. Receita
    k2.metric(
        "💰 Receita", 
        f"R$ {kpis['Receita']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta=f"{kpis['Var_Receita_QoQ']:.1%} (QoQ)",
        delta_color="normal"
    )

    # 3. Ticket
    k3.metric(
        "📊 Ticket Médio", 
        f"R$ {kpis['Ticket']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    
    # 4. Rank Grupo (Limpamos a gestão daqui pois já está no header)
    k4.metric(
        f"🏢 Rank {marca_atual}", 
        f"#{rank_grupo}",
        f"de {total_grupo} ops",
        delta_color="off"
    )

    st.divider()

    # --- BLOCO 1: MATRIZ DE COMPARAÇÃO ---
    st.subheader("1. Matriz de Performance (Comparativo)")
    
    data_matrix = {
        "Indicador": ["👥 Carteira de Vidas", "💰 Receita Trimestral (R$)", "🎟️ Ticket Médio (R$)"],
        f"Resultado ({sel_trimestre})": [
            f"{int(kpis['Vidas']):,}".replace(",", "."),
            f"R$ {kpis['Receita']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            f"R$ {kpis['Ticket']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ],
        "vs Trimestre Anterior (QoQ)": [
            f"{kpis['Var_Vidas_QoQ']:+.2%}",
            f"{kpis['Var_Receita_QoQ']:+.2%}",
            "-" 
        ],
        "vs Ano Anterior (YoY)": [
            f"{kpis['Var_Vidas_YoY']:+.2%}",
            f"{kpis['Var_Receita_YoY']:+.2%}",
            "-"
        ]
    }
    df_matrix = pd.DataFrame(data_matrix)
    
    st.dataframe(
        df_matrix,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Indicador": st.column_config.TextColumn("KPI", width="medium"),
            f"Resultado ({sel_trimestre})": st.column_config.TextColumn("Resultado Atual", width="medium"),
            "vs Trimestre Anterior (QoQ)": st.column_config.TextColumn("Tendência Curta (QoQ)", width="small"),
            "vs Ano Anterior (YoY)": st.column_config.TextColumn("Cresc. Real (YoY)", width="small")
        }
    )

    st.divider()

    # --- BLOCO 2: GRÁFICO ---
    st.subheader("2. Evolução Histórica (Receita vs Vidas)")
    
    df_hist = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora_sel)].sort_values('ID_TRIMESTRE')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['NR_BENEF_T'],
        name='Vidas', line=dict(color='#1f77b4', width=3),
        hovertemplate='%{y:,.0f} Vidas'
    ))
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['VL_SALDO_FINAL'],
        name='Receita (R$)', line=dict(color='#2ca02c', width=3, dash='dot'),
        yaxis='y2', hovertemplate='R$ %{y:,.2f}'
    ))
    fig.update_layout(
        title="", xaxis=dict(title="Trimestre"),
        yaxis=dict(
            title=dict(text="Quantidade de Vidas", font=dict(color="#1f77b4")),
            tickfont=dict(color="#1f77b4"), tickformat=",.0f"
        ),
        yaxis2=dict(
            title=dict(text="Receita (R$)", font=dict(color="#2ca02c")),
            tickfont=dict(color="#2ca02c"), overlaying='y', side='right',
            tickprefix="R$ ", tickformat=",.2s"
        ),
        legend=dict(x=0, y=1.1, orientation='h'), hovermode="x unified", height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- BLOCO 3: RANKING DO GRUPO ---
    st.subheader(f"3. Ranking do Grupo: {marca_atual}")
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Participação no Grupo", f"{insights_marca['Share_of_Brand']:.2f}%")
    col_m2.metric("Média Cresc. Vidas (Grupo)", f"{insights_marca['Media_Cresc_Vidas_Grupo']:.2%}")

    with st.expander(f"📋 Ver Ranking Completo: {marca_atual}", expanded=True):
        df_view_grupo = df_grupo_scored.copy().sort_values('Power_Score', ascending=False)
        df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)
        
        df_view_grupo = df_view_grupo[[
            '#', 'razao_social', 'uf', 'Power_Score', 'NR_BENEF_T', 'VL_SALDO_FINAL'
        ]]
        df_view_grupo.columns = ['#', 'Operadora', 'UF', 'Score', 'Vidas', 'Receita (R$)']
        
        st.dataframe(
            df_view_grupo.style.format({
                'Score': '{:.1f}',
                'Vidas': '{:,.0f}',
                'Receita (R$)': 'R$ {:,.2f}'
            }),
            use_container_width=True,
            height=400,
            hide_index=True
        )
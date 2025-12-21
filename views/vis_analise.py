import streamlit as st
import pandas as pd
import numpy as np

# Imports de Backend
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_power_score

# Imports dos Novos Componentes
from views.components.header import render_header
from views.components.metrics import render_kpi_row
from views.components.charts import render_spread_chart, render_evolution_chart
from views.components.tables import render_ranking_table
from views.components.glossary import render_glossary

def render_analise(df_mestre):
    # --- 1. CONFIGURAÇÃO (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Configuração da Análise")
        
        # Filtros (Mantidos aqui pois são específicos da página)
        opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
        sel_trimestre = st.selectbox("📅 Trimestre de Análise:", options=opcoes_trimestre)
        st.markdown("---")
        
        st.subheader("🔍 Filtros de Busca")
        
        df_base_filtro = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        opcoes_modalidade = sorted(df_base_filtro['modalidade'].dropna().unique())
        sel_modalidade = st.selectbox("1️⃣ Modalidade:", options=["Todas"] + opcoes_modalidade, index=0)
        
        if sel_modalidade != "Todas":
            df_base_filtro = df_base_filtro[df_base_filtro['modalidade'] == sel_modalidade]

        # Tratamento de Marca
        df_base_filtro['Marca_Temp'] = df_base_filtro['razao_social'].apply(extrair_marca)
        df_mestre['Marca_Temp'] = df_mestre['razao_social'].apply(extrair_marca)

        lista_marcas = sorted(df_base_filtro['Marca_Temp'].unique())
        sel_grupo = st.selectbox("2️⃣ Filtrar por Grupo/Marca:", options=["Todos"] + lista_marcas, index=0)

        if sel_grupo != "Todos":
            df_base_filtro = df_base_filtro[df_base_filtro['Marca_Temp'] == sel_grupo]
            
        df_op_unicas = df_base_filtro[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        opcoes_map = {f"{row['razao_social']} ({row['cnpj']})": row['ID_OPERADORA'] for _, row in df_op_unicas.iterrows()}
        
        # Default Logic
        default_cnpj_root = "340952"
        index_default = 0
        lista_opcoes = sorted(list(opcoes_map.keys()))
        for i, op in enumerate(lista_opcoes):
            if default_cnpj_root in opcoes_map[op] or "UNIMED CARUARU" in op:
                index_default = i; break
        if index_default >= len(lista_opcoes): index_default = 0

        if not lista_opcoes:
            st.warning("Nenhuma operadora encontrada."); return

        sel_operadora_nome = st.selectbox("3️⃣ Selecione a Operadora:", options=lista_opcoes, index=index_default)
        id_operadora_sel = str(opcoes_map[sel_operadora_nome])
        st.markdown("---")

        # Componente Glossário
        render_glossary()

    # --- 2. PROCESSAMENTO ---
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
    df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
    
    operadora_row = df_tri[df_tri['ID_OPERADORA'] == id_operadora_sel]
    if operadora_row.empty: st.error(f"Sem dados."); return

    op_dados = operadora_row.iloc[0]
    marca_atual = extrair_marca(op_dados['razao_social'])
    
    # Ranks
    df_tri_scored = calcular_power_score(df_tri)
    df_tri_scored['Rank_Geral'] = df_tri_scored['Power_Score'].rank(ascending=False, method='min')
    df_tri_scored['ID_OPERADORA'] = df_tri_scored['ID_OPERADORA'].astype(str)
    
    df_tri_scored['Marca_Temp'] = df_tri_scored['razao_social'].apply(extrair_marca)
    df_grupo_scored = df_tri_scored[df_tri_scored['Marca_Temp'] == marca_atual].copy()
    df_grupo_scored['Rank_Grupo'] = df_grupo_scored['Power_Score'].rank(ascending=False, method='min')
    
    total_grupo = len(df_grupo_scored)

    try:
        dados_geral = df_tri_scored[df_tri_scored['ID_OPERADORA'] == id_operadora_sel]
        rank_geral = int(dados_geral.iloc[0]['Rank_Geral']) if not dados_geral.empty else "-"
        score_real = dados_geral.iloc[0]['Power_Score'] if not dados_geral.empty else 0
        
        dados_grupo = df_grupo_scored[df_grupo_scored['ID_OPERADORA'] == id_operadora_sel]
        rank_grupo = int(dados_grupo.iloc[0]['Rank_Grupo']) if not dados_grupo.empty else "-"
    except:
        score_real, rank_geral, rank_grupo = 0, "-", "-"

    kpis = calcular_variacoes_operadora(df_mestre, id_operadora_sel, sel_trimestre)
    insights_marca = analisar_performance_marca(df_tri, op_dados)

    # --- 3. RENDERIZAÇÃO (AGORA MUITO MAIS LIMPA) ---

    st.caption(f"📅 Referência: **{sel_trimestre}** | Grupo: **{marca_atual}**")
    
    # 1. Componente Header
    render_header(op_dados, rank_geral, score_real)

    st.divider()

    # 2. Componente KPI Row
    render_kpi_row(kpis, rank_grupo_info=(rank_grupo, total_grupo, marca_atual))

    st.divider()

    # 3. Matriz (Ainda mantida aqui pois é muito específica, ou poderia virar componente se usada em outro lugar)
    st.subheader("1. Matriz de Performance (Valores e Variações)")
    def fmt_val_delta(valor, delta, is_money=False):
        if is_money: val_str = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else: val_str = f"{int(valor):,}".replace(",", ".")
        return f"{val_str} ({delta:+.2%})"

    data_matrix = {
        "Indicador": ["👥 Carteira de Vidas", "💰 Receita Trimestral (R$)", "🎟️ Ticket Médio (R$)"],
        f"Resultado ({sel_trimestre})": [
            f"{int(kpis['Vidas']):,}".replace(",", "."), # type: ignore
            f"R$ {kpis['Receita']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), # pyright: ignore[reportOptionalSubscript]
            f"R$ {kpis['Ticket']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") # type: ignore
        ],
        f"vs Anterior ({kpis['Ref_QoQ']})": [ # type: ignore
            fmt_val_delta(kpis['Val_Vidas_QoQ'], kpis['Var_Vidas_QoQ']), # type: ignore
            fmt_val_delta(kpis['Val_Receita_QoQ'], kpis['Var_Receita_QoQ'], True), "-"  # type: ignore
        ],
        f"vs Ano Passado ({kpis['Ref_YoY']})": [ # type: ignore
            fmt_val_delta(kpis['Val_Vidas_YoY'], kpis['Var_Vidas_YoY']), # type: ignore
            fmt_val_delta(kpis['Val_Receita_YoY'], kpis['Var_Receita_YoY'], True), "-" # type: ignore
        ]
    }
    st.dataframe(pd.DataFrame(data_matrix), use_container_width=True, hide_index=True)
    st.divider()

    # 4. Componente Gráficos de Spread
    st.subheader("2. Performance Relativa (Spread)")
    st.markdown("Comparativo do crescimento da operadora vs **Mediana do Mercado** e **Mediana do Grupo**.")
    tab_fin, tab_vol = st.tabs(["💰 Financeiro (Receita)", "👥 Volume (Vidas)"])

    with tab_fin:
        c1, c2 = st.columns(2)
        with c1:
            fig = render_spread_chart(df_mestre, id_operadora_sel, op_dados['razao_social'], "Receita", "Mercado Geral")
            if fig: st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = render_spread_chart(df_mestre, id_operadora_sel, op_dados['razao_social'], "Receita", "Grupo", marca_atual)
            if fig: st.plotly_chart(fig, use_container_width=True)

    with tab_vol:
        c1, c2 = st.columns(2)
        with c1:
            fig = render_spread_chart(df_mestre, id_operadora_sel, op_dados['razao_social'], "Vidas", "Mercado Geral")
            if fig: st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = render_spread_chart(df_mestre, id_operadora_sel, op_dados['razao_social'], "Vidas", "Grupo", marca_atual)
            if fig: st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

    # 5. Componente Evolução Histórica
    st.subheader("3. Evolução Histórica (Tendência)")
    fig_hist = render_evolution_chart(df_mestre, id_operadora_sel)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    st.divider()

    # 6. Componentes Tabelas
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Participação no Grupo (Share)", f"{insights_marca['Share_of_Brand']:.2f}%")
    col_m2.metric("Média Cresc. Vidas (Grupo)", f"{insights_marca['Media_Cresc_Vidas_Grupo']:.2%}")

    df_view_grupo = df_grupo_scored.copy().sort_values('Power_Score', ascending=False)
    df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)
    
    # Renderiza Tabela Grupo
    render_ranking_table(
        df_view_grupo, 
        titulo=f"4. Ranking do Grupo: {marca_atual}", 
        subtitulo=f"Listagem das operadoras do grupo **{marca_atual}**."
    )
    
    st.divider()

    df_view_geral = df_tri_scored.copy().sort_values('Power_Score', ascending=False)
    df_view_geral['#'] = range(1, len(df_view_geral) + 1)
    
    # Renderiza Tabela Geral
    render_ranking_table(
        df_view_geral, 
        titulo="5. Ranking de Mercado (Geral)", 
        subtitulo="Comparativo com **todas as operadoras**."
    )
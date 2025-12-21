import streamlit as st
import pandas as pd

# Imports Backend
from backend.analytics.filtros_mercado import filtrar_por_modalidade
from backend.analytics.calculadora_score import calcular_power_score
from backend.analytics.brand_intelligence import extrair_marca

# Imports Components
from views.components.header import render_header
from views.components.metrics import render_kpi_row
from views.components.charts import render_spread_chart
# IMPORTANTE: Importamos a nova função de tabela estilizada aqui
from views.components.tables import render_styled_ranking_table 
from views.components.glossary import render_glossary

def render_panorama_mercado(df_mestre):
    # --- SIDEBAR ---
    with st.sidebar:
        st.divider()
        st.header("⚙️ Filtros & Configuração")
        
        opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
        sel_trimestre = st.selectbox("📅 Selecione o Trimestre:", options=opcoes_trimestre, index=0)

        st.markdown("---")
        opcoes_modalidade = sorted(df_mestre['modalidade'].dropna().unique())
        sel_modalidade = st.multiselect("📌 Filtrar por Modalidade:", options=opcoes_modalidade, placeholder="Todas as Modalidades")
        
        st.markdown("---")
        render_glossary()

    # --- PROCESSAMENTO ---
    df_mercado_filtrado = filtrar_por_modalidade(df_mestre, sel_modalidade)
    if df_mercado_filtrado.empty: st.warning("Sem dados."); return

    df_snapshot = df_mercado_filtrado[df_mercado_filtrado['ID_TRIMESTRE'] == sel_trimestre].copy()
    if df_snapshot.empty: st.warning("Sem dados para o trimestre."); return

    # Ranking
    df_ranqueado = calcular_power_score(df_snapshot)
    df_ranqueado['Rank_Geral'] = df_ranqueado['Power_Score'].rank(ascending=False, method='min')
    df_ranqueado['#'] = range(1, len(df_ranqueado) + 1)
    
    # Líder
    top_1 = df_ranqueado.iloc[0]
    id_top_1 = str(top_1['ID_OPERADORA'])
    
    texto_contexto = f"Filtro: {', '.join(sel_modalidade)}" if sel_modalidade else "Mercado Total"

    kpis_lider = {
        'Vidas': top_1['NR_BENEF_T'],
        'Receita': top_1['VL_SALDO_FINAL'],
        'Ticket': top_1['VL_SALDO_FINAL'] / top_1['NR_BENEF_T'] if top_1['NR_BENEF_T'] > 0 else 0,
        'Var_Vidas_QoQ': top_1['VAR_PCT_VIDAS'],
        'Var_Receita_QoQ': top_1['VAR_PCT_RECEITA']
    }

    # --- RENDERIZAÇÃO ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | 🔍 {texto_contexto}")

    # 1. Header Líder
    render_header(top_1, 1, top_1['Power_Score'])

    st.divider()
    
    # 2. KPIs Líder
    local_sede = f"{str(top_1.get('cidade','')).title()}/{str(top_1.get('uf',''))}"
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("👥 Vidas", f"{int(kpis_lider['Vidas']):,}".replace(",", "."), delta=f"{kpis_lider['Var_Vidas_QoQ']:.2%} (Vol)")
    with k2: st.metric("💰 Receita", f"R$ {kpis_lider['Receita']:,.2f}", delta=f"{kpis_lider['Var_Receita_QoQ']:.2%} (Fin)")
    with k3: st.metric("📊 Ticket Médio", f"R$ {kpis_lider['Ticket']:,.2f}")
    with k4: st.metric("📍 Sede", local_sede)
    
    st.divider()

    # 3. Gráficos Spread
    st.subheader(f"📊 Performance Relativa: {top_1['razao_social']} vs Mercado")
    tab_rec, tab_vid = st.tabs(["💰 Spread Receita", "👥 Spread Vidas"])
    
    if 'Marca_Temp' not in df_mestre.columns:
        df_mestre['Marca_Temp'] = df_mestre['razao_social'].apply(extrair_marca)

    with tab_rec:
        fig = render_spread_chart(df_mestre, id_top_1, top_1['razao_social'], "Receita", "Mercado Geral")
        if fig: st.plotly_chart(fig, use_container_width=True)
    
    with tab_vid:
        fig = render_spread_chart(df_mestre, id_top_1, top_1['razao_social'], "Vidas", "Mercado Geral")
        if fig: st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 4. Tabela Ranking COLORIDA (Componente Novo)
    render_styled_ranking_table(
        df_ranqueado.head(30), 
        titulo=f"🏆 Top 30 Ranking do Trimestre {sel_trimestre}"
    )
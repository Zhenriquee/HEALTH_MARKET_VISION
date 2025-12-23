import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Imports Backend
from backend.analytics.comparativos import calcular_variacoes_operadora, calcular_kpis_vidas_avancados
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_score_vidas

# Imports Components
from views.components.header import render_header
from views.components.metrics import render_lives_kpi_row
from views.components.charts import render_spread_chart
from views.components.tables import render_ranking_table, formatar_moeda_br
from views.components.glossary import render_glossary

def gerar_storytelling_vidas(nome_op, trimestre, kpis, kpis_avancados, df_trimestre, marca_grupo):
    """
    Gera diagnóstico focado em Volume de Vidas.
    """
    # Dados
    var_vid_op = kpis.get('Var_Vidas_QoQ', 0) * 100
    volatilidade = kpis_avancados.get('Volatilidade', 0)
    cagr = kpis_avancados.get('CAGR_1Ano', 0) * 100
    
    # Mercado
    mediana_mkt_vid = df_trimestre['VAR_PCT_VIDAS'].median() * 100
    spread_mkt = var_vid_op - mediana_mkt_vid

    # Grupo
    df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
    if not df_grupo.empty:
        mediana_grp_vid = df_grupo['VAR_PCT_VIDAS'].median() * 100
        spread_grp = var_vid_op - mediana_grp_vid
    else:
        spread_grp = 0

    texto = f"##### 👥 Diagnóstico de Carteira: {trimestre}\n\n"
    
    # 1. Performance Curto Prazo
    texto += f"**1. Variação de Carteira:** A operadora **{nome_op}** registrou variação de **{var_vid_op:+.2f}%** em vidas."
    if spread_mkt > 0:
        texto += f" O crescimento de base superou o mercado em **+{spread_mkt:.2f} p.p.**"
    else:
        texto += f" A captação ficou **{spread_mkt:.2f} p.p.** abaixo da média de mercado."

    # 2. Contexto Grupo
    if marca_grupo != "OUTROS" and len(df_grupo) > 1:
        texto += f"\n\n**2. Contexto Grupo {marca_grupo}:** "
        if spread_grp > 0:
            texto += f"Destaque positivo, ampliando a base **+{spread_grp:.2f} p.p.** acima dos pares."
        else:
            texto += f"Performance de carteira inferior à média do grupo (**{spread_grp:.2f} p.p.**)."

    # 3. Tendência
    texto += f"\n\n**3. Tendência e Estabilidade:** "
    texto += f"A base de clientes apresenta volatilidade de **{volatilidade:.1f}%**"
    texto += "." if volatilidade < 5 else " (alta rotatividade/churn implícito)."
    texto += f" O crescimento estrutural (CAGR 1 ano) é de **{cagr:+.1f}%**."

    return texto

def render_evolution_lives_chart(df_mestre, id_operadora):
    df_hist = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].sort_values('ID_TRIMESTRE')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['NR_BENEF_T'], 
        name='Vidas', line=dict(color='#1f77b4', width=4), 
        hovertemplate='%{y:,.0f} Vidas'
    ))
    fig.update_layout(
        title="", xaxis_title="Trimestre", 
        yaxis=dict(title="Vidas", tickformat=",.0f"),
        hovermode="x unified", height=400
    )
    return fig

def render_analise_vidas(df_mestre):
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Filtros de Carteira")
        sel_trimestre = st.selectbox("📅 Trimestre:", sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True))
        
        df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        opts_mod = ["Todas"] + sorted(df_base['modalidade'].dropna().unique())
        sel_mod = st.selectbox("1️⃣ Modalidade:", opts_mod)
        if sel_mod != "Todas": df_base = df_base[df_base['modalidade'] == sel_mod]
        
        df_base['Marca_Temp'] = df_base['razao_social'].apply(extrair_marca)
        df_mestre['Marca_Temp'] = df_mestre['razao_social'].apply(extrair_marca)
        
        opts_grupo = ["Todos"] + sorted(df_base['Marca_Temp'].unique())
        sel_grupo = st.selectbox("2️⃣ Grupo:", opts_grupo)
        if sel_grupo != "Todos": df_base = df_base[df_base['Marca_Temp'] == sel_grupo]
        
        df_ops = df_base[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        map_ops = {f"{r['razao_social']} ({r['cnpj']})": str(r['ID_OPERADORA']) for _, r in df_ops.iterrows()}
        
        idx_def = 0
        lista_ops = sorted(list(map_ops.keys()))
        for i, op in enumerate(lista_ops):
            if "340952" in map_ops[op] or "UNIMED CARUARU" in op: idx_def = i; break
            
        if not lista_ops: st.warning("Sem operadoras."); return
        sel_op_nome = st.selectbox("3️⃣ Operadora:", lista_ops, index=idx_def)
        id_op = str(map_ops[sel_op_nome])
        st.markdown("---")
        render_glossary()

    # --- Processamento ---
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
    df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
    
    row_op = df_tri[df_tri['ID_OPERADORA'] == id_op]
    if row_op.empty: st.error("Dados não encontrados."); return
    dados_op = row_op.iloc[0]
    marca = extrair_marca(dados_op['razao_social'])
    
    # Score Vidas
    df_score = calcular_score_vidas(df_tri)
    df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
    df_score['Rank_Geral'] = df_score['Lives_Score'].rank(ascending=False, method='min')
    
    df_score['Marca_Temp'] = df_score['razao_social'].apply(extrair_marca)
    df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
    df_grupo['Rank_Grupo'] = df_grupo['Lives_Score'].rank(ascending=False, method='min')
    
    try:
        row_geral = df_score[df_score['ID_OPERADORA'] == id_op]
        r_geral = int(row_geral['Rank_Geral'].iloc[0]) if not row_geral.empty else "-"
        score = row_geral['Lives_Score'].iloc[0] if not row_geral.empty else 0
        
        row_grp = df_grupo[df_grupo['ID_OPERADORA'] == id_op]
        r_grupo = int(row_grp['Rank_Grupo'].iloc[0]) if not row_grp.empty else "-"
    except: r_geral, score, r_grupo = "-", 0, "-"
    
    # KPIs
    kpis = calcular_variacoes_operadora(df_mestre, id_op, sel_trimestre)
    kpis_avancados = calcular_kpis_vidas_avancados(df_mestre, id_op, sel_trimestre)
    insights = analisar_performance_marca(df_tri, dados_op)

    # --- Renderização ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | Grupo: **{marca}** | Visão: **Carteira de Vidas**")
    
    render_header(dados_op, r_geral, score)
    st.divider()

    texto_story = gerar_storytelling_vidas(dados_op['razao_social'], sel_trimestre, kpis, kpis_avancados, df_tri, marca)
    st.info(texto_story, icon="👥")
    st.divider()
    
    render_lives_kpi_row(kpis, kpis_avancados)
    st.divider()
    
    st.subheader("1. Matriz de Performance (Volume)")
    def fmt_mat(val, delta, money=False):
        v_str = formatar_moeda_br(val) if money else f"{int(val):,}".replace(",", ".")
        return f"{v_str} ({delta:+.2%})"
        
    matriz = {
        "Indicador": ["Carteira de Vidas", "Ticket Médio"],
        "Atual": [f"{int(kpis['Vidas']):,}".replace(",", "."), formatar_moeda_br(kpis['Ticket'])],
        "vs QoQ": [fmt_mat(kpis['Val_Vidas_QoQ'], kpis['Var_Vidas_QoQ']), "-"],
        "vs YoY": [fmt_mat(kpis['Val_Vidas_YoY'], kpis['Var_Vidas_YoY']), "-"]
    }
    st.dataframe(pd.DataFrame(matriz), use_container_width=True, hide_index=True)
    st.divider()
    
    st.subheader("2. Performance Relativa (Spread de Vidas)")
    c1, c2 = st.columns(2)
    c1.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Vidas", "Mercado"), use_container_width=True)
    c2.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Vidas", "Grupo", marca), use_container_width=True)
    st.divider()
    
    st.subheader("3. Evolução Histórica da Carteira")
    st.plotly_chart(render_evolution_lives_chart(df_mestre, id_op), use_container_width=True)
    st.divider()
    
    c1, c2 = st.columns(2)
    c1.metric("Share no Grupo", f"{insights['Share_of_Brand']:.2f}%")
    c2.metric("Cresc. Vidas (Média Grupo)", f"{insights['Media_Cresc_Vidas_Grupo']:.2%}")
    
    # Tabelas
    df_view_grupo = df_grupo.rename(columns={'Lives_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False)
    df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)
    
    render_ranking_table(
        df_view_grupo, 
        titulo=f"4. Ranking Carteira Grupo: {marca}",
        subtitulo="Ordenado por Score de Vidas (Volume + Crescimento)."
    )
    st.divider()
    
    df_view_geral = df_score.rename(columns={'Lives_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False)
    df_view_geral['#'] = df_view_geral['Rank_Geral']
    
    render_ranking_table(
        df_view_geral, 
        titulo="5. Ranking Carteira Geral",
        subtitulo="Comparativo de mercado baseado em performance de vidas."
    )
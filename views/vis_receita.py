import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Imports Backend
from backend.analytics.comparativos import calcular_variacoes_operadora, calcular_kpis_financeiros_avancados
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_score_financeiro # Nova função

# Imports Components
from views.components.header import render_header
from views.components.metrics import render_revenue_kpi_row # Novo componente
from views.components.charts import render_spread_chart
from views.components.tables import render_ranking_table, formatar_moeda_br
from views.components.glossary import render_glossary

def gerar_storytelling_financeiro(nome_op, trimestre, kpis, kpis_avancados, df_trimestre, marca_grupo):
    """
    Gera um diagnóstico financeiro COMPLETO (360º).
    """
    # Dados Básicos
    var_rec_op = kpis.get('Var_Receita_QoQ', 0) * 100
    var_ticket = kpis_avancados.get('Var_Ticket', 0) * 100
    volatilidade = kpis_avancados.get('Volatilidade', 0)
    cagr = kpis_avancados.get('CAGR_1Ano', 0) * 100
    
    # Referências de Mercado
    mediana_mkt_rec = df_trimestre['VAR_PCT_RECEITA'].median() * 100
    spread_mkt = var_rec_op - mediana_mkt_rec

    # Referências de Grupo
    df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
    if not df_grupo.empty:
        mediana_grp_rec = df_grupo['VAR_PCT_RECEITA'].median() * 100
        spread_grp = var_rec_op - mediana_grp_rec
    else:
        spread_grp = 0

    # --- NARRATIVA ---
    texto = f"##### Diagnóstico Financeiro Completo: {trimestre}\n\n"
    
    # 1. Performance Trimestral vs Mercado
    texto += f"**1. Performance Curto Prazo:** A operadora **{nome_op}** variou sua receita em **{var_rec_op:+.2f}%**."
    if spread_mkt > 0:
        texto += f" O desempenho superou a tendência do mercado em **+{spread_mkt:.2f} p.p.**, indicando ganho de tração."
    else:
        texto += f" O desempenho ficou **{spread_mkt:.2f} p.p.** abaixo da média de mercado, sinalizando perda de share relativo."

    # 2. Qualidade da Receita (Ticket)
    texto += f"\n\n**2. Qualidade da Receita (Ticket):** "
    if var_ticket > 0:
        texto += f"O Ticket Médio **cresceu {var_ticket:+.2f}%**, sugerindo capacidade de repasse de preço ou melhora no mix de carteira."
    elif var_ticket < -1:
        texto += f"Houve queda de **{var_ticket:.2f}%** no Ticket Médio, o que pode indicar descontos comerciais agressivos ou perda de contratos premium."
    else:
        texto += "O Ticket Médio manteve-se estável."

    # 3. Visão Grupo (Se aplicável)
    if marca_grupo != "OUTROS" and len(df_grupo) > 1:
        texto += f"\n\n**3. Contexto Grupo {marca_grupo}:** "
        if spread_grp > 0:
            texto += f"Liderança relativa, crescendo **+{spread_grp:.2f} p.p.** acima dos pares do grupo."
        else:
            texto += f"Desempenho inferior à média do grupo (**{spread_grp:.2f} p.p.**)."

    # 4. Risco e Longo Prazo
    texto += f"\n\n**4. Risco e Tendência:** "
    texto += f"A volatilidade histórica é de **{volatilidade:.1f}%**"
    texto += " (estável)." if volatilidade < 5 else " (alta oscilação)."
    texto += f" O crescimento estrutural (CAGR 1 ano) está em **{cagr:+.1f}%**."

    return texto

def render_evolution_revenue_chart(df_mestre, id_operadora):
    df_hist = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].sort_values('ID_TRIMESTRE')
    fig = go.Figure()
    # Apenas Linha de Receita
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['VL_SALDO_FINAL'], 
        name='Receita', line=dict(color='#2ca02c', width=4), 
        hovertemplate='R$ %{y:,.2f}'
    ))
    fig.update_layout(
        title="", xaxis_title="Trimestre", 
        yaxis=dict(title="Receita (R$)", tickprefix="R$ ", tickformat=",.2s"),
        hovermode="x unified", height=400
    )
    return fig

def render_analise_receita(df_mestre):
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Filtros Financeiros")
        sel_trimestre = st.selectbox("📅 Trimestre:", sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True))
        
        # Filtro Base (Cópia Segura)
        df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        # Filtros Cascata
        opts_mod = ["Todas"] + sorted(df_base['modalidade'].dropna().unique())
        sel_mod = st.selectbox("1️⃣ Modalidade:", opts_mod)
        if sel_mod != "Todas": df_base = df_base[df_base['modalidade'] == sel_mod]
        
        # Marca
        df_base['Marca_Temp'] = df_base['razao_social'].apply(extrair_marca)
        df_mestre['Marca_Temp'] = df_mestre['razao_social'].apply(extrair_marca) # Aplica no global para gráficos
        
        opts_grupo = ["Todos"] + sorted(df_base['Marca_Temp'].unique())
        sel_grupo = st.selectbox("2️⃣ Grupo:", opts_grupo)
        if sel_grupo != "Todos": df_base = df_base[df_base['Marca_Temp'] == sel_grupo]
        
        # Seleção Operadora
        df_ops = df_base[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        map_ops = {f"{r['razao_social']} ({r['cnpj']})": str(r['ID_OPERADORA']) for _, r in df_ops.iterrows()}
        
        # Default Logic
        idx_def = 0
        lista_ops = sorted(list(map_ops.keys()))
        for i, op in enumerate(lista_ops):
            if "340952" in map_ops[op] or "UNIMED CARUARU" in op: idx_def = i; break
            
        if not lista_ops: st.warning("Sem operadoras."); return
        sel_op_nome = st.selectbox("3️⃣ Operadora:", lista_ops, index=idx_def)
        id_op = str(map_ops[sel_op_nome]) # Força String explicitamente
        st.markdown("---")
        render_glossary()

    # --- Processamento ---
    
    # 1. Cria DF do Trimestre e garante tipagem de ID para cruzamento
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
    df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
    
    row_op = df_tri[df_tri['ID_OPERADORA'] == id_op]
    if row_op.empty: st.error("Dados não encontrados para esta operadora no trimestre."); return
    dados_op = row_op.iloc[0]
    marca = extrair_marca(dados_op['razao_social'])
    
    # 2. Score e Rankings Financeiros (Correção do desaparecimento)
    df_score = calcular_score_financeiro(df_tri)
    
    # Garante que IDs no df_score sejam string para o match funcionar
    df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
    df_score['Rank_Geral'] = df_score['Revenue_Score'].rank(ascending=False, method='min')
    
    df_score['Marca_Temp'] = df_score['razao_social'].apply(extrair_marca)
    df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
    df_grupo['Rank_Grupo'] = df_grupo['Revenue_Score'].rank(ascending=False, method='min')
    
    try:
        # Busca Segura
        row_score_geral = df_score[df_score['ID_OPERADORA'] == id_op]
        if not row_score_geral.empty:
            r_geral = int(row_score_geral['Rank_Geral'].iloc[0])
            score = row_score_geral['Revenue_Score'].iloc[0]
        else:
            r_geral = "-"
            score = 0

        row_score_grupo = df_grupo[df_grupo['ID_OPERADORA'] == id_op]
        if not row_score_grupo.empty:
            r_grupo = int(row_score_grupo['Rank_Grupo'].iloc[0])
        else:
            r_grupo = "-"
            
    except Exception as e:
        print(f"Erro Ranking: {e}")
        r_geral, score, r_grupo = "-", 0, "-"
    
    # 3. KPIs
    kpis = calcular_variacoes_operadora(df_mestre, id_op, sel_trimestre)
    kpis_avancados = calcular_kpis_financeiros_avancados(df_mestre, id_op, sel_trimestre)
    insights = analisar_performance_marca(df_tri, dados_op) # Traz Share of Brand

    # --- Renderização ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | Grupo: **{marca}** | Visão: **Receita**")
    
    render_header(dados_op, r_geral, score)
    st.divider()

    # Storytelling Completo (Passando kpis_avancados agora)
    texto_story = gerar_storytelling_financeiro(dados_op['razao_social'], sel_trimestre, kpis, kpis_avancados, df_tri, marca)
    st.info(texto_story, icon="💰")
    st.divider()
    
    render_revenue_kpi_row(
        kpis, 
        kpis_avancados, 
        rank_grupo_info=(r_grupo, len(df_grupo), marca)
    )
    st.divider()
    
    # Matriz Financeira
    st.subheader("1. Matriz de Performance Financeira")
    def fmt_mat(val, delta):
        return f"{formatar_moeda_br(val)} ({delta:+.2%})"
        
    matriz = {
        "Indicador": ["Receita Total", "Ticket Médio"],
        "Atual": [formatar_moeda_br(kpis['Receita']), formatar_moeda_br(kpis['Ticket'])],
        "vs QoQ": [fmt_mat(kpis['Val_Receita_QoQ'], kpis['Var_Receita_QoQ']), "-"],
        "vs YoY": [fmt_mat(kpis['Val_Receita_YoY'], kpis['Var_Receita_YoY']), "-"]
    }
    st.dataframe(pd.DataFrame(matriz), use_container_width=True, hide_index=True)
    st.divider()
    
    st.subheader("2. Performance Relativa (Spread de Receita)")
    c1, c2 = st.columns(2)
    c1.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Receita", "Mercado"), use_container_width=True)
    c2.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Receita", "Grupo", marca), use_container_width=True)
    st.divider()
    
    st.subheader("3. Evolução Histórica da Receita")
    st.plotly_chart(render_evolution_revenue_chart(df_mestre, id_op), use_container_width=True)
    st.divider()
    
    # --- Rankings e Share do Grupo ---
    
    # Métricas de Grupo (Solicitado no ponto 2)
    col_g1, col_g2 = st.columns(2)
    col_g1.metric("Participação no Grupo (Share)", f"{insights['Share_of_Brand']:.2f}%", help="Quanto a operadora representa da receita total do grupo.")
    col_g2.metric("Média Cresc. Receita (Grupo)", f"{insights['Media_Cresc_Receita_Grupo']:.2%}")
    
    # Tabelas
    df_view_grupo = df_grupo.rename(columns={'Revenue_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False)
    df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)
    
    render_ranking_table(
        df_view_grupo, 
        titulo=f"4. Ranking Financeiro Grupo: {marca}",
        subtitulo="Ordenado por Revenue Score (Volume + Crescimento)."
    )
    
    st.divider()
    
    df_view_geral = df_score.rename(columns={'Revenue_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False)
    df_view_geral['#'] = df_view_geral['Rank_Geral']
    
    render_ranking_table(
        df_view_geral, 
        titulo="5. Ranking Financeiro Geral",
        subtitulo="Comparativo de mercado baseado em performance de receita."
    )
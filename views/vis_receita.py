import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import traceback

# Imports Clean Arch
from backend.use_cases.revenue_analysis import RevenueAnalysisUseCase
from backend.exceptions import AppError
from backend.analytics.brand_intelligence import extrair_marca

# Imports Componentes Visuais
from views.components.header import render_header
from views.components.metrics import render_revenue_kpi_row
from views.components.charts import render_spread_chart
from views.components.tables import render_ranking_table, formatar_moeda_br
from views.components.glossary import render_glossary

def render_evolution_revenue_chart(df_mestre, id_operadora):
    """
    (Helper local de visualização apenas)
    """
    df_hist = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].sort_values('ID_TRIMESTRE')
    fig = go.Figure()
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
    # --- 1. CONTROLLER (Sidebar) ---
    with st.sidebar:
        st.header("⚙️ Filtros Financeiros")
        
        try:
            opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
            sel_trimestre = st.selectbox("📅 Trimestre:", options=opcoes_trimestre)
        except Exception:
            st.error("Erro ao carregar lista de trimestres.")
            return
        
        # Filtros Cascata
        df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        opts_mod = ["Todas"] + sorted(df_base['modalidade'].dropna().unique())
        sel_mod = st.selectbox("1️⃣ Modalidade:", opts_mod)
        if sel_mod != "Todas": df_base = df_base[df_base['modalidade'] == sel_mod]
        
        # Grupo
        df_base['Marca_Temp'] = df_base['razao_social'].apply(extrair_marca)
        opts_grupo = ["Todos"] + sorted(df_base['Marca_Temp'].unique())
        sel_grupo = st.selectbox("2️⃣ Grupo:", opts_grupo)
        if sel_grupo != "Todos": df_base = df_base[df_base['Marca_Temp'] == sel_grupo]
        
        # Operadora
        df_ops = df_base[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        map_ops = {f"{r['razao_social']} ({r['cnpj']})": str(r['ID_OPERADORA']) for _, r in df_ops.iterrows()}
        
        idx_def = 0
        lista_ops = sorted(list(map_ops.keys()))
        for i, op in enumerate(lista_ops):
            if "340952" in map_ops[op] or "UNIMED CARUARU" in op: idx_def = i; break
            
        if not lista_ops: st.warning("Sem operadoras."); return
        sel_op_nome = st.selectbox("3️⃣ Operadora:", lista_ops, index=idx_def)
        id_op = map_ops[sel_op_nome]
        
        st.markdown("---")
        render_glossary()

    # --- 2. EXECUÇÃO DO CASO DE USO ---
    try:
        use_case = RevenueAnalysisUseCase(df_mestre)
        resultado = use_case.execute(id_operadora=id_op, trimestre=sel_trimestre)
        
        # Desempacotamento
        info = resultado['info']
        metrics = resultado['metrics']
        content = resultado['content']

    except AppError as e:
        st.warning(f"Atenção: {str(e)}")
        return
    except Exception as e:
        st.error(f"Erro crítico: {str(e)}")
        with st.expander("Detalhes Técnicos"):
            st.code(traceback.format_exc())
        return

    # --- 3. RENDERIZAÇÃO ---
    st.caption(f"📅 Referência: **{info['trimestre']}** | Grupo: **{info['marca']}** | Visão: **Receita**")
    
    # Header
    render_header(info['dados_op'], metrics['rank_geral'], metrics['score'])
    st.divider()

    # Storytelling
    st.info(content['storytelling'], icon="💰")
    st.divider()
    
    # KPI Grid (Avançado)
    render_revenue_kpi_row(
        metrics['kpis'], 
        metrics['kpis_avancados'],
        rank_grupo_info=(metrics['rank_grupo'], metrics['total_grupo'], info['marca'])
    )
    st.divider()
    
    # Matriz Financeira
    st.subheader("1. Matriz de Performance Financeira")
    def fmt_mat(val, delta):
        return f"{formatar_moeda_br(val)} ({delta:+.2%})"
        
    kpis = metrics['kpis']
    matriz = {
        "Indicador": ["Receita Total", "Ticket Médio"],
        "Atual": [formatar_moeda_br(kpis['Receita']), formatar_moeda_br(kpis['Ticket'])],
        "vs QoQ": [fmt_mat(kpis['Val_Receita_QoQ'], kpis['Var_Receita_QoQ']), "-"],
        "vs YoY": [fmt_mat(kpis['Val_Receita_YoY'], kpis['Var_Receita_YoY']), "-"]
    }
    st.dataframe(pd.DataFrame(matriz), width="stretch", hide_index=True)
    st.divider()
    
    # Gráficos Spread
    st.subheader("2. Performance Relativa (Spread de Receita)")
    
    # Prepara DF para gráficos
    df_graficos = content['df_full'].copy()
    if 'Marca_Temp' not in df_graficos.columns:
        df_graficos['Marca_Temp'] = df_graficos['razao_social'].apply(extrair_marca)
        
    c1, c2 = st.columns(2)
    c1.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Receita", "Mercado"), use_container_width=True)
    c2.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Receita", "Grupo", info['marca']), use_container_width=True)
    st.divider()
    
    # Evolução
    st.subheader("3. Evolução Histórica da Receita")
    st.plotly_chart(render_evolution_revenue_chart(df_graficos, info['id_op']), use_container_width=True)
    st.divider()
    
    # Tabelas
    c1, c2 = st.columns(2)
    c1.metric("Participação no Grupo (Share)", f"{metrics['insights']['Share_of_Brand']:.2f}%")
    c2.metric("Média Cresc. Receita (Grupo)", f"{metrics['insights']['Media_Cresc_Receita_Grupo']:.2%}")
    
    render_ranking_table(
        content['tabela_grupo'], 
        titulo=f"4. Ranking Financeiro Grupo: {info['marca']}",
        subtitulo="Ordenado por Revenue Score (Volume + Crescimento)."
    )
    st.divider()
    
    render_ranking_table(
        content['tabela_geral'], 
        titulo="5. Ranking Financeiro Geral",
        subtitulo="Comparativo de mercado baseado em performance de receita."
    )
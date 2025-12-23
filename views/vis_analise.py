import streamlit as st
import pandas as pd
import traceback

# Imports Clean Arch
from backend.use_cases.operator_analysis import OperatorAnalysisUseCase
from backend.exceptions import AppError
from backend.analytics.brand_intelligence import extrair_marca

# Imports Componentes Visuais
from views.components.header import render_header
from views.components.metrics import render_kpi_row
from views.components.charts import render_spread_chart, render_evolution_chart
from views.components.tables import render_ranking_table, formatar_moeda_br
from views.components.glossary import render_glossary

def render_analise(df_mestre):
    # --- 1. CONTROLLER DA VIEW (Sidebar & Filtros) ---
    with st.sidebar:
        st.header("⚙️ Configuração")

        st.divider()
        
        # Filtro de Trimestre
        try:
            opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
            sel_trimestre = st.selectbox("📅 Trimestre:", options=opcoes_trimestre)
        except Exception:
            st.error("Erro ao carregar trimestres.")
            return
        
        # Lógica de Cascata de Filtros
        df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        # Modalidade
        opts_mod = ["Todas"] + sorted(df_base['modalidade'].dropna().unique())
        sel_mod = st.selectbox("1️⃣ Modalidade:", opts_mod)
        if sel_mod != "Todas": df_base = df_base[df_base['modalidade'] == sel_mod]
        
        # Grupo/Marca
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
        
        st.session_state["filtro_id_op"] = id_op
        st.session_state["filtro_trimestre"] = sel_trimestre
        
        st.markdown("---")
        render_glossary()

    # --- 2. EXECUÇÃO DO CASO DE USO ---
    try:
        use_case = OperatorAnalysisUseCase(df_mestre)
        resultado = use_case.execute(id_operadora=id_op, trimestre=sel_trimestre)
        
        # Desempacotamento (ViewModel)
        info = resultado['info']
        metrics = resultado['metrics']
        content = resultado['content']

    except AppError as e:
        st.warning(f"Atenção: {str(e)}")
        return
    except Exception as e:
        st.error(f"Erro crítico: {str(e)}")
        # Em produção, logging seria feito aqui
        with st.expander("Detalhes Técnicos"):
            st.code(traceback.format_exc())
        return

    # --- 3. RENDERIZAÇÃO (Visualização Pura) ---
    
    st.caption(f"📅 Referência: **{info['trimestre']}** | Grupo: **{info['marca']}**")
    
    # Header
    render_header(info['dados_op'], metrics['rank_geral'], metrics['score'])
    st.divider()

    # Storytelling
    st.info(content['storytelling'], icon="📈")
    st.divider()
    
    # KPIs Grid
    render_kpi_row(
        metrics['kpis'], 
        rank_grupo_info=(metrics['rank_grupo'], metrics['total_grupo'], info['marca'])
    )
    st.divider()
    
    # Matriz Visual
    st.subheader("1. Matriz de Performance")
    def fmt_mat(val, delta, money=False):
        v_str = formatar_moeda_br(val) if money else f"{int(val):,}".replace(",", ".")
        return f"{v_str} ({delta:+.2%})"
    
    kpis = metrics['kpis']
    matriz = {
        "Indicador": ["Vidas", "Receita", "Ticket"],
        "Atual": [f"{int(kpis['Vidas']):,}".replace(",", "."), formatar_moeda_br(kpis['Receita']), formatar_moeda_br(kpis['Ticket'])],
        "vs QoQ": [fmt_mat(kpis['Val_Vidas_QoQ'], kpis['Var_Vidas_QoQ']), fmt_mat(kpis['Val_Receita_QoQ'], kpis['Var_Receita_QoQ'], True), "-"],
        "vs YoY": [fmt_mat(kpis['Val_Vidas_YoY'], kpis['Var_Vidas_YoY']), fmt_mat(kpis['Val_Receita_YoY'], kpis['Var_Receita_YoY'], True), "-"]
    }
    st.dataframe(pd.DataFrame(matriz), width="stretch", hide_index=True)
    st.divider()
    
    # Gráficos
    st.subheader("2. Performance Relativa")
    t1, t2 = st.tabs(["💰 Receita", "👥 Vidas"])
    
    # Preparação para gráficos (garantindo a coluna marca)
    df_graficos = content['df_full'].copy()
    if 'Marca_Temp' not in df_graficos.columns:
        df_graficos['Marca_Temp'] = df_graficos['razao_social'].apply(extrair_marca)

    with t1:
        c1, c2 = st.columns(2)
        c1.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Receita", "Mercado"), use_container_width=True)
        c2.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Receita", "Grupo", info['marca']), use_container_width=True)
    with t2:
        c1, c2 = st.columns(2)
        c1.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Vidas", "Mercado"), use_container_width=True)
        c2.plotly_chart(render_spread_chart(df_graficos, info['id_op'], info['dados_op']['razao_social'], "Vidas", "Grupo", info['marca']), use_container_width=True)
    st.divider()
    
    st.subheader("3. Evolução Histórica")
    st.plotly_chart(render_evolution_chart(df_graficos, info['id_op']), use_container_width=True)
    st.divider()
    
    # Tabelas
    c1, c2 = st.columns(2)
    c1.metric("Share no Grupo", f"{metrics['insights']['Share_of_Brand']:.2f}%")
    c2.metric("Cresc. Vidas (Média Grupo)", f"{metrics['insights']['Media_Cresc_Vidas_Grupo']:.2%}")
    
    render_ranking_table(
        content['tabela_grupo'], 
        titulo=f"4. Ranking Grupo: {info['marca']}"
    )
    st.divider()
    render_ranking_table(
        content['tabela_geral'], 
        titulo="5. Ranking Geral (Mercado)"
    )
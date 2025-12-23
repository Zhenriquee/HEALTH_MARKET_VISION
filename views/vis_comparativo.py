import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import traceback

# Imports Clean Arch
from backend.use_cases.comparison_analysis import ComparisonAnalysisUseCase
from backend.exceptions import AppError

# Imports Componentes
from views.components.tables import formatar_moeda_br
from views.components.glossary import render_glossary

def render_comparativo(df_mestre):
    # --- 1. CONTROLLER (Sidebar) ---
    with st.sidebar:
        st.header("Configuração do Comparativo")
        
        try:
            opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
            sel_trimestre = st.selectbox("Trimestre de Referência:", options=opcoes_trimestre)
        except Exception:
            st.error("Erro ao carregar trimestres.")
            return
        
        # Filtros Auxiliares
        st.markdown("---")
        st.caption("Filtros de Busca")
        df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        opcoes_modalidade = ["Todas"] + sorted(df_tri['modalidade'].dropna().unique())
        sel_mod = st.selectbox("Modalidade:", options=opcoes_modalidade)
        
        if sel_mod != "Todas":
            df_lista = df_tri[df_tri['modalidade'] == sel_mod].copy()
        else:
            df_lista = df_tri.copy()
            
        df_lista_unicas = df_lista[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        map_ops = {f"{r['razao_social']} ({r['cnpj']})": str(r['ID_OPERADORA']) for _, r in df_lista_unicas.iterrows()}
        lista_nomes = sorted(list(map_ops.keys()))
        
        st.markdown("---")
        
        op1_nome = st.selectbox("Operadora A:", options=lista_nomes, index=0 if lista_nomes else None)
        lista_b = [x for x in lista_nomes if x != op1_nome]
        op2_nome = st.selectbox("Operadora B:", options=lista_b, index=0 if lista_b else None)
        
        if not op1_nome or not op2_nome:
            st.warning("Selecione duas operadoras para prosseguir.")
            return

        id_op1 = map_ops[op1_nome]
        id_op2 = map_ops[op2_nome]
        
        st.markdown("---")
        render_glossary()

    # --- 2. EXECUÇÃO DO CASO DE USO ---
    try:
        use_case = ComparisonAnalysisUseCase(df_mestre)
        resultado = use_case.execute(id_op1=id_op1, id_op2=id_op2, trimestre=sel_trimestre)
        
        op1 = resultado['op1']
        op2 = resultado['op2']
        comp_data = resultado['comparison_table']
        radar = resultado['radar_data']

    except AppError as e:
        st.warning(f"Atenção: {str(e)}")
        return
    except Exception as e:
        st.error(f"Erro crítico: {str(e)}")
        with st.expander("Detalhes Técnicos"):
            st.code(traceback.format_exc())
        return

    # --- 3. RENDERIZAÇÃO ---
    
    st.title("⚔️ Comparativo Direto entre Operadoras")
    st.caption(f"Período de Referência: {sel_trimestre}")
    
    # 1. HEADER (Cards com Ícones Restaurados)
    col1, col_mid, col2 = st.columns([1, 0.1, 1])
    
    def render_clean_card(col, stats, label_op, icon_op):
        with col:
            st.subheader(f"{icon_op} {label_op}")
            st.markdown(f"**{stats['Dados']['razao_social']}**")
            st.caption(f"CNPJ: {stats['Dados']['cnpj']}")
            st.caption(f"Modalidade: {stats['Dados']['modalidade']}")
            
            st.divider()
            
            c_r1, c_r2 = st.columns(2)
            c_r1.metric("⭐ Power Score", f"{stats['Dados']['Power_Score']:.1f}")
            c_r2.metric("🏆 Rank Geral", f"#{stats['Rank_Geral']}")
            
            st.metric(f"🏢 Rank {stats['Marca']}", f"#{stats['Rank_Grupo']}", f"de {stats['Total_Grupo']}")
            st.progress(stats['Dados']['Power_Score']/100)

    render_clean_card(col1, op1, "Operadora A", "🅰️")
    with col_mid: 
        st.markdown("<div style='border-left:1px solid #e6e6e6; height:100%'></div>", unsafe_allow_html=True)
    render_clean_card(col2, op2, "Operadora B", "🅱️")
    
    st.divider()
    
    # 2. TABELA COMPARATIVA (Ícones nos Indicadores e Vencedor)
    st.subheader("📊 Quadro Comparativo de Indicadores")
    
    df_rows = []
    for row in comp_data:
        val1 = row['val1']
        val2 = row['val2']
        diff = row['diff']
        label = row['label']
        
        # Adiciona Ícones aos Labels (Visual Only)
        if "Vidas" in label and "Cresc" not in label: label = f"👥 {label}"
        elif "Cresc" in label: label = f"📈 {label}"
        elif "Receita" in label: label = f"💰 {label}"
        elif "Ticket" in label: label = f"🎟️ {label}"
        
        # Formata Valores
        if "Receita" in label or "Ticket" in label:
            s1 = formatar_moeda_br(val1)
            s2 = formatar_moeda_br(val2)
        elif row['is_pct']:
            s1 = f"{val1:+.2f}%"
            s2 = f"{val2:+.2f}%"
        else:
            s1 = f"{val1:,.0f}".replace(",", ".")
            s2 = f"{val2:,.0f}".replace(",", ".")
        
        # Formata Diferença
        if row['is_pct']:
            s_diff = f"{diff:+.2f} p.p."
        else:
            s_diff = f"{diff:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        # Vencedor com Ícones
        if row['winner'] == 'op1': winner_name = "🅰️ Op A"
        elif row['winner'] == 'op2': winner_name = "🅱️ Op B"
        else: winner_name = "➖"
        
        df_rows.append({
            "Indicador": label,
            "Operadora A": s1,
            "Operadora B": s2,
            "Diferença": s_diff,
            "Vantagem": winner_name
        })

    st.dataframe(
        pd.DataFrame(df_rows), 
        width="stretch",
        hide_index=True,
        column_config={
            "Indicador": st.column_config.TextColumn("KPI", width="medium"),
            "Operadora A": st.column_config.TextColumn(f"🅰️ Op A ({op1['Dados']['razao_social'][:10]}...)", width="medium"),
            "Operadora B": st.column_config.TextColumn(f"🅱️ Op B ({op2['Dados']['razao_social'][:10]}...)", width="medium"),
        }
    )
    
    st.divider()
    
    # 3. RADAR CHART
    st.subheader("🕸️ Gráfico Radar de Performance (Normalizado)")
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar['norm1'], theta=radar['categories'], fill='toself', 
        name=f"A: {radar['name1'][:15]}...", line_color='#1f77b4'
    ))
    fig.add_trace(go.Scatterpolar(
        r=radar['norm2'], theta=radar['categories'], fill='toself', 
        name=f"B: {radar['name2'][:15]}...", line_color='#d62728'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, height=450,
        title="Comparativo Relativo (Escala 0-100)",
        margin=dict(t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)
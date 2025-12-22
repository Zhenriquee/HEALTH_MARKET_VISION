import streamlit as st
import pandas as pd
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_power_score

# Imports dos Componentes
from views.components.header import render_header
from views.components.metrics import render_kpi_row
from views.components.charts import render_spread_chart, render_evolution_chart
from views.components.tables import render_ranking_table, formatar_moeda_br
from views.components.glossary import render_glossary

# Função de Storytelling (Mantida igual)
def gerar_resumo_storytelling(nome_op, trimestre, kpis, df_trimestre, marca_grupo):
    var_rec_op = kpis.get('Var_Receita_QoQ', 0) * 100
    var_vid_op = kpis.get('Var_Vidas_QoQ', 0) * 100
    mediana_mkt_rec = df_trimestre['VAR_PCT_RECEITA'].median() * 100
    mediana_mkt_vid = df_trimestre['VAR_PCT_VIDAS'].median() * 100

    df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
    if not df_grupo.empty:
        mediana_grp_rec = df_grupo['VAR_PCT_RECEITA'].median() * 100
    else:
        mediana_grp_rec = 0

    spread_mkt = var_rec_op - mediana_mkt_rec
    spread_grp = var_rec_op - mediana_grp_rec

    texto = f"##### 📝 Resumo Executivo: {trimestre}\n\n"
    texto += f"No **{trimestre}**, a operadora **{nome_op}** registrou uma variação de receita de **{var_rec_op:+.2f}%**. "

    if spread_mkt > 0:
        texto += f"Performance sólida, superando a média do mercado em **+{spread_mkt:.2f} p.p.** "
    elif spread_mkt < 0:
        texto += f"Desempenho financeiro ficou **{spread_mkt:.2f} p.p.** abaixo da média do mercado. "
    else:
        texto += "Desempenho alinhado à média do mercado. "

    if marca_grupo != "OUTROS" and len(df_grupo) > 1:
        texto += f"No grupo **{marca_grupo}**, a operadora "
        if spread_grp > 0:
            texto += f"destacou-se com **+{spread_grp:.2f} p.p.** acima dos pares."
        else:
            texto += f"ficou **{spread_grp:.2f} p.p.** abaixo da média do grupo."
    
    texto += f"\n\n> *Carteira de Clientes: **{var_vid_op:+.2f}%** (vs **{mediana_mkt_vid:+.2f}%** do mercado).*"
    return texto

def render_analise(df_mestre):
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Filtros")
        sel_trimestre = st.selectbox("📅 Trimestre:", sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True))
        
        df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        opts_mod = ["Todas"] + sorted(df_base['modalidade'].dropna().unique())
        sel_mod = st.selectbox("1️⃣ Modalidade:", opts_mod)
        if sel_mod != "Todas": df_base = df_base[df_base['modalidade'] == sel_mod]
        
        df_base['Marca_Temp'] = df_base['razao_social'].apply(extrair_marca)
        df_mestre['Marca_Temp'] = df_mestre['razao_social'].apply(extrair_marca) # Global
        
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
        id_op = map_ops[sel_op_nome]
        st.markdown("---")
        render_glossary()

    # --- Processamento ---
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
    df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
    
    row_op = df_tri[df_tri['ID_OPERADORA'] == id_op]
    if row_op.empty: st.error("Dados não encontrados."); return
    dados_op = row_op.iloc[0]
    marca = extrair_marca(dados_op['razao_social'])
    
    # Cálculos de Score e Rank Geral
    df_score = calcular_power_score(df_tri)
    df_score['Rank_Geral'] = df_score['Power_Score'].rank(ascending=False, method='min')
    df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
    
    # Cálculos de Rank Grupo
    df_score['Marca_Temp'] = df_score['razao_social'].apply(extrair_marca)
    df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
    df_grupo['Rank_Grupo'] = df_grupo['Power_Score'].rank(ascending=False, method='min')
    
    try:
        r_geral = int(df_score[df_score['ID_OPERADORA'] == id_op]['Rank_Geral'].iloc[0])
        score = df_score[df_score['ID_OPERADORA'] == id_op]['Power_Score'].iloc[0]
        r_grupo = int(df_grupo[df_grupo['ID_OPERADORA'] == id_op]['Rank_Grupo'].iloc[0])
    except: r_geral, score, r_grupo = "-", 0, "-"
    
    kpis = calcular_variacoes_operadora(df_mestre, id_op, sel_trimestre)
    insights = analisar_performance_marca(df_tri, dados_op)

    # --- Renderização ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | Grupo: **{marca}**")
    
    render_header(dados_op, r_geral, score)
    st.divider()

    # Resumo Storytelling
    resumo_narrativo = gerar_resumo_storytelling(dados_op['razao_social'], sel_trimestre, kpis, df_tri, marca)
    st.info(resumo_narrativo, icon="📈")
    st.divider()
    
    render_kpi_row(kpis, rank_grupo_info=(r_grupo, len(df_grupo), marca))
    st.divider()
    
    st.subheader("1. Matriz de Performance")
    def fmt_mat(val, delta, money=False):
        v_str = formatar_moeda_br(val) if money else f"{int(val):,}".replace(",", ".")
        return f"{v_str} ({delta:+.2%})"
        
    matriz = {
        "Indicador": ["Vidas", "Receita", "Ticket"],
        "Atual": [f"{int(kpis['Vidas']):,}".replace(",", "."), formatar_moeda_br(kpis['Receita']), formatar_moeda_br(kpis['Ticket'])], # pyright: ignore[reportOptionalSubscript]
        "vs QoQ": [fmt_mat(kpis['Val_Vidas_QoQ'], kpis['Var_Vidas_QoQ']), fmt_mat(kpis['Val_Receita_QoQ'], kpis['Var_Receita_QoQ'], True), "-"], # pyright: ignore[reportOptionalSubscript]
        "vs YoY": [fmt_mat(kpis['Val_Vidas_YoY'], kpis['Var_Vidas_YoY']), fmt_mat(kpis['Val_Receita_YoY'], kpis['Var_Receita_YoY'], True), "-"] # pyright: ignore[reportOptionalSubscript]
    }
    st.dataframe(pd.DataFrame(matriz), use_container_width=True, hide_index=True)
    st.divider()
    
    st.subheader("2. Performance Relativa")
    t1, t2 = st.tabs(["💰 Receita", "👥 Vidas"])
    with t1:
        c1, c2 = st.columns(2)
        c1.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Receita", "Mercado"), use_container_width=True)
        c2.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Receita", "Grupo", marca), use_container_width=True)
    with t2:
        c1, c2 = st.columns(2)
        c1.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Vidas", "Mercado"), use_container_width=True)
        c2.plotly_chart(render_spread_chart(df_mestre, id_op, dados_op['razao_social'], "Vidas", "Grupo", marca), use_container_width=True)
    st.divider()
    
    st.subheader("3. Evolução Histórica")
    st.plotly_chart(render_evolution_chart(df_mestre, id_op), use_container_width=True)
    st.divider()
    
    # --- CORREÇÃO NOS RANKINGS ---
    c1, c2 = st.columns(2)
    c1.metric("Share no Grupo", f"{insights['Share_of_Brand']:.2f}%")
    c2.metric("Cresc. Vidas (Média Grupo)", f"{insights['Media_Cresc_Vidas_Grupo']:.2%}")
    
    # Tabela 1: Ranking Grupo
    # Atribuímos o range 1..N à coluna '#' para o componente renderizar corretamente como Ranking do Grupo
    df_view_grupo = df_grupo.sort_values('Power_Score', ascending=False).copy()
    df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)
    
    render_ranking_table(
        df_view_grupo, 
        titulo=f"4. Ranking Grupo: {marca}"
    )
    
    st.divider()
    
    # Tabela 2: Ranking Geral
    # Aqui usamos o Rank_Geral real que calculamos, pois na tabela geral queremos saber a posição absoluta
    df_view_geral = df_score.sort_values('Power_Score', ascending=False).copy()
    df_view_geral['#'] = df_view_geral['Rank_Geral'].astype(int)
    
    render_ranking_table(
        df_view_geral, 
        titulo="5. Ranking Geral (Mercado)"
    )
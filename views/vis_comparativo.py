import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Imports Backend
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.calculadora_score import calcular_power_score
from backend.analytics.brand_intelligence import extrair_marca

# Imports Components
from views.components.tables import formatar_moeda_br

def render_comparativo(df_mestre):
    # --- SIDEBAR: SELEÇÃO DUPLA ---
    with st.sidebar:
        st.header("Configurar Comparativo")
        
        # 1. Trimestre (Comum as duas)
        opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
        sel_trimestre = st.selectbox("📅 Trimestre de Referência:", options=opcoes_trimestre)
        
        # Filtra base pelo tempo
        df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == sel_trimestre].copy()
        
        # 2. Filtros Auxiliares
        st.markdown("---")
        st.caption("Filtros para encontrar as operadoras")
        opcoes_modalidade = ["Todas"] + sorted(df_tri['modalidade'].dropna().unique())
        sel_mod = st.selectbox("Modalidade (Filtro):", options=opcoes_modalidade)
        
        if sel_mod != "Todas":
            df_lista = df_tri[df_tri['modalidade'] == sel_mod].copy()
        else:
            df_lista = df_tri.copy()
            
        # Cria lista de nomes para selectbox
        df_lista_unicas = df_lista[['ID_OPERADORA', 'razao_social', 'cnpj']].drop_duplicates()
        map_ops = {f"{r['razao_social']} ({r['cnpj']})": str(r['ID_OPERADORA']) for _, r in df_lista_unicas.iterrows()}
        lista_nomes = sorted(list(map_ops.keys()))
        
        st.markdown("---")
        
        # 3. Seleção das Operadoras
        op1_nome = st.selectbox("🥊 Operadora A:", options=lista_nomes, index=0 if lista_nomes else None)
        
        # Remove a Operadora A da lista da Operadora B
        lista_b = [x for x in lista_nomes if x != op1_nome]
        op2_nome = st.selectbox("🥊 Operadora B:", options=lista_b, index=0 if lista_b else None)
        
        if not op1_nome or not op2_nome:
            st.warning("Selecione duas operadoras.")
            return

        id_op1 = map_ops[op1_nome]
        id_op2 = map_ops[op2_nome]

    # --- PROCESSAMENTO ---
    
    # 1. Garante tipagem
    df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
    
    # 2. Calcula Rankings Gerais do Trimestre
    df_scored = calcular_power_score(df_tri)
    df_scored['Rank_Geral'] = df_scored['Power_Score'].rank(ascending=False, method='min')
    df_scored['ID_OPERADORA'] = df_scored['ID_OPERADORA'].astype(str)
    
    # 3. Extrai Dados Individuais
    def get_op_stats(id_op):
        row = df_scored[df_scored['ID_OPERADORA'] == id_op]
        if row.empty: return None
        data = row.iloc[0]
        
        # Calcula Rank Grupo
        marca = extrair_marca(data['razao_social'])
        df_grupo = df_scored[df_scored['razao_social'].apply(extrair_marca) == marca]
        
        # Busca rank no grupo com segurança
        try:
            rank_grupo = df_grupo['Power_Score'].rank(ascending=False, method='min')[df_grupo['ID_OPERADORA'] == id_op].iloc[0]
        except:
            rank_grupo = "-"
        
        # KPIs Financeiros/Vidas
        kpis = calcular_variacoes_operadora(df_mestre, id_op, sel_trimestre)
        
        return {
            'Dados': data,
            'Marca': marca,
            'Rank_Geral': int(data['Rank_Geral']),
            'Rank_Grupo': int(rank_grupo) if rank_grupo != "-" else "-",
            'Total_Grupo': len(df_grupo),
            'KPIs': kpis
        }

    stats_1 = get_op_stats(id_op1)
    stats_2 = get_op_stats(id_op2)
    
    if not stats_1 or not stats_2:
        st.error("Erro ao processar dados das operadoras selecionadas.")
        return

    # --- RENDERIZAÇÃO ---
    
    st.title("Comparativo Direto")
    st.caption(f"Referência: {sel_trimestre}")
    
    # 1. HEADER LADO A LADO
    col1, col_mid, col2 = st.columns([1, 0.1, 1])
    
    def render_mini_card(col, stats, label_op):
        with col:
            st.subheader(f"{label_op}: {stats['Dados']['razao_social']}")
            st.caption(f"CNPJ: {stats['Dados']['cnpj']} | {stats['Dados']['modalidade']}")
            
            # Rank e Score
            c_r1, c_r2 = st.columns(2)
            c_r1.metric("⭐ Power Score", f"{stats['Dados']['Power_Score']:.1f}")
            c_r2.metric("🏆 Rank Geral", f"#{stats['Rank_Geral']}")
            
            st.metric(f"🏢 Rank {stats['Marca']}", f"#{stats['Rank_Grupo']}", f"de {stats['Total_Grupo']}")
            
            # Barra de Score visual
            st.progress(stats['Dados']['Power_Score']/100)

    render_mini_card(col1, stats_1, "Operadora A")
    with col_mid: st.markdown("<div style='border-left:1px solid #ddd; height:100%'></div>", unsafe_allow_html=True) 
    render_mini_card(col2, stats_2, "Operadora B")
    
    st.divider()
    
    # 2. TABELA COMPARATIVA (Head to Head)
    st.subheader("📊 Batalha de Números")
    
    k1 = stats_1['KPIs']
    k2 = stats_2['KPIs']
    
    # --- CORREÇÃO AQUI NA FUNÇÃO CALC_DIFF ---
    def calc_diff(v1, v2, is_pct=False):
        diff = v1 - v2
        
        if is_pct: 
            return f"{diff:+.2f} p.p."
        
        # Formatação numérica padrão com separadores de milhar e 2 casas decimais
        # Ex: +1,500.00 -> +1.500,00 (BR)
        # O ":+,.2f" força o sinal (+/-), usa virgula pra milhar e ponto pra decimal
        texto_fmt = f"{diff:+,.2f}"
        
        # Inverte para padrão Brasileiro (Ponto milhar, Virgula decimal)
        return texto_fmt.replace(",", "X").replace(".", ",").replace("X", ".")

    # Lista de Métricas
    metrics_data = [
        ("👥 Vidas Totais", int(k1['Vidas']), int(k2['Vidas']), False),
        ("📈 Cresc. Vidas (QoQ)", k1['Var_Vidas_QoQ']*100, k2['Var_Vidas_QoQ']*100, True),
        ("💰 Receita Total", k1['Receita'], k2['Receita'], False),
        ("📈 Cresc. Receita (QoQ)", k1['Var_Receita_QoQ']*100, k2['Var_Receita_QoQ']*100, True),
        ("🎟️ Ticket Médio", k1['Ticket'], k2['Ticket'], False)
    ]
    
    df_compare = []
    for label, v1, v2, is_pct in metrics_data:
        # Formatação Visual das Colunas A e B
        if "Receita" in label or "Ticket" in label:
            s1 = formatar_moeda_br(v1)
            s2 = formatar_moeda_br(v2)
        elif is_pct:
            s1 = f"{v1:+.2f}%"
            s2 = f"{v2:+.2f}%"
        else:
            s1 = f"{v1:,.0f}".replace(",", ".")
            s2 = f"{v2:,.0f}".replace(",", ".")
            
        # Vencedor
        if v1 > v2: winner = "🅰️ Op A"
        elif v2 > v1: winner = "🅱️ Op B"
        else: winner = "Empate"
        
        df_compare.append({
            "Indicador": label,
            f"🅰️ {stats_1['Dados']['razao_social'][:15]}...": s1,
            f"🅱️ {stats_2['Dados']['razao_social'][:15]}...": s2,
            "Diferença": calc_diff(v1, v2, is_pct), # Agora usa a função corrigida
            "Vantagem": winner
        })
        
    st.dataframe(pd.DataFrame(df_compare), use_container_width=True, hide_index=True)
    
    st.divider()
    
    # 3. GRÁFICO RADAR
    st.subheader("🕸️ Comparativo de Performance (Normalizado)")
    
    categories = ['Score', 'Vidas', 'Receita', 'Cresc. Vidas', 'Cresc. Receita']
    
    vals1 = [stats_1['Dados']['Power_Score'], k1['Vidas'], k1['Receita'], k1['Var_Vidas_QoQ'], k1['Var_Receita_QoQ']]
    vals2 = [stats_2['Dados']['Power_Score'], k2['Vidas'], k2['Receita'], k2['Var_Vidas_QoQ'], k2['Var_Receita_QoQ']]
    
    norm_vals1 = []
    norm_vals2 = []
    
    for v1, v2 in zip(vals1, vals2):
        # Normalização relativa (Maior = 100%)
        # Usa valor absoluto para evitar problemas com crescimento negativo no radar
        abs_v1, abs_v2 = abs(v1), abs(v2)
        max_val = max(abs_v1, abs_v2) if max(abs_v1, abs_v2) > 0 else 1
        
        norm_vals1.append((abs_v1 / max_val) * 100)
        norm_vals2.append((abs_v2 / max_val) * 100)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=norm_vals1, theta=categories, fill='toself', name='Op A (Azul)', line_color='#1f77b4'
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_vals2, theta=categories, fill='toself', name='Op B (Vermelho)', line_color='#d62728'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, height=400,
        title="Raio-X Relativo (Escala 0-100)"
    )
    st.plotly_chart(fig, use_container_width=True)
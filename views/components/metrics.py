import streamlit as st

def formatar_moeda_kpi(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_kpi_row(kpis, rank_grupo_info=None):
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Vidas", f"{int(kpis['Vidas']):,}".replace(",", "."), delta=f"{kpis.get('Var_Vidas_QoQ', 0):.1%} (QoQ)".replace(".", ","), delta_color="normal")
    k2.metric("💰 Receita", formatar_moeda_kpi(kpis['Receita']), delta=f"{kpis.get('Var_Receita_QoQ', 0):.1%} (QoQ)".replace(".", ","), delta_color="normal")
    k3.metric("📊 Ticket Médio", formatar_moeda_kpi(kpis['Ticket']))
    
    if rank_grupo_info and isinstance(rank_grupo_info, tuple):
        rank, total, nome_grupo = rank_grupo_info
        k4.metric(f"🏢 Rank {nome_grupo}", f"#{rank}", f"de {total} ops", delta_color="off")
    else:
        k4.metric("📍 Info", "-")

def render_revenue_kpi_row(kpis, kpis_avancados, rank_grupo_info=None):
    k1, k2, k3 = st.columns(3)
    k1.metric("💰 Receita Total", formatar_moeda_kpi(kpis['Receita']), delta=f"{kpis.get('Var_Receita_QoQ', 0):.1%} (QoQ)".replace(".", ","), delta_color="normal")
    
    var_ticket = kpis_avancados.get('Var_Ticket', 0)
    k2.metric("📊 Ticket Médio", formatar_moeda_kpi(kpis['Ticket']), delta=f"{var_ticket:.1%} (QoQ)".replace(".", ","), delta_color="normal")
    
    share_br = kpis_avancados.get('Share_Nacional', 0)
    ctx_br = kpis_avancados.get('Ctx_Share_Nacional', 'N/A')
    k3.metric("🌎 Market Share (Brasil)", f"{share_br:.4f}%".replace('.', ','), help=f"**Fórmula:** Receita Op / Receita Brasil\n\n**Cálculo:** {ctx_br}")
    
    st.markdown("") 
    k4, k5, k6 = st.columns(3)

    share_grp = kpis_avancados.get('Share_Grupo', 0)
    marca = kpis_avancados.get('Marca_Grupo', 'Grupo')
    ctx_grp = kpis_avancados.get('Ctx_Share_Grupo', 'N/A')
    k4.metric(f"🏢 Share no Grupo ({marca})", f"{share_grp:.2f}%".replace('.', ','), help=f"**Fórmula:** Receita Op / Receita Grupo\n\n**Cálculo:** {ctx_grp}")
    
    cagr = kpis_avancados.get('CAGR_1Ano', 0)
    k5.metric("📈 Crescimento Anual (CAGR)", f"{cagr:.1%}".replace('.', ','), delta="12 Meses")

    # 6. Rank no Grupo (Consistente com Tabela)
    if rank_grupo_info and isinstance(rank_grupo_info, tuple):
        rank, total, _ = rank_grupo_info
        k6.metric(f"🏆 Rank no Grupo ({marca})", f"#{rank}", f"de {total} operadoras", help="Posição baseada no Revenue Score (igual à tabela).")
    else:
        k6.metric(f"🏆 Rank no Grupo", "-")

def render_lives_kpi_row(kpis, kpis_avancados, rank_grupo_info=None):
    k1, k2, k3 = st.columns(3)
    k1.metric("👥 Carteira de Vidas", f"{int(kpis['Vidas']):,}".replace(",", "."), delta=f"{kpis.get('Var_Vidas_QoQ', 0):.1%} (QoQ)".replace(".", ","), delta_color="normal")
    k2.metric("📊 Ticket Médio", formatar_moeda_kpi(kpis['Ticket']), help="Valor médio pago por vida.")
    
    share_br = kpis_avancados.get('Share_Nacional', 0)
    ctx_br = kpis_avancados.get('Ctx_Share_Nacional', 'N/A')
    k3.metric("🌎 Share Vidas (Brasil)", f"{share_br:.4f}%".replace('.', ','), help=f"**Fórmula:** Vidas Op / Vidas Brasil\n\n**Cálculo:** {ctx_br}")
    
    st.markdown("")
    k4, k5, k6 = st.columns(3)

    share_grp = kpis_avancados.get('Share_Grupo', 0)
    marca = kpis_avancados.get('Marca_Grupo', 'Grupo')
    ctx_grp = kpis_avancados.get('Ctx_Share_Grupo', 'N/A')
    k4.metric(f"🏢 Share no Grupo ({marca})", f"{share_grp:.2f}%".replace('.', ','), help=f"**Fórmula:** Vidas Op / Vidas Grupo\n\n**Cálculo:** {ctx_grp}")
    
    cagr = kpis_avancados.get('CAGR_1Ano', 0)
    k5.metric("📈 Crescimento Carteira (CAGR)", f"{cagr:.1%}".replace('.', ','), delta="12 Meses")

    # 6. Rank no Grupo (Consistente com Tabela)
    if rank_grupo_info and isinstance(rank_grupo_info, tuple):
        rank, total, _ = rank_grupo_info
        k6.metric(f"🏆 Rank no Grupo ({marca})", f"#{rank}", f"de {total} operadoras", help="Posição baseada no Lives Score (Volume + Crescimento).")
    else:
        k6.metric(f"🏆 Rank no Grupo", "-")
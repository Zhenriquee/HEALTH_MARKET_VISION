import streamlit as st

def formatar_moeda_kpi(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_kpi_row(kpis, rank_grupo_info=None):
    """Renderiza a linha de 4 métricas principais."""
    k1, k2, k3, k4 = st.columns(4)

    # 1. Vidas
    k1.metric(
        "👥 Vidas", 
        f"{int(kpis['Vidas']):,}".replace(",", "."), 
        delta=f"{kpis.get('Var_Vidas_QoQ', 0):.1%} (QoQ)",
        delta_color="normal"
    )
    
    # 2. Receita
    val_receita = formatar_moeda_kpi(kpis['Receita'])
    k2.metric(
        "💰 Receita", 
        val_receita,
        delta=f"{kpis.get('Var_Receita_QoQ', 0):.1%} (QoQ)",
        delta_color="normal"
    )

    # 3. Ticket
    val_ticket = formatar_moeda_kpi(kpis['Ticket'])
    k3.metric(
        "📊 Ticket Médio", 
        val_ticket
    )
    
    # 4. Quarto Card (Variável)
    if rank_grupo_info:
        # Se for uma tupla (rank, total, nome_grupo)
        if isinstance(rank_grupo_info, tuple):
            rank, total, nome_grupo = rank_grupo_info
            k4.metric(f"🏢 Rank {nome_grupo}", f"#{rank}", f"de {total} ops", delta_color="off")
        else:
            # Se for apenas uma string (ex: Sede)
            k4.metric("📍 Info", str(rank_grupo_info))
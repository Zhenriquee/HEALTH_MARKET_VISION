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
            k4.metric("📍 Sede", str(rank_grupo_info))

def render_revenue_kpi_row(kpis, kpis_avancados, rank_grupo_info=None):
    """
    Renderiza linha de KPIs focada em Receita com 6 indicadores.
    """
    # --- LINHA 1: Core Financeiro ---
    k1, k2, k3 = st.columns(3)

    # 1. Receita Total
    val_receita = formatar_moeda_kpi(kpis['Receita'])
    k1.metric(
        "💰 Receita Total", 
        val_receita,
        delta=f"{kpis.get('Var_Receita_QoQ', 0):.1%} (QoQ)",
        delta_color="normal"
    )

    # 2. Ticket Médio & Variação (Pricing Power)
    val_ticket = formatar_moeda_kpi(kpis['Ticket'])
    var_ticket = kpis_avancados.get('Var_Ticket', 0)
    k2.metric(
        "📊 Ticket Médio", 
        val_ticket,
        delta=f"{var_ticket:.1%} (QoQ)",
        delta_color="normal",
        help="Variação positiva indica ganho de poder de preço (Pricing Power)."
    )
    
    # 3. Market Share Nacional (Share of Wallet)
    share_br = kpis_avancados.get('Share_Nacional', 0)
    k3.metric(
        "🌎 Market Share (Brasil)", 
        f"{share_br:.4f}%",
        help="Participação na receita total do mercado brasileiro."
    )
    
    st.markdown("") # Espaçamento
    
    # --- LINHA 2: Estratégico ---
    k4, k5, k6 = st.columns(3)

    # 4. Share UF (Concentração)
    share_uf = kpis_avancados.get('Share_UF', 0)
    uf = kpis_avancados.get('UF', 'UF')
    k4.metric(
        f"📍 Share Estadual ({uf})", 
        f"{share_uf:.2f}%",
        help=f"Participação na receita total do estado de {uf}."
    )
    
    # 5. CAGR (Tendência Estrutural)
    cagr = kpis_avancados.get('CAGR_1Ano', 0)
    k5.metric(
        "📈 Crescimento Anual (CAGR)", 
        f"{cagr:.1%}",
        delta="12 Meses",
        help="Taxa de Crescimento Composto no último ano."
    )

    # 6. Volatilidade (Risco)
    vol = kpis_avancados.get('Volatilidade', 0)
    # Lógica de cor invertida para risco: muito alto pode ser ruim (vermelho), baixo é estável (verde/cinza)
    # Mas o Streamlit delta padrão: verde = positivo (cima). Vamos usar inverse_delta se quiser.
    # Aqui usaremos cor neutra (off) ou normal.
    k6.metric(
        "⚡ Volatilidade (Risco)", 
        f"{vol:.2f}%",
        help="Desvio padrão das variações de receita. Quanto maior, mais instável o fluxo de caixa.",
        delta_color="off"
    )

def render_lives_kpi_row(kpis, kpis_avancados, rank_grupo_info=None):
    """
    Renderiza linha de KPIs focada em Vidas (Volume).
    """
    k1, k2, k3 = st.columns(3)

    # 1. Vidas Totais
    k1.metric(
        "👥 Carteira de Vidas", 
        f"{int(kpis['Vidas']):,}".replace(",", "."), 
        delta=f"{kpis.get('Var_Vidas_QoQ', 0):.1%} (QoQ)",
        delta_color="normal"
    )

    # 2. Ticket Médio (Mantido como contexto financeiro da carteira)
    val_ticket = formatar_moeda_kpi(kpis['Ticket'])
    k2.metric(
        "📊 Ticket Médio", 
        val_ticket,
        help="Valor médio pago por vida."
    )
    
    # 3. Market Share Vidas
    share_br = kpis_avancados.get('Share_Nacional', 0)
    k3.metric(
        "🌎 Share Vidas (Brasil)", 
        f"{share_br:.4f}%",
        help="Participação no total de beneficiários do Brasil."
    )
    
    st.markdown("")
    
    k4, k5, k6 = st.columns(3)

    # 4. Share UF
    share_uf = kpis_avancados.get('Share_UF', 0)
    uf = kpis_avancados.get('UF', 'UF')
    k4.metric(
        f"📍 Share Vidas ({uf})", 
        f"{share_uf:.2f}%",
        help=f"Participação no total de beneficiários de {uf}."
    )
    
    # 5. CAGR Vidas
    cagr = kpis_avancados.get('CAGR_1Ano', 0)
    k5.metric(
        "📈 Crescimento Carteira (CAGR)", 
        f"{cagr:.1%}",
        delta="12 Meses",
        help="Taxa de crescimento anual composta da carteira."
    )

    # 6. Volatilidade Vidas
    vol = kpis_avancados.get('Volatilidade', 0)
    k6.metric(
        "⚡ Volatilidade Carteira", 
        f"{vol:.2f}%",
        help="Instabilidade da base de clientes (Entradas/Saídas bruscas).",
        delta_color="off"
    )    
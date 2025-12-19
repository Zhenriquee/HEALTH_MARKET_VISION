import streamlit as st
import pandas as pd

# Importando as Lógicas separadas
from backend.analytics.filtros_mercado import filtrar_por_modalidade
from backend.analytics.calculadora_score import calcular_power_score
from views.styles import aplicar_estilo_ranking

def render_panorama_mercado(df_mestre):
    # 1. Preparação Básica (Isolar último trimestre)
    ultimo_trimestre = df_mestre['ID_TRIMESTRE'].max()
    df_base = df_mestre[df_mestre['ID_TRIMESTRE'] == ultimo_trimestre].copy()

    # --- CONTROLES (UI) ---
    with st.container():
        col_filtro, col_info = st.columns([2, 1])
        with col_filtro:
            # Obtém opções para o usuario
            opcoes_modalidade = sorted(df_base['modalidade'].dropna().unique())
            
            sel_modalidade = st.multiselect(
                "📌 Filtrar por Modalidade:",
                options=opcoes_modalidade,
                placeholder="Selecione para filtrar (Vazio = Todas)"
            )
        
        with col_info:
            with st.expander("ℹ️ Entenda o Score"):
                st.markdown("$$Score = (0.5 \\times \\frac{Vidas}{MaxVidas}) + (0.5 \\times \\frac{Receita}{MaxReceita}) \\times 100$$")

    # --- CHAMADA DA REGRA DE NEGÓCIO (ANALYTICS) ---
    # Passo 1: Filtrar
    df_filtrado = filtrar_por_modalidade(df_base, sel_modalidade)

    if df_filtrado.empty:
        st.warning("Sem dados para o filtro selecionado.")
        return

    # Passo 2: Calcular Score e Ranking
    df_ranqueado = calcular_power_score(df_filtrado)
    df_ranqueado['Rank'] = df_ranqueado.index + 1
    
    # Texto de contexto para o título
    texto_contexto = f"Ranking: {', '.join(sel_modalidade)}" if sel_modalidade else "Ranking: Todo o Mercado"
    
    # Totais para Market Share (Cálculo simples de agregação para visualização)
    total_vidas = df_filtrado['NR_BENEF_T'].sum()
    total_receita = df_filtrado['VL_SALDO_FINAL'].sum()

    # --- INICIO DA PROJEÇÃO VISUAL ---
    top_1 = df_ranqueado.iloc[0]
    
    st.divider()
    st.caption(f"📅 Referência: **{ultimo_trimestre}** | 🔍 {texto_contexto}")

    # CARD DO LÍDER
    with st.container():
        c_rank, c_info = st.columns([1, 6])
        with c_rank:
            st.markdown(f"<h1 style='text-align: center; color: #DAA520; font-size: 60px; margin: 0;'>#1</h1>", unsafe_allow_html=True)
            st.caption("Líder do Filtro")
        with c_info:
            st.markdown(f"## {top_1['razao_social']}")
            st.markdown(f"**CNPJ:** {top_1['cnpj']} | **Modalidade:** {top_1['modalidade']}")
            st.progress(int(top_1['Power_Score']) / 100, text=f"Power Score: {top_1['Power_Score']:.1f}/100")

        st.divider()

        # KPIs do Líder
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # Vidas
        kpi1.metric("👥 Total de Vidas", f"{int(top_1['NR_BENEF_T']):,}".replace(",", "."))
        kpi1.caption(f"Market Share: {(top_1['NR_BENEF_T']/total_vidas)*100:.2f}%")

        # Receita
        kpi2.metric("💰 Receita Trimestral", f"R$ {top_1['VL_SALDO_FINAL']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        kpi2.caption(f"Market Share: {(top_1['VL_SALDO_FINAL']/total_receita)*100:.2f}%")

        # Ticket
        ticket = top_1['VL_SALDO_FINAL'] / top_1['NR_BENEF_T'] if top_1['NR_BENEF_T'] > 0 else 0
        kpi3.metric("📊 Ticket Médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Sede
        cidade = str(top_1.get('cidade', '')).title()
        uf = str(top_1.get('uf', ''))
        kpi4.metric("📍 Sede", f"{cidade}/{uf}")

        # Box de Liderança
        st.markdown("")
        nome_rep = str(top_1.get('representante', 'Não Informado')).title()
        if nome_rep == 'Nan': nome_rep = "Não Informado"
        
        cargo_rep = str(top_1.get('cargo_representante', 'Cargo Não Informado')).title()
        if cargo_rep == 'Nan': cargo_rep = ""

        st.info(f"**👨‍💼 Liderança Executiva:** {nome_rep} — *{cargo_rep}*")

    st.divider()

    # TABELA TOP 30
    st.subheader(f"🏆 Top 30 Operadoras - {texto_contexto}")
    
    # Seleção de Colunas
    cols_view = ['Rank', 'razao_social', 'modalidade', 'Power_Score', 'NR_BENEF_T', 'VL_SALDO_FINAL']
    df_view = df_ranqueado.head(30)[cols_view].copy()
    df_view.columns = ['Rank', 'Operadora', 'Modalidade', 'Score', 'Vidas', 'Receita (R$)']

    # Aplicação de Estilo (Visual)
    styler = aplicar_estilo_ranking(df_view)
    styler.format({'Score': "{:.1f}", 'Vidas': "{:,.0f}", 'Receita (R$)': "R$ {:,.2f}"})

    st.dataframe(styler, use_container_width=True, height=800, hide_index=True)
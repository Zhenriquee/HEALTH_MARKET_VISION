import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Importando as Lógicas
from backend.analytics.filtros_mercado import filtrar_por_modalidade
from backend.analytics.calculadora_score import calcular_power_score
from views.styles import aplicar_estilo_ranking

def render_panorama_mercado(df_mestre):
    # --- SIDEBAR: CONTROLES ---
    with st.sidebar:
        st.divider()
        st.header("⚙️ Filtros & Configuração")
        
        # 1. Filtro de Trimestre
        opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
        sel_trimestre = st.selectbox(
            "📅 Selecione o Trimestre:",
            options=opcoes_trimestre,
            index=0
        )

        st.markdown("---")

        # 2. Filtro de Modalidade
        opcoes_modalidade = sorted(df_mestre['modalidade'].dropna().unique())
        sel_modalidade = st.multiselect(
            "📌 Filtrar por Modalidade:",
            options=opcoes_modalidade,
            placeholder="Todas as Modalidades"
        )
        
        st.markdown("---")
        
        # --- GLOSSÁRIO GERAL ---
        with st.expander("📚 Glossário Geral", expanded=False):
            tab_score, tab_share, tab_evolucao, tab_spread = st.tabs(["Score", "Share", "Evolução", "Spread"])
            
            with tab_score:
                st.markdown("""
                **Power Score (0-100)**
                $$Score = (0.4 \\times Vidas) + (0.4 \\times Receita) + (0.2 \\times Perf)$$
                """)
            
            with tab_share:
                st.markdown("**Market Share (%):** Fatia de mercado que a operadora domina dentro do filtro.")
            
            with tab_evolucao:
                st.markdown("""
                **Evolução (Δ):** Variação % em relação ao trimestre anterior.
                * **Vol:** Volume de Vidas.
                * **Fin:** Financeiro (Receita).
                """)
                
            with tab_spread:
                st.markdown("""
                **Spread (Alpha):** Diferença de mérito.
                $$Spread = Operadora - Mediana$$
                
                **Cores:**
                * 🟩 **Verde:** Cresceu acima da mediana do mercado (Ganho Real).
                * 🟥 **Vermelho:** Cresceu menos que o mercado (Perda Relativa).
                
                **Siglas:**
                * **p.p. (Pontos Percentuais):** Diferença absoluta entre duas porcentagens.
                * **Mediana:** Valor central do mercado.
                """)

    # --- PROCESSAMENTO DOS DADOS ---

    # A. Filtragem de Modalidade
    df_mercado_filtrado = filtrar_por_modalidade(df_mestre, sel_modalidade)
    
    if df_mercado_filtrado.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    # B. Preparação do SNAPSHOT
    df_snapshot = df_mercado_filtrado[df_mercado_filtrado['ID_TRIMESTRE'] == sel_trimestre].copy()
    
    if df_snapshot.empty:
        st.warning(f"Não há dados disponíveis para o trimestre {sel_trimestre} com os filtros atuais.")
        return

    # C. Ranking Snapshot
    df_ranqueado = calcular_power_score(df_snapshot)
    df_ranqueado['Rank'] = df_ranqueado.index + 1
    
    # Identifica Líder
    top_1 = df_ranqueado.iloc[0]
    id_top_1 = top_1['ID_OPERADORA']
    nome_top_1 = top_1['razao_social']

    # Contexto
    texto_contexto = f"Filtro: {', '.join(sel_modalidade)}" if sel_modalidade else "Mercado Total"
    total_vidas = df_snapshot['NR_BENEF_T'].sum()
    total_receita = df_snapshot['VL_SALDO_FINAL'].sum()
    
    # Dados de Gestão (Tratamento)
    rep_nome = str(top_1.get('representante') or 'Não Informado').title()
    rep_cargo = str(top_1.get('cargo_representante') or '').title()

    # --- CARD DO LÍDER ---
    st.caption(f"📅 Referência: **{sel_trimestre}** | 🔍 {texto_contexto}")

    with st.container():
        c_rank, c_info = st.columns([1, 6])
        with c_rank:
            st.markdown(f"<h1 style='text-align: center; color: #DAA520; font-size: 60px; margin: 0;'>#1</h1>", unsafe_allow_html=True)
            st.caption("Líder do Trimestre")
        with c_info:
            st.markdown(f"## {top_1['razao_social']}")
            
            # --- AJUSTE AQUI: Gestão no Cabeçalho ---
            st.markdown(f"""
            **CNPJ:** {top_1['cnpj']} | **Modalidade:** {top_1['modalidade']}  
            👤 **Gestão:** {rep_nome} — *{rep_cargo}*
            """)
            
            st.progress(int(top_1['Power_Score']) / 100, text=f"Power Score: {top_1['Power_Score']:.1f}/100")

        st.divider()
        
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        
        k1.metric("👥 Vidas", f"{int(top_1['NR_BENEF_T']):,}".replace(",", "."), 
                  delta=f"{top_1['VAR_PCT_VIDAS']*100:.2f}% (Vol)", delta_color="normal")
        k1.caption(f"Share Vidas: {(top_1['NR_BENEF_T']/total_vidas)*100:.2f}%")

        k2.metric("💰 Receita", f"R$ {top_1['VL_SALDO_FINAL']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                  delta=f"{top_1['VAR_PCT_RECEITA']*100:.2f}% (Fin)", delta_color="normal")
        k2.caption(f"Share Receita: {(top_1['VL_SALDO_FINAL']/total_receita)*100:.2f}%")

        ticket = top_1['VL_SALDO_FINAL'] / top_1['NR_BENEF_T'] if top_1['NR_BENEF_T'] > 0 else 0
        k3.metric("📊 Ticket Médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        k4.metric("📍 Sede", f"{str(top_1.get('cidade','')).title()}/{str(top_1.get('uf',''))}")

        # Removemos o st.info antigo daqui

    st.divider()

    # --- GRÁFICOS DE SPREAD (COM TABS) ---
    st.subheader(f"📊 Performance Relativa: {nome_top_1} vs Mercado")
    
    # Criação das Abas
    tab_receita, tab_vidas = st.tabs(["💰 Spread Receita (Financeiro)", "👥 Spread Vidas (Volume)"])

    # Timeline Mestre (Compartilhada)
    timeline_completa = sorted(df_mestre['ID_TRIMESTRE'].unique())

    # ==============================
    # ABA 1: SPREAD DE RECEITA
    # ==============================
    with tab_receita:
        st.markdown("**Análise Financeira:** Diferença entre o crescimento de **Receita** da operadora e a mediana do mercado.")
        
        # 1. Série Top 1 Receita
        df_top1_rec = df_mercado_filtrado[df_mercado_filtrado['ID_OPERADORA'] == id_top_1].copy()
        df_top1_rec = df_top1_rec.set_index('ID_TRIMESTRE').reindex(timeline_completa)
        s_top1_rec_pct = df_top1_rec['VL_SALDO_FINAL'].pct_change() * 100

        # 2. Série Mercado Receita (Mediana)
        df_mkt_rec = df_mercado_filtrado.groupby('ID_TRIMESTRE')['VAR_PCT_RECEITA'].median() * 100
        s_mkt_rec_pct = df_mkt_rec.reindex(timeline_completa)
        
        # 3. Spread
        s_spread_rec = s_top1_rec_pct - s_mkt_rec_pct
        
        # 4. Plotagem
        df_graf_rec = pd.DataFrame({
            'ID_TRIMESTRE': timeline_completa,
            'SPREAD': s_spread_rec.values,
            'TOP1_PCT': s_top1_rec_pct.values,
            'MERCADO_PCT': s_mkt_rec_pct.values
        }).dropna(subset=['SPREAD']).sort_values('ID_TRIMESTRE')

        if df_graf_rec.empty:
            st.warning("Dados históricos insuficientes para Receita.")
        else:
            df_graf_rec['Cor'] = np.where(df_graf_rec['SPREAD'] >= 0, 'Superou Mercado', 'Abaixo do Mercado')
            
            fig_rec = px.bar(
                df_graf_rec, x='ID_TRIMESTRE', y='SPREAD', color='Cor',
                color_discrete_map={'Superou Mercado': '#2E8B57', 'Abaixo do Mercado': '#CD5C5C'},
                custom_data=['TOP1_PCT', 'MERCADO_PCT']
            )
            fig_rec.update_layout(
                xaxis={'categoryorder':'category ascending'},
                xaxis_title="Trimestre", yaxis_title="Spread Receita (p.p.)",
                legend_title="", hovermode="x unified", height=400,
                yaxis=dict(ticksuffix=" p.p.")
            )
            fig_rec.update_traces(
                hovertemplate="<br>".join([
                    "<b>Spread Fin: %{y:.2f} p.p.</b>",
                    "Operadora: %{customdata[0]:.2f}%",
                    "Mercado: %{customdata[1]:.2f}%"
                ])
            )
            fig_rec.add_hline(y=0, line_width=2, line_color="black")
            st.plotly_chart(fig_rec, use_container_width=True)

    # ==============================
    # ABA 2: SPREAD DE VIDAS
    # ==============================
    with tab_vidas:
        st.markdown("**Análise de Carteira:** Diferença entre o crescimento de **Vidas** da operadora e a mediana do mercado.")
        
        # 1. Série Top 1 Vidas
        df_top1_vid = df_mercado_filtrado[df_mercado_filtrado['ID_OPERADORA'] == id_top_1].copy()
        df_top1_vid = df_top1_vid.set_index('ID_TRIMESTRE').reindex(timeline_completa)
        s_top1_vid_pct = df_top1_vid['NR_BENEF_T'].pct_change() * 100

        # 2. Série Mercado Vidas (Mediana)
        df_mkt_vid = df_mercado_filtrado.groupby('ID_TRIMESTRE')['VAR_PCT_VIDAS'].median() * 100
        s_mkt_vid_pct = df_mkt_vid.reindex(timeline_completa)
        
        # 3. Spread
        s_spread_vid = s_top1_vid_pct - s_mkt_vid_pct
        
        # 4. Plotagem
        df_graf_vid = pd.DataFrame({
            'ID_TRIMESTRE': timeline_completa,
            'SPREAD': s_spread_vid.values,
            'TOP1_PCT': s_top1_vid_pct.values,
            'MERCADO_PCT': s_mkt_vid_pct.values
        }).dropna(subset=['SPREAD']).sort_values('ID_TRIMESTRE')

        if df_graf_vid.empty:
            st.warning("Dados históricos insuficientes para Vidas.")
        else:
            df_graf_vid['Cor'] = np.where(df_graf_vid['SPREAD'] >= 0, 'Superou Mercado', 'Abaixo do Mercado')
            
            fig_vid = px.bar(
                df_graf_vid, x='ID_TRIMESTRE', y='SPREAD', color='Cor',
                color_discrete_map={'Superou Mercado': '#2E8B57', 'Abaixo do Mercado': '#CD5C5C'},
                custom_data=['TOP1_PCT', 'MERCADO_PCT']
            )
            fig_vid.update_layout(
                xaxis={'categoryorder':'category ascending'},
                xaxis_title="Trimestre", yaxis_title="Spread Vidas (p.p.)",
                legend_title="", hovermode="x unified", height=400,
                yaxis=dict(ticksuffix=" p.p.")
            )
            fig_vid.update_traces(
                hovertemplate="<br>".join([
                    "<b>Spread Vol: %{y:.2f} p.p.</b>",
                    "Operadora: %{customdata[0]:.2f}%",
                    "Mercado: %{customdata[1]:.2f}%"
                ])
            )
            fig_vid.add_hline(y=0, line_width=2, line_color="black")
            st.plotly_chart(fig_vid, use_container_width=True)

    st.divider()

    # --- TABELA TOP 30 (Mantida) ---
    st.subheader(f"🏆 Ranking do Trimestre {sel_trimestre}")
    
    cols_view = ['Rank', 'razao_social', 'modalidade', 'Power_Score', 'NR_BENEF_T', 'VAR_PCT_VIDAS', 'VL_SALDO_FINAL', 'VAR_PCT_RECEITA']
    df_view = df_ranqueado.head(30)[cols_view].copy()
    
    df_view.columns = ['Rank', 'Operadora', 'Modalidade', 'Score', 'Vidas', 'Δ Vol (%)', 'Receita (R$)', 'Δ Fin (%)']

    styler = aplicar_estilo_ranking(df_view)
    
    styler.format({
        'Score': "{:.1f}", 
        'Vidas': "{:,.0f}", 
        'Δ Vol (%)': "{:.2%}", 
        'Receita (R$)': "R$ {:,.2f}",
        'Δ Fin (%)': "{:.2%}" 
    })

    st.dataframe(styler, use_container_width=True, height=800, hide_index=True)
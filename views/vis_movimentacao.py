import streamlit as st
import plotly.express as px
import pandas as pd
from backend.analytics.movimentacao_mercado import calcular_fluxo_entrada_saida, gerar_analise_impacto
from views.components.tables import formatar_moeda_br

# Imports dos Componentes Visuais (Padrão Sidebar)
from views.components.sidebar_header import render_sidebar_header
from views.components.footer import render_sidebar_footer
from views.components.glossary import render_glossary

def render_movimentacao_mercado(df_mestre):
    # --- 1. CONTROLLER (Sidebar) ---
    with st.sidebar:
        render_sidebar_header()
        st.divider()
        st.header("⚙️ Configuração")
        
        # Filtros de Trimestre
        try:
            lista_trimestres = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
            
            tri_atual = st.selectbox(
                "📅 Trimestre Referência (B):", 
                lista_trimestres, 
                index=0,
                help="Trimestre mais recente (Onde as operadoras entraram ou saíram)."
            )   
            
            idx_anterior = 1 if len(lista_trimestres) > 1 else 0
            tri_anterior = st.selectbox(
                "📅 Trimestre Comparativo (A):", 
                lista_trimestres, 
                index=idx_anterior,
                help="Trimestre base (Quem estava aqui e não está mais?)"
            )
        except Exception:
            st.error("Erro ao carregar lista de trimestres.")
            return

        st.markdown("---")
        render_glossary()
        render_sidebar_footer()

    # --- 2. ÁREA PRINCIPAL ---
    st.header("🔄 Movimentação de Mercado (Entradas & Saídas)")
    st.markdown(f"Análise de fluxo entre **{tri_anterior}** (A) e **{tri_atual}** (B).")
    
    # Validação Básica
    if tri_atual == tri_anterior:
        st.warning("⚠️ Selecione trimestres diferentes na barra lateral para realizar a comparação.")
        return

    # --- Processamento ---
    df_entrantes, df_saintes = calcular_fluxo_entrada_saida(df_mestre, tri_atual, tri_anterior)
    analise = gerar_analise_impacto(df_entrantes, df_saintes)
    imp_geral = analise['Geral']
    imp_unimed = analise['Unimed']

    # --- Seção 1: Resumo de Impacto Comparativo ---
    st.subheader("1. Impacto de Mercado vs. Rede Unimed")
    
    t1, t2 = st.tabs(["🌎 Impacto Mercado Geral", "🌲 Impacto Rede Unimed"])
    
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vidas Ganhas", f"{imp_geral['Vidas_Ganhas']:,.0f}".replace(",", "."), help="Soma de vidas das operadoras que entraram")
        c2.metric("Vidas Perdidas", f"{imp_geral['Vidas_Perdidas']:,.0f}".replace(",", "."), delta_color="inverse", help="Soma de vidas (no trimestre anterior) das que saíram")
        
        # Saldo Vidas Geral
        saldo_v = imp_geral['Saldo_Vidas']
        pct_v = imp_geral['Pct_Saldo_Vidas']
        c3.metric(
            "Saldo Líquido Vidas", 
            f"{saldo_v:+,.0f}".replace(",", "."), 
            delta=f"{pct_v:+.2%}".replace(".", ","),
            help="Diferença absoluta e variação percentual."
        )
        
        # Saldo Receita Geral
        saldo_r = imp_geral['Saldo_Receita']
        pct_r = imp_geral['Pct_Saldo_Receita']
        c4.metric(
            "Saldo Líquido Receita", 
            formatar_moeda_br(saldo_r), 
            delta=f"{pct_r:+.2%}".replace(".", ","),
            help="Diferença absoluta e variação percentual."
        )

    with t2:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Unimeds Entrantes", imp_unimed['Qtd_Entrou'])
        c2.metric("Unimeds Saintes", imp_unimed['Qtd_Saiu'], delta_color="inverse")
        
        # Saldo Vidas Unimed
        saldo_v_uni = imp_unimed['Saldo_Vidas']
        pct_v_uni = imp_unimed['Pct_Saldo_Vidas']
        c3.metric(
            "Saldo Vidas Unimed", 
            f"{saldo_v_uni:+,.0f}".replace(",", "."), 
            delta=f"{pct_v_uni:+.2%}".replace(".", ",")
        )
        
        # Saldo Receita Unimed
        saldo_r_uni = imp_unimed['Saldo_Receita']
        pct_r_uni = imp_unimed['Pct_Saldo_Receita']
        c4.metric(
            "Saldo Receita Unimed", 
            formatar_moeda_br(saldo_r_uni), 
            delta=f"{pct_r_uni:+.2%}".replace(".", ",")
        )

    st.divider()

    # --- Função Auxiliar de Formatação ---
    def preparar_tabela_exibicao(df):
        if df.empty: return df
        
        cols_map = {
            'ID_OPERADORA': 'Registro ANS', 
            'razao_social': 'Razão Social', 
            'uf': 'UF', 
            'NR_BENEF_T': 'Vidas',
            'VL_SALDO_FINAL': 'Receita (R$)',
            'descredenciada_em': 'Data Descred.',
            'descredenciamento_motivo': 'Motivo'
        }
        
        cols_presentes = [c for c in cols_map.keys() if c in df.columns]
        df_show = df[cols_presentes].copy()
        
        # Formatações
        if 'NR_BENEF_T' in df_show.columns:
            df_show['NR_BENEF_T'] = pd.to_numeric(df_show['NR_BENEF_T'], errors='coerce').fillna(0)
            df_show['NR_BENEF_T'] = df_show['NR_BENEF_T'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            
        if 'VL_SALDO_FINAL' in df_show.columns:
            df_show['VL_SALDO_FINAL'] = pd.to_numeric(df_show['VL_SALDO_FINAL'], errors='coerce').fillna(0)
            df_show['VL_SALDO_FINAL'] = df_show['VL_SALDO_FINAL'].apply(formatar_moeda_br)

        if 'descredenciada_em' in df_show.columns:
            df_show['descredenciada_em'] = pd.to_datetime(df_show['descredenciada_em'], errors='coerce')
            df_show['descredenciada_em'] = df_show['descredenciada_em'].dt.strftime('%d/%m/%Y').fillna("-")
            
        return df_show.rename(columns=cols_map)

    # --- Seção 2: Monitoramento Detalhado UNIMED ---
    st.subheader("2. Detalhe Rede Unimed")
    
    col_u_entrou, col_u_saiu = st.columns(2)

    with col_u_entrou:
        st.info(f"🟢 **Unimeds que Entraram** ({imp_unimed['Qtd_Entrou']})")
        if not imp_unimed['Entrantes_DF'].empty:
            st.dataframe(preparar_tabela_exibicao(imp_unimed['Entrantes_DF']), hide_index=True, width='stretch')
        else:
            st.caption("Nenhuma entrada registrada.")

    with col_u_saiu:
        st.error(f"🔴 **Unimeds que Saíram** ({imp_unimed['Qtd_Saiu']})")
        if not imp_unimed['Saintes_DF'].empty:
            st.dataframe(preparar_tabela_exibicao(imp_unimed['Saintes_DF']), hide_index=True, width='stretch')
        else:
            st.caption("Nenhuma saída registrada.")

    st.divider()

    # --- Seção 3: Listagem Geral do Mercado ---
    st.subheader("3. Listagem Geral do Mercado")
    
    tab_e, tab_s = st.tabs([f"Entrantes Gerais ({len(df_entrantes)})", f"Saídas Gerais ({len(df_saintes)})"])
    
    with tab_e:
        if not df_entrantes.empty:
            st.dataframe(preparar_tabela_exibicao(df_entrantes), width="stretch", hide_index=True)
        else:
            st.info("Sem entrantes no período.")

    with tab_s:
        if not df_saintes.empty:
            st.markdown(f"ℹ️ *Dados financeiros e de vidas referentes ao último reporte em {tri_anterior}.*")
            st.dataframe(preparar_tabela_exibicao(df_saintes), width="stretch", hide_index=True)
        else:
            st.info("Sem saídas no período.")
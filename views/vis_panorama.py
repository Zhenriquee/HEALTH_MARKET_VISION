import streamlit as st
import traceback # Para logar erros detalhados se necessário

# Imports da Arquitetura Limpa
from backend.use_cases.market_overview import MarketOverviewUseCase
from backend.exceptions import AppError

# Imports dos Componentes Visuais (Mantidos)
from views.components.header import render_header
from views.components.metrics import render_kpi_row
from views.components.charts import render_spread_chart
from views.components.tables import render_styled_ranking_table
from views.components.glossary import render_glossary

def render_panorama_mercado(df_mestre):
    # --- 1. CONFIGURAÇÃO (Inputs do Usuário) ---
    with st.sidebar:
        st.divider()
        st.header("⚙️ Filtros & Configuração")
        
        # Filtro Trimestre
        try:
            opcoes_trimestre = sorted(df_mestre['ID_TRIMESTRE'].unique(), reverse=True)
            sel_trimestre = st.selectbox("📅 Selecione o Trimestre:", options=opcoes_trimestre, index=0)
        except Exception:
            st.error("Erro ao carregar lista de trimestres. Verifique a base de dados.")
            return

        st.markdown("---")
        
        # Filtro Modalidade
        try:
            opcoes_modalidade = sorted(df_mestre['modalidade'].dropna().unique())
            sel_modalidade = st.multiselect("📌 Filtrar por Modalidade:", options=opcoes_modalidade, placeholder="Todas as Modalidades")
        except Exception:
            st.error("Erro ao carregar lista de modalidades.")
            return
        
        st.markdown("---")
        render_glossary()

    # --- 2. EXECUÇÃO DO CASO DE USO (Processamento) ---
    try:
        # Instancia o Caso de Uso
        use_case = MarketOverviewUseCase(df_mestre)
        
        # Executa a lógica (aqui ocorrem os cálculos, filtros e validações)
        resultado = use_case.execute(trimestre=sel_trimestre, modalidades=sel_modalidade)
        
        # Desempacota os dados retornados (ViewModel)
        lider = resultado['lider']
        top_30 = resultado['ranking_top_30']
        texto_contexto = resultado['contexto_filtro']
        # Atualiza a referência do df_mestre local caso o UseCase tenha enriquecido dados (ex: Marcas)
        df_mestre_enriched = resultado['df_mestre_atualizado'] 

    except AppError as e:
        # Erros de negócio esperados (ex: Filtro vazio)
        st.warning(f"Atenção: {str(e)}")
        return
    except Exception as e:
        # Erros críticos de sistema
        st.error(f"Ocorreu um erro crítico ao processar o painel: {str(e)}")
        with st.expander("Ver detalhes técnicos"):
            st.code(traceback.format_exc())
        return

    # --- 3. RENDERIZAÇÃO (Visualização) ---
    
    # Cabeçalho de Contexto
    st.caption(f"📅 Referência: **{sel_trimestre}** | 🔍 {texto_contexto}")

    # 1. Header do Líder
    render_header(lider['dados'], 1, lider['dados']['Power_Score'])

    st.divider()
    
    # 2. KPIs do Líder
    # Adaptador para o componente render_kpi_row (que espera dicionário de KPIs)
    # Aqui passamos a 'Sede' no parâmetro opcional rank_grupo_info para preencher o 4º card
    render_kpi_row(lider['kpis'], rank_grupo_info=lider['kpis']['Sede'])
    
    st.divider()

    # 3. Gráficos de Performance Relativa (Spread)
    st.subheader(f"📊 Performance Relativa: {lider['dados']['razao_social']} vs Mercado")
    
    tab_rec, tab_vid = st.tabs(["💰 Spread Receita", "👥 Spread Vidas"])
    
    with tab_rec:
        fig = render_spread_chart(
            df_mestre_enriched, # Usa o DF enriquecido pelo UseCase
            lider['id'], 
            lider['dados']['razao_social'], 
            "Receita", 
            "Mercado Geral"
        )
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("Dados insuficientes para gerar gráfico de receita.")
    
    with tab_vid:
        fig = render_spread_chart(
            df_mestre_enriched, 
            lider['id'], 
            lider['dados']['razao_social'], 
            "Vidas", 
            "Mercado Geral"
        )
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("Dados insuficientes para gerar gráfico de vidas.")

    st.divider()

    # 4. Tabela de Ranking (Estilizada)
    render_styled_ranking_table(
        top_30, 
        titulo=f"🏆 Top 30 Ranking do Trimestre {sel_trimestre}"
    )
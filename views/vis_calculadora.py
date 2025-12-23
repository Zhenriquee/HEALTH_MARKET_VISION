import streamlit as st
import pandas as pd
import numpy as np

from backend.use_cases.calculation_explainer import CalculationExplainerUseCase
from views.components.tables import formatar_moeda_br

def render_calculadora_didatica(df_mestre):
    st.header("🧮 Memória de Cálculo")
    st.caption("Auditoria detalhada dos indicadores da operadora selecionada.")
    
    # Validação
    if "filtro_id_op" not in st.session_state or "filtro_trimestre" not in st.session_state:
        st.warning("⚠️ Selecione uma operadora na tela 'Raio-X' primeiro.")
        return
        
    id_op = st.session_state["filtro_id_op"]
    trimestre = st.session_state["filtro_trimestre"]
    
    use_case = CalculationExplainerUseCase(df_mestre)
    try:
        resultado = use_case.execute(id_op, trimestre)
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
        return
        
    dados = resultado['dados_op']
    ps = resultado['passos_score']
    ex = resultado['extras']
    
    st.subheader(f"Operadora: {dados['razao_social']}")
    
    # --- ABAS DE NAVEGAÇÃO ---
    tab_score, tab_spread, tab_grupo = st.tabs(["⚡ Power Score", "📊 Performance Relativa", "🏢 Métricas de Grupo"])
    
    # --- ABA 1: POWER SCORE (Lógica já existente mantida aqui) ---
    with tab_score:
        st.info(f"O Power Score final é **{ps['final']:.1f}/100**.")
        
        with st.expander("1. Detalhe Vidas (40%)", expanded=False):
            st.latex(r"Score = \frac{Log(Vidas) - Log(Min)}{Log(Max) - Log(Min)}")
            st.code(f"({ps['vidas']['log']:.4f} - {ps['vidas']['min']:.4f}) / ({ps['vidas']['max']:.4f} - {ps['vidas']['min']:.4f}) = {ps['vidas']['score']:.2f}", language="text")

        with st.expander("2. Detalhe Receita (40%)", expanded=False):
            st.latex(r"Score = \frac{Log(Receita) - Log(Min)}{Log(Max) - Log(Min)}")
            st.code(f"({ps['receita']['log']:.4f} - {ps['receita']['min']:.4f}) / ({ps['receita']['max']:.4f} - {ps['receita']['min']:.4f}) = {ps['receita']['score']:.2f}", language="text")
            
        with st.expander("3. Detalhe Performance (20%)", expanded=False):
            st.latex(r"Score = \frac{Cresc - Min}{Max - Min}")
            st.code(f"({ps['perf']['clip']:.4f} - {ps['perf']['min']:.4f}) / ({ps['perf']['max']:.4f} - {ps['perf']['min']:.4f}) = {ps['perf']['score']:.2f}", language="text")

    # --- ABA 2: PERFORMANCE RELATIVA (Novos Cálculos) ---
    with tab_spread:
        st.markdown("### Como calculamos o Spread (Diferencial)?")
        st.markdown("Comparamos o crescimento da operadora (QoQ) contra a **mediana do mercado**.")
        st.latex(r"Spread = \Delta\%_{Operadora} - \Delta\%_{MedianaMercado}")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        
        # Spread Receita
        with c1:
            st.subheader("💰 Spread de Receita")
            sr = ex['spread_receita']
            
            st.metric("Cresc. Operadora", f"{sr['op']:+.2%}")
            st.metric("Mediana Mercado", f"{sr['mkt']:+.2%}")
            st.metric("Resultado (Spread)", f"{sr['res']:+.2f} p.p.", delta_color="off")
            
            st.code(f"""
{sr['op']:.4f} (Op)
- {sr['mkt']:.4f} (Mkt)
----------------
= {sr['res']:.4f} ({sr['res']*100:.2f} p.p.)
            """, language="text")
            
        # Spread Vidas
        with c2:
            st.subheader("👥 Spread de Vidas")
            sv = ex['spread_vidas']
            
            st.metric("Cresc. Operadora", f"{sv['op']:+.2%}")
            st.metric("Mediana Mercado", f"{sv['mkt']:+.2%}")
            st.metric("Resultado (Spread)", f"{sv['res']:+.2f} p.p.", delta_color="off")
            
            st.code(f"""
{sv['op']:.4f} (Op)
- {sv['mkt']:.4f} (Mkt)
----------------
= {sv['res']:.4f} ({sv['res']*100:.2f} p.p.)
            """, language="text")

    # --- ABA 3: MÉTRICAS DE GRUPO (Novos Cálculos) ---
    with tab_grupo:
        grp = ex['grupo']
        st.markdown(f"### Análise do Grupo: **{grp['marca']}**")
        
        col_share, col_cresc = st.columns(2)
        
        # 1. Share no Grupo
        with col_share:
            st.subheader("🍰 Share no Grupo (Receita)")
            st.caption("Quanto a operadora representa financeiramente dentro do grupo.")
            
            st.latex(r"Share = \frac{Receita_{Operadora}}{\sum Receita_{Grupo}}")
            
            st.metric("Receita Operadora", formatar_moeda_br(grp['total_op_rec']))
            st.metric("Total do Grupo", formatar_moeda_br(grp['total_grp_rec']))
            st.metric("Share Calculado", f"{grp['share_rec']:.2f}%")
            
            st.code(f"""
{grp['total_op_rec']:.2f}
/ {grp['total_grp_rec']:.2f}
= {grp['share_rec']/100:.4f} ({grp['share_rec']:.2f}%)
            """, language="text")
            
        # 2. Crescimento Médio do Grupo
        with col_cresc:
            st.subheader("📈 Cresc. Vidas (Média Grupo)")
            st.caption("Mediana do crescimento de vidas de todas as operadoras deste grupo.")
            
            st.latex(r"Média = Mediana(\{ \Delta\%_{Op1}, \Delta\%_{Op2}, ... \})")
            
            st.metric("Crescimento da Operadora", f"{ex['spread_vidas']['op']:+.2%}")
            st.metric("Mediana do Grupo", f"{grp['mediana_cresc_vid']:+.2%}")
            
            diff_grp = ex['spread_vidas']['op'] - grp['mediana_cresc_vid']
            st.caption(f"A operadora está {diff_grp:+.2f} p.p. em relação ao grupo.")
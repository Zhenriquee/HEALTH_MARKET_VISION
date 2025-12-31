import streamlit as st
import pandas as pd
from views.styles import aplicar_estilo_ranking

def formatar_moeda_br(valor):
    """Converte float para string R$ X.XXX,XX"""
    if pd.isna(valor): return "-"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render_styled_ranking_table(df, titulo=None):
    """
    Renderiza a tabela COLORIDA (usada no Panorama) com formatação BR.
    """
    if titulo: st.subheader(titulo)
    
    # 1. Seleção e Renomeação de Colunas
    cols_map = {
        '#': 'Rank',
        'razao_social': 'Operadora',
        'modalidade': 'Modalidade',
        'Power_Score': 'Score',
        'NR_BENEF_T': 'Vidas',
        'VAR_PCT_VIDAS': 'Δ Vol (%)',
        'VL_SALDO_FINAL': 'Receita (R$)',
        'VAR_PCT_RECEITA': 'Δ Fin (%)'
    }
    
    # Filtra colunas existentes e renomeia
    cols_uteis = [c for c in cols_map.keys() if c in df.columns]
    df_view = df[cols_uteis].rename(columns=cols_map).copy()
    
    # 2. Aplica Estilo (Cores)
    styler = aplicar_estilo_ranking(df_view)
    
    # 3. Formatação de Valores (Moeda BR e Percentual)
    styler.format({
        'Rank': "{:.0f}",
        'Score': "{:.1f}",
        'Vidas': "{:,.0f}", 
        'Δ Vol (%)': "{:.2%}",
        'Δ Fin (%)': "{:.2%}",
        'Receita (R$)': formatar_moeda_br 
    })
    
    # 4. Renderiza (CORRIGIDO AQUI: width="stretch")
    st.dataframe(styler, width="stretch", height=800, hide_index=True)

def render_ranking_table(df, titulo=None, subtitulo=None):
    """
    Renderiza a tabela PADRÃO (Branca, usada na Análise) com formatação BR.
    """
    if titulo: st.subheader(titulo)
    if subtitulo: st.markdown(subtitulo)
    
    cols_map = {
        'razao_social': 'Operadora', 'uf': 'UF', 
        'Power_Score': 'Score', 'NR_BENEF_T': 'Vidas', 
        'VL_SALDO_FINAL': 'Receita (R$)'
    }
    
    if '#' in df.columns: cols_map['#'] = 'Rank'
    elif 'Rank_Geral' in df.columns: cols_map['Rank_Geral'] = 'Rank'
    elif 'Rank_Grupo' in df.columns: cols_map['Rank_Grupo'] = 'Rank'
    
    cols_presentes = [c for c in cols_map.keys() if c in df.columns]
    df_view = df[cols_presentes].rename(columns=cols_map).copy()
    
    styler = df_view.style.format({
        'Rank': "{:.0f}",
        'Score': "{:.1f}",
        'Vidas': "{:.0f}",
        'Receita (R$)': formatar_moeda_br
    })

    # (CORRIGIDO AQUI: width="stretch")
    st.dataframe(styler, width="stretch", hide_index=True)
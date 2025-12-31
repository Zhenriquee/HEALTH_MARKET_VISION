import pandas as pd
import numpy as np
from backend.analytics.brand_intelligence import extrair_marca

# --- Funções Auxiliares de Formatação ---
def _fmt_reais(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def _fmt_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except:
        return "0"

def obter_trimestres_anteriores(trimestre_atual):
    try:
        ano, tri = trimestre_atual.split('-')
        ano = int(ano)
        tri_num = int(tri.replace('T', ''))
        if tri_num == 1:
            tri_prev_q = f"{ano-1}-T4"
        else:
            tri_prev_q = f"{ano}-T{tri_num-1}"
        tri_prev_y = f"{ano-1}-T{tri_num}"
        return tri_prev_q, tri_prev_y
    except:
        return None, None

def calcular_variacoes_operadora(df, id_operadora, trimestre_atual):
    # Normaliza ID para busca
    id_busca = str(id_operadora).split('.')[0].strip().zfill(6)
    
    # Garante que o DF também tenha IDs normalizados (caso não tenha vindo do DataEngine)
    df = df.copy()
    df['ID_OPERADORA'] = df['ID_OPERADORA'].apply(lambda x: str(x).split('.')[0].strip().zfill(6))
    
    df_op = df[df['ID_OPERADORA'] == id_busca].set_index('ID_TRIMESTRE')
    
    if trimestre_atual not in df_op.index:
        return None

    atual = df_op.loc[trimestre_atual]
    tri_prev_q, tri_prev_y = obter_trimestres_anteriores(trimestre_atual)
    
    dados_prev_q = df_op.loc[tri_prev_q] if tri_prev_q in df_op.index else None
    dados_prev_y = df_op.loc[tri_prev_y] if tri_prev_y in df_op.index else None

    kpis = {
        'Vidas': atual['NR_BENEF_T'],
        'Receita': atual['VL_SALDO_FINAL'],
        'Ticket': atual['VL_SALDO_FINAL'] / atual['NR_BENEF_T'] if atual['NR_BENEF_T'] > 0 else 0,
        'Val_Vidas_QoQ': dados_prev_q['NR_BENEF_T'] if dados_prev_q is not None else 0,
        'Val_Receita_QoQ': dados_prev_q['VL_SALDO_FINAL'] if dados_prev_q is not None else 0,
        'Val_Vidas_YoY': dados_prev_y['NR_BENEF_T'] if dados_prev_y is not None else 0,
        'Val_Receita_YoY': dados_prev_y['VL_SALDO_FINAL'] if dados_prev_y is not None else 0,
        'Var_Vidas_QoQ': 0.0, 'Var_Receita_QoQ': 0.0, 'Var_Vidas_YoY': 0.0, 'Var_Receita_YoY': 0.0,
        'Ref_QoQ': tri_prev_q, 'Ref_YoY': tri_prev_y
    }

    if dados_prev_q is not None:
        if dados_prev_q['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_QoQ'] = (atual['NR_BENEF_T'] - dados_prev_q['NR_BENEF_T']) / dados_prev_q['NR_BENEF_T']
        if dados_prev_q['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_QoQ'] = (atual['VL_SALDO_FINAL'] - dados_prev_q['VL_SALDO_FINAL']) / dados_prev_q['VL_SALDO_FINAL']

    if dados_prev_y is not None:
        if dados_prev_y['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_YoY'] = (atual['NR_BENEF_T'] - dados_prev_y['NR_BENEF_T']) / dados_prev_y['NR_BENEF_T']
        if dados_prev_y['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_YoY'] = (atual['VL_SALDO_FINAL'] - dados_prev_y['VL_SALDO_FINAL']) / dados_prev_y['VL_SALDO_FINAL']

    return kpis

def calcular_kpis_financeiros_avancados(df_mestre, id_operadora, trimestre_atual):
    # Normaliza ID
    id_busca = str(id_operadora).split('.')[0].strip().zfill(6)
    df_mestre = df_mestre.copy()
    df_mestre['ID_OPERADORA'] = df_mestre['ID_OPERADORA'].apply(lambda x: str(x).split('.')[0].strip().zfill(6))

    df_op = df_mestre[df_mestre['ID_OPERADORA'] == id_busca].copy()
    df_hist_window = df_op[df_op['ID_TRIMESTRE'] <= trimestre_atual].sort_values('ID_TRIMESTRE')
    
    if df_hist_window.empty or df_hist_window.iloc[-1]['ID_TRIMESTRE'] != trimestre_atual:
        return None
        
    row_atual = df_hist_window.iloc[[-1]]
    df_tri_mercado = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre_atual].copy()
    
    receita_op = row_atual['VL_SALDO_FINAL'].values[0]
    vidas_op = row_atual['NR_BENEF_T'].values[0]
    razao_social = row_atual['razao_social'].values[0]
    
    # Share Nacional
    total_receita_br = df_tri_mercado['VL_SALDO_FINAL'].sum()
    share_br = (receita_op / total_receita_br) * 100 if total_receita_br > 0 else 0
    ctx_share_br = f"{_fmt_reais(receita_op)} (Op)  /  {_fmt_reais(total_receita_br)} (Total BR)"
    
    # Share Grupo
    marca_op = extrair_marca(razao_social, id_busca)
    df_tri_mercado['Marca_Temp'] = df_tri_mercado.apply(
        lambda x: extrair_marca(x['razao_social'], x['ID_OPERADORA']), axis=1
    )
    df_grupo = df_tri_mercado[df_tri_mercado['Marca_Temp'] == marca_op].copy()
    total_receita_grupo = df_grupo['VL_SALDO_FINAL'].sum()
    share_grupo = (receita_op / total_receita_grupo) * 100 if total_receita_grupo > 0 else 0
    ctx_share_grupo = f"{_fmt_reais(receita_op)} (Op)  /  {_fmt_reais(total_receita_grupo)} (Total {marca_op})"
    
    # Ranking Financeiro (Volume)
    df_grupo['Rank_Fin'] = df_grupo['VL_SALDO_FINAL'].rank(ascending=False, method='min')
    try:
        rank_grupo = int(df_grupo[df_grupo['ID_OPERADORA'] == id_busca]['Rank_Fin'].iloc[0])
    except:
        rank_grupo = "-"
    total_grupo = len(df_grupo)
    
    # KPIs Avançados
    ticket_atual = receita_op / vidas_op if vidas_op > 0 else 0
    if len(df_hist_window) >= 2:
        row_prev = df_hist_window.iloc[-2]
        ticket_prev = row_prev['VL_SALDO_FINAL'] / row_prev['NR_BENEF_T'] if row_prev['NR_BENEF_T'] > 0 else 0
        var_ticket = (ticket_atual / ticket_prev) - 1 if ticket_prev > 0 else 0
    else: var_ticket = 0
    
    df_cagr_window = df_hist_window.tail(5)
    cagr = (df_cagr_window.iloc[-1]['VL_SALDO_FINAL'] / df_cagr_window.iloc[0]['VL_SALDO_FINAL']) - 1 if len(df_cagr_window) >= 5 and df_cagr_window.iloc[0]['VL_SALDO_FINAL'] > 0 else 0
    volatilidade = df_hist_window.tail(8)['VAR_PCT_RECEITA'].std() * 100
    if pd.isna(volatilidade): volatilidade = 0

    return {
        'Share_Nacional': share_br, 'Ctx_Share_Nacional': ctx_share_br,
        'Share_Grupo': share_grupo, 'Ctx_Share_Grupo': ctx_share_grupo, 'Marca_Grupo': marca_op,
        'Rank_Grupo': rank_grupo, 'Total_Grupo': total_grupo,
        'Var_Ticket': var_ticket, 'CAGR_1Ano': cagr, 'Volatilidade': volatilidade
    }

def calcular_kpis_vidas_avancados(df_mestre, id_operadora, trimestre_atual):
    # Normaliza ID
    id_busca = str(id_operadora).split('.')[0].strip().zfill(6)
    df_mestre = df_mestre.copy()
    df_mestre['ID_OPERADORA'] = df_mestre['ID_OPERADORA'].apply(lambda x: str(x).split('.')[0].strip().zfill(6))

    df_op = df_mestre[df_mestre['ID_OPERADORA'] == id_busca].copy()
    df_hist_window = df_op[df_op['ID_TRIMESTRE'] <= trimestre_atual].sort_values('ID_TRIMESTRE')
    
    if df_hist_window.empty or df_hist_window.iloc[-1]['ID_TRIMESTRE'] != trimestre_atual:
        return None
        
    row_atual = df_hist_window.iloc[[-1]]
    df_tri_mercado = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre_atual].copy()
    
    vidas_op = row_atual['NR_BENEF_T'].values[0]
    razao_social = row_atual['razao_social'].values[0]
    
    # Share Nacional
    total_vidas_br = df_tri_mercado['NR_BENEF_T'].sum()
    share_br = (vidas_op / total_vidas_br) * 100 if total_vidas_br > 0 else 0
    ctx_share_br = f"{_fmt_numero(vidas_op)} (Op)  /  {_fmt_numero(total_vidas_br)} (Total BR)"
    
    # Share Grupo
    marca_op = extrair_marca(razao_social, id_busca)
    df_tri_mercado['Marca_Temp'] = df_tri_mercado.apply(
        lambda x: extrair_marca(x['razao_social'], x['ID_OPERADORA']), axis=1
    )
    df_grupo = df_tri_mercado[df_tri_mercado['Marca_Temp'] == marca_op].copy()
    total_vidas_grupo = df_grupo['NR_BENEF_T'].sum()
    share_grupo = (vidas_op / total_vidas_grupo) * 100 if total_vidas_grupo > 0 else 0
    ctx_share_grupo = f"{_fmt_numero(vidas_op)} (Op)  /  {_fmt_numero(total_vidas_grupo)} (Total {marca_op})"
    
    # Ranking Vidas (Volume)
    df_grupo['Rank_Vid'] = df_grupo['NR_BENEF_T'].rank(ascending=False, method='min')
    try:
        rank_grupo = int(df_grupo[df_grupo['ID_OPERADORA'] == id_busca]['Rank_Vid'].iloc[0])
    except:
        rank_grupo = "-"
    total_grupo = len(df_grupo)
    
    # KPIs
    df_cagr_window = df_hist_window.tail(5)
    cagr = (df_cagr_window.iloc[-1]['NR_BENEF_T'] / df_cagr_window.iloc[0]['NR_BENEF_T']) - 1 if len(df_cagr_window) >= 5 and df_cagr_window.iloc[0]['NR_BENEF_T'] > 0 else 0
    
    volatilidade = df_hist_window.tail(8)['VAR_PCT_VIDAS'].std() * 100
    if pd.isna(volatilidade): volatilidade = 0

    return {
        'Share_Nacional': share_br, 'Ctx_Share_Nacional': ctx_share_br,
        'Share_Grupo': share_grupo, 'Ctx_Share_Grupo': ctx_share_grupo, 'Marca_Grupo': marca_op,
        'Rank_Grupo': rank_grupo, 'Total_Grupo': total_grupo,
        'CAGR_1Ano': cagr, 'Volatilidade': volatilidade
    }
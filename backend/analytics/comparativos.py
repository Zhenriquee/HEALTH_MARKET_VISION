import pandas as pd
import numpy as np


def obter_trimestres_anteriores(trimestre_atual):
    """
    Retorna o Trimestre Anterior (QoQ) e o Mesmo Trimestre do Ano Anterior (YoY).
    Entrada: '2023-T2' -> Saída: ('2023-T1', '2022-T2')
    """
    try:
        ano, tri = trimestre_atual.split('-')
        ano = int(ano)
        tri_num = int(tri.replace('T', ''))

        # Cálculo QoQ (Trimestre Anterior)
        if tri_num == 1:
            tri_prev_q = f"{ano-1}-T4"
        else:
            tri_prev_q = f"{ano}-T{tri_num-1}"

        # Cálculo YoY (Ano Anterior)
        tri_prev_y = f"{ano-1}-T{tri_num}"

        return tri_prev_q, tri_prev_y
    except:
        return None, None

def calcular_variacoes_operadora(df, id_operadora, trimestre_atual):
    """
    Busca os dados da operadora no trimestre atual, anterior e ano anterior.
    Retorna KPI atual, Variação % e VALORES ABSOLUTOS anteriores.
    """
    # Filtra apenas a operadora
    df_op = df[df['ID_OPERADORA'] == str(id_operadora)].set_index('ID_TRIMESTRE')
    
    if trimestre_atual not in df_op.index:
        return None

    # Dados Atuais
    atual = df_op.loc[trimestre_atual]
    
    # Identifica trimestres passados
    tri_prev_q, tri_prev_y = obter_trimestres_anteriores(trimestre_atual)
    
    # Busca dados passados (se existirem)
    dados_prev_q = df_op.loc[tri_prev_q] if tri_prev_q in df_op.index else None
    dados_prev_y = df_op.loc[tri_prev_y] if tri_prev_y in df_op.index else None

    kpis = {
        # --- VALORES ATUAIS ---
        'Vidas': atual['NR_BENEF_T'],
        'Receita': atual['VL_SALDO_FINAL'],
        'Ticket': atual['VL_SALDO_FINAL'] / atual['NR_BENEF_T'] if atual['NR_BENEF_T'] > 0 else 0,
        
        # --- VALORES ANTERIORES (NOVO) ---
        'Val_Vidas_QoQ': dados_prev_q['NR_BENEF_T'] if dados_prev_q is not None else 0,
        'Val_Receita_QoQ': dados_prev_q['VL_SALDO_FINAL'] if dados_prev_q is not None else 0,
        
        'Val_Vidas_YoY': dados_prev_y['NR_BENEF_T'] if dados_prev_y is not None else 0,
        'Val_Receita_YoY': dados_prev_y['VL_SALDO_FINAL'] if dados_prev_y is not None else 0,
        
        # --- VARIAÇÕES PERCENTUAIS ---
        'Var_Vidas_QoQ': 0.0,
        'Var_Receita_QoQ': 0.0,
        'Var_Vidas_YoY': 0.0,
        'Var_Receita_YoY': 0.0,
        
        # Referências de Data
        'Ref_QoQ': tri_prev_q,
        'Ref_YoY': tri_prev_y
    }

    # Cálculos QoQ %
    if dados_prev_q is not None:
        if dados_prev_q['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_QoQ'] = (atual['NR_BENEF_T'] - dados_prev_q['NR_BENEF_T']) / dados_prev_q['NR_BENEF_T']
        if dados_prev_q['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_QoQ'] = (atual['VL_SALDO_FINAL'] - dados_prev_q['VL_SALDO_FINAL']) / dados_prev_q['VL_SALDO_FINAL']

    # Cálculos YoY %
    if dados_prev_y is not None:
        if dados_prev_y['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_YoY'] = (atual['NR_BENEF_T'] - dados_prev_y['NR_BENEF_T']) / dados_prev_y['NR_BENEF_T']
        if dados_prev_y['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_YoY'] = (atual['VL_SALDO_FINAL'] - dados_prev_y['VL_SALDO_FINAL']) / dados_prev_y['VL_SALDO_FINAL']

    return kpis

def calcular_kpis_financeiros_avancados(df_mestre, id_operadora, trimestre_atual):
    """
    Calcula indicadores estratégicos avançados considerando a janela temporal até o trimestre selecionado.
    """
    # 1. Preparação dos Dados da Operadora
    df_op = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].copy()
    
    # --- CORREÇÃO PRINCIPAL: Janela Temporal Dinâmica ---
    # Filtra apenas dados ATÉ o trimestre selecionado (inclusive) para que o histórico
    # respeite a seleção do usuário ("Visão do Passado").
    # Como o formato é "YYYY-TX", a ordenação de string funciona cronologicamente.
    df_hist_window = df_op[df_op['ID_TRIMESTRE'] <= trimestre_atual].sort_values('ID_TRIMESTRE')
    
    # Pega a linha exata do trimestre selecionado (última da janela filtrada)
    if df_hist_window.empty or df_hist_window.iloc[-1]['ID_TRIMESTRE'] != trimestre_atual:
        return None
        
    row_atual = df_hist_window.iloc[[-1]] # Mantém formato DataFrame
    
    # Dados do Trimestre (Mercado Total) para cálculo de Share
    df_tri_mercado = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre_atual]
    
    # Valores Chave Atuais
    receita_op = row_atual['VL_SALDO_FINAL'].values[0]
    vidas_op = row_atual['NR_BENEF_T'].values[0]
    uf_op = row_atual['uf'].values[0]
    
    # 2. Market Share Financeiro (Nacional)
    total_receita_br = df_tri_mercado['VL_SALDO_FINAL'].sum()
    share_br = (receita_op / total_receita_br) * 100 if total_receita_br > 0 else 0
    
    # 3. Share UF (Concentração Geográfica)
    total_receita_uf = df_tri_mercado[df_tri_mercado['uf'] == uf_op]['VL_SALDO_FINAL'].sum()
    share_uf = (receita_op / total_receita_uf) * 100 if total_receita_uf > 0 else 0
    
    # 4. Variação do Ticket Médio (Pricing Power)
    # Buscamos a penúltima linha da janela filtrada (Trimestre Anterior relativo à seleção)
    ticket_atual = receita_op / vidas_op if vidas_op > 0 else 0
    
    if len(df_hist_window) >= 2:
        row_prev = df_hist_window.iloc[-2]
        rec_prev = row_prev['VL_SALDO_FINAL']
        vid_prev = row_prev['NR_BENEF_T']
        ticket_prev = rec_prev / vid_prev if vid_prev > 0 else 0
        var_ticket = (ticket_atual / ticket_prev) - 1 if ticket_prev > 0 else 0
    else:
        var_ticket = 0
        
    # 5. CAGR (Crescimento Anualizado - Janela de 1 ano terminando na seleção)
    # Pegamos os últimos 5 registros DA JANELA FILTRADA
    df_cagr_window = df_hist_window.tail(5)
    
    if len(df_cagr_window) >= 5:
        start_val = df_cagr_window.iloc[0]['VL_SALDO_FINAL'] # T-4 (Ano antes da seleção)
        end_val = df_cagr_window.iloc[-1]['VL_SALDO_FINAL']  # T (Seleção)
        cagr = (end_val / start_val) - 1 if start_val > 0 else 0
    else:
        cagr = 0 
        
    # 6. Volatilidade (Janela de 2 anos terminando na seleção)
    # Pegamos os últimos 8 registros DA JANELA FILTRADA
    df_vol_window = df_hist_window.tail(8)
    volatilidade = df_vol_window['VAR_PCT_RECEITA'].std() * 100 
    if pd.isna(volatilidade): volatilidade = 0

    return {
        'Share_Nacional': share_br,
        'Share_UF': share_uf,
        'UF': uf_op,
        'Var_Ticket': var_ticket,
        'CAGR_1Ano': cagr,
        'Volatilidade': volatilidade
    }

def calcular_kpis_vidas_avancados(df_mestre, id_operadora, trimestre_atual):
    """
    Calcula indicadores estratégicos para a tela de Vidas.
    """
    # 1. Preparação
    df_op = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].copy()
    
    # Janela Temporal (Visão do Passado)
    df_hist_window = df_op[df_op['ID_TRIMESTRE'] <= trimestre_atual].sort_values('ID_TRIMESTRE')
    
    if df_hist_window.empty or df_hist_window.iloc[-1]['ID_TRIMESTRE'] != trimestre_atual:
        return None
        
    row_atual = df_hist_window.iloc[[-1]]
    df_tri_mercado = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre_atual]
    
    # Valores
    vidas_op = row_atual['NR_BENEF_T'].values[0]
    uf_op = row_atual['uf'].values[0]
    
    # 2. Market Share Vidas (Nacional)
    total_vidas_br = df_tri_mercado['NR_BENEF_T'].sum()
    share_br = (vidas_op / total_vidas_br) * 100 if total_vidas_br > 0 else 0
    
    # 3. Share UF (Vidas)
    total_vidas_uf = df_tri_mercado[df_tri_mercado['uf'] == uf_op]['NR_BENEF_T'].sum()
    share_uf = (vidas_op / total_vidas_uf) * 100 if total_vidas_uf > 0 else 0
    
    # 4. CAGR Vidas (1 Ano)
    df_cagr_window = df_hist_window.tail(5)
    if len(df_cagr_window) >= 5:
        start_val = df_cagr_window.iloc[0]['NR_BENEF_T']
        end_val = df_cagr_window.iloc[-1]['NR_BENEF_T']
        cagr = (end_val / start_val) - 1 if start_val > 0 else 0
    else:
        cagr = 0 
        
    # 5. Volatilidade de Vidas (Estabilidade da carteira)
    df_vol_window = df_hist_window.tail(8)
    volatilidade = df_vol_window['VAR_PCT_VIDAS'].std() * 100 
    if pd.isna(volatilidade): volatilidade = 0

    return {
        'Share_Nacional': share_br,
        'Share_UF': share_uf,
        'UF': uf_op,
        'CAGR_1Ano': cagr,
        'Volatilidade': volatilidade
    }    
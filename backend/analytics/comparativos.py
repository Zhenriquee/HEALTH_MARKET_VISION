import pandas as pd

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
    Retorna um dicionário com os valores e as variações %.
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
        # Valores Atuais
        'Vidas': atual['NR_BENEF_T'],
        'Receita': atual['VL_SALDO_FINAL'],
        'Ticket': atual['VL_SALDO_FINAL'] / atual['NR_BENEF_T'] if atual['NR_BENEF_T'] > 0 else 0,
        
        # Variações QoQ (Trimestre Anterior)
        'Var_Vidas_QoQ': 0,
        'Var_Receita_QoQ': 0,
        
        # Variações YoY (Ano Anterior)
        'Var_Vidas_YoY': 0,
        'Var_Receita_YoY': 0
    }

    # Cálculos QoQ
    if dados_prev_q is not None:
        if dados_prev_q['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_QoQ'] = (atual['NR_BENEF_T'] - dados_prev_q['NR_BENEF_T']) / dados_prev_q['NR_BENEF_T']
        if dados_prev_q['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_QoQ'] = (atual['VL_SALDO_FINAL'] - dados_prev_q['VL_SALDO_FINAL']) / dados_prev_q['VL_SALDO_FINAL']

    # Cálculos YoY
    if dados_prev_y is not None:
        if dados_prev_y['NR_BENEF_T'] > 0:
            kpis['Var_Vidas_YoY'] = (atual['NR_BENEF_T'] - dados_prev_y['NR_BENEF_T']) / dados_prev_y['NR_BENEF_T']
        if dados_prev_y['VL_SALDO_FINAL'] > 0:
            kpis['Var_Receita_YoY'] = (atual['VL_SALDO_FINAL'] - dados_prev_y['VL_SALDO_FINAL']) / dados_prev_y['VL_SALDO_FINAL']

    return kpis
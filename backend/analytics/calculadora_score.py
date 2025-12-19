import pandas as pd

def calcular_power_score(df):
    """
    Recebe um DataFrame filtrado e adiciona a coluna 'Power_Score'.
    Lógica: 50% Vidas (Normalizado) + 50% Receita (Normalizado).
    Retorna o DF ordenado pelo Score.
    """
    df_calc = df.copy()
    
    if df_calc.empty:
        return df_calc

    # Encontra os máximos do contexto atual
    max_vidas = df_calc['NR_BENEF_T'].max()
    max_receita = df_calc['VL_SALDO_FINAL'].max()
    
    # Previne divisão por zero
    if max_vidas == 0 or pd.isna(max_vidas): max_vidas = 1
    if max_receita == 0 or pd.isna(max_receita): max_receita = 1

    # Cálculo dos vetores normalizados (0 a 1)
    score_vidas = df_calc['NR_BENEF_T'] / max_vidas
    score_receita = df_calc['VL_SALDO_FINAL'] / max_receita
    
    # Média Ponderada (0 a 100)
    df_calc['Power_Score'] = (0.5 * score_vidas + 0.5 * score_receita) * 100
    
    # Retorna ordenado e reseta o índice para virar o Rank
    return df_calc.sort_values(by='Power_Score', ascending=False).reset_index(drop=True)
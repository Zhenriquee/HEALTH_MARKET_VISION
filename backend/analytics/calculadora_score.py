import pandas as pd
import numpy as np

# Pesos da Regra de Negócio
PESO_VIDAS = 0.40       # 40% Tamanho de Carteira (Volume)
PESO_RECEITA = 0.40     # 40% Faturamento (Volume)
PESO_PERFORMANCE = 0.20 # 20% Crescimento (Vidas + Receita)

def calcular_power_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula Power Score (0-100) ponderado.
    Performance agora considera crescimento de VIDAS e RECEITA.
    """
    if df.empty: return df.copy()

    df_calc = df.copy()
    
    # 1. Normalização de Volume (0 a 1)
    max_vidas = df_calc['NR_BENEF_T'].max() or 1
    max_receita = df_calc['VL_SALDO_FINAL'].max() or 1

    score_vidas = df_calc['NR_BENEF_T'] / max_vidas
    score_receita = df_calc['VL_SALDO_FINAL'] / max_receita
    
    # 2. Normalização de Performance (Crescimento)
    # Clipamos entre -10% e +10% para evitar distorções extremas
    clip_min, clip_max = -0.10, 0.10
    
    # A. Performance Vidas
    perf_vidas = df_calc['VAR_PCT_VIDAS'].clip(lower=clip_min, upper=clip_max)
    # Transforma escala [-0.10, 0.10] em [0, 1]
    score_perf_vidas = (perf_vidas - clip_min) / (clip_max - clip_min)
    
    # B. Performance Receita (NOVO)
    perf_receita = df_calc['VAR_PCT_RECEITA'].clip(lower=clip_min, upper=clip_max)
    score_perf_receita = (perf_receita - clip_min) / (clip_max - clip_min)
    
    # C. Performance Combinada (Média Simples)
    score_performance_total = (score_perf_vidas + score_perf_receita) / 2

    # 3. Cálculo Final
    df_calc['Power_Score'] = (
        (PESO_VIDAS * score_vidas) + 
        (PESO_RECEITA * score_receita) + 
        (PESO_PERFORMANCE * score_performance_total)
    ) * 100
    
    return df_calc.sort_values(by='Power_Score', ascending=False).reset_index(drop=True)

def calcular_score_financeiro(df_input):
    """
    Calcula um Score focado apenas em Receita (0-100).
    Peso: 70% Volume de Receita + 30% Crescimento de Receita.
    """
    df = df_input.copy()
    
    # Normalização Logarítmica para Receita (para não distorcer com gigantes)
    log_receita = np.log1p(df['VL_SALDO_FINAL'])
    min_rec = log_receita.min()
    max_rec = log_receita.max()
    score_vol = ((log_receita - min_rec) / (max_rec - min_rec)).fillna(0) * 100
    
    # Normalização de Crescimento Financeiro
    # Clipamos entre -50% e +50% para evitar distorções de outliers
    growth = df['VAR_PCT_RECEITA'].clip(-0.5, 0.5)
    min_g = growth.min()
    max_g = growth.max()
    
    if max_g > min_g:
        score_growth = ((growth - min_g) / (max_g - min_g)).fillna(0) * 100
    else:
        score_growth = 50
        
    # Cálculo Final (70% Volume, 30% Performance)
    df['Revenue_Score'] = (score_vol * 0.7) + (score_growth * 0.3)
    
    return df.sort_values('Revenue_Score', ascending=False)    
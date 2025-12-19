import pandas as pd

def extrair_marca(razao_social):
    """
    Normaliza a Marca/Grupo Econômico.
    Agrupa variações como 'UNIMED-RIO', 'UNIMED DO BRASIL' sob 'UNIMED'.
    """
    if pd.isna(razao_social): return "OUTROS"
    
    nome = razao_social.strip().upper()
    
    # Regras de Agrupamento de Grandes Redes
    if nome.startswith("UNIMED"): return "UNIMED"
    if nome.startswith("BRADESCO"): return "BRADESCO"
    if nome.startswith("AMIL"): return "AMIL"
    if nome.startswith("SUL AMERICA") or nome.startswith("SULAMERICA"): return "SULAMERICA"
    if nome.startswith("HAPVIDA"): return "HAPVIDA"
    if nome.startswith("NOTRE DAME") or nome.startswith("NOTREDAME") or nome.startswith("GNDI"): return "NOTREDAME"
    if nome.startswith("GOLDEN CROSS"): return "GOLDEN CROSS"
    if nome.startswith("PORTO SEGURO"): return "PORTO SEGURO"
    
    # Regra Geral: Pega a primeira palavra (tratando hífens)
    primeira_palavra = nome.split()[0].replace("-", "")
    return primeira_palavra

def analisar_performance_marca(df_trimestre, operadora_row):
    """
    Retorna estatísticas comparativas do grupo.
    """
    marca = extrair_marca(operadora_row['razao_social'])
    
    # Cria cópia para não alterar o original
    df_calc = df_trimestre.copy()
    df_calc['Marca_Temp'] = df_calc['razao_social'].apply(extrair_marca)
    
    # Filtra o grupo
    df_grupo = df_calc[df_calc['Marca_Temp'] == marca].copy()
    
    total_vidas_grupo = df_grupo['NR_BENEF_T'].sum()
    
    # Share of Brand
    vidas_op = operadora_row['NR_BENEF_T']
    share_of_brand = (vidas_op / total_vidas_grupo) * 100 if total_vidas_grupo > 0 else 0
    
    return {
        'Marca': marca,
        'Qtd_Grupo': len(df_grupo),
        'Share_of_Brand': share_of_brand,
        'Media_Cresc_Vidas_Grupo': df_grupo['VAR_PCT_VIDAS'].median(),
        'Media_Cresc_Receita_Grupo': df_grupo['VAR_PCT_RECEITA'].median(),
        'Df_Grupo': df_grupo # Retorna o DF para listagem
    }
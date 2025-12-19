import pandas as pd

def filtrar_por_modalidade(df, modalidades_selecionadas):
    """
    Filtra o DataFrame mantendo apenas as modalidades informadas.
    Se a lista estiver vazia, retorna o DataFrame original.
    """
    if not modalidades_selecionadas:
        return df.copy()
    
    return df[df['modalidade'].isin(modalidades_selecionadas)].copy()
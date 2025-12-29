import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

def calcular_correlacoes(df_mestre):
    """
    Calcula a matriz de correlação entre as principais métricas numéricas.
    """

    cols = ['NR_BENEF_T', 'VL_SALDO_FINAL', 'VAR_PCT_VIDAS', 'VAR_PCT_RECEITA']
    
    df_corr = df_mestre[cols].copy()
    df_corr['TICKET_MEDIO'] = df_corr['VL_SALDO_FINAL'] / df_corr['NR_BENEF_T']
    
    df_corr.columns = ['Vidas', 'Receita', 'Cresc. Vidas', 'Cresc. Receita', 'Ticket Médio']
    
    # Calcula correlação de Pearson
    return df_corr.corr()

def preparar_dados_segmentacao(df_mestre, trimestre):
    """
    Prepara os dados para o gráfico de quadrantes (Scatter Plot).
    Eixos: Crescimento (Y) vs Market Share (X).
    """
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre].copy()
    
    # Calcula Market Share
    total_receita = df_tri['VL_SALDO_FINAL'].sum()
    df_tri['Market_Share'] = (df_tri['VL_SALDO_FINAL'] / total_receita) * 100
    
    df_clean = df_tri[
        (df_tri['VAR_PCT_RECEITA'] > -0.5) & 
        (df_tri['VAR_PCT_RECEITA'] < 1.0)
    ].copy()
    
    return df_clean

def calcular_outliers_ticket(df_mestre, trimestre):
    """
    Prepara dados para análise de distribuição de Ticket Médio por Modalidade.
    """
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre].copy()
    df_tri['Ticket_Medio'] = df_tri['VL_SALDO_FINAL'] / df_tri['NR_BENEF_T']
    
    # Remove infinitos e nulos
    df_tri = df_tri.replace([np.inf, -np.inf], np.nan).dropna(subset=['Ticket_Medio'])
    
    return df_tri

def _preparar_dados_clustering(df_mestre, trimestre):
    """
    Prepara os dados: Log em Vidas/Receita, cria Ticket Médio e remove NaNs.
    """
    df_tri = df_mestre[df_mestre['ID_TRIMESTRE'] == trimestre].copy()
    
    # Features Logarítmicas (para reduzir escala de gigantes)
    df_tri['Log_Vidas'] = np.log1p(df_tri['NR_BENEF_T'].clip(lower=0))
    df_tri['Log_Receita'] = np.log1p(df_tri['VL_SALDO_FINAL'].clip(lower=0))
    
    if 'Ticket_Medio' not in df_tri.columns:
        df_tri['Ticket_Medio'] = df_tri['VL_SALDO_FINAL'] / df_tri['NR_BENEF_T']
    
    features = ['Log_Vidas', 'Log_Receita', 'VAR_PCT_VIDAS', 'VAR_PCT_RECEITA', 'Ticket_Medio']
    
    df_model = df_tri.dropna(subset=features).replace([np.inf, -np.inf], 0).copy()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_model[features])
    
    return df_model, X_scaled

def calcular_elbow_method(df_mestre, trimestre, max_k=10):
    """Calcula inércia para gráfico do cotovelo."""
    _, X_scaled = _preparar_dados_clustering(df_mestre, trimestre)
    inertias = []
    k_values = range(1, max_k + 1)
    
    for k in k_values:
        model = KMeans(n_clusters=k, random_state=42, n_init='auto')
        model.fit(X_scaled)
        inertias.append(model.inertia_)
        
    return pd.DataFrame({'K': k_values, 'Inertia': inertias})

def aplicar_kmeans_pca(df_mestre, trimestre, n_clusters=4, n_components=2):
    """
    Aplica K-Means e PCA e retorna os DADOS AGRUPADOS (Centroides) com coordenadas.
    """
    df_model, X_scaled = _preparar_dados_clustering(df_mestre, trimestre)
    
    # 1. K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    cluster_labels = kmeans.fit_predict(X_scaled)
    df_model['Cluster_ID'] = cluster_labels.astype(str)
    
    # 2. PCA
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X_scaled)
    
    df_model['PC1'] = components[:, 0]
    df_model['PC2'] = components[:, 1]
    
    cols_coords = ['PC1', 'PC2']
    
    if n_components >= 3:
        df_model['PC3'] = components[:, 2]
        cols_coords.append('PC3')
        explained_var = pca.explained_variance_ratio_
    else:
        explained_var = pca.explained_variance_ratio_
    
    cols_stats = ['NR_BENEF_T', 'VL_SALDO_FINAL', 'VAR_PCT_VIDAS', 'VAR_PCT_RECEITA', 'Ticket_Medio']
    
    df_centroids = df_model.groupby('Cluster_ID')[cols_stats + cols_coords].mean().reset_index()
    df_centroids['Qtd_Operadoras'] = df_model.groupby('Cluster_ID')['ID_OPERADORA'].count().values
    
    return df_model, df_centroids, explained_var
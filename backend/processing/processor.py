import pandas as pd
import numpy as np

class DataProcessor:
    """
    Responsável pela transformação pura dos dados (Pandas).
    Camada Silver (Limpeza) e Gold (Regras de Negócio/KPIs).
    """

    @staticmethod
    def normalizar_chaves(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
        """Padroniza chaves (ex: Registro ANS) para 6 dígitos string."""
        if df.empty:
            return df
            
        def _normalizar(valor):
            return str(valor).split('.')[0].strip().zfill(6)

        for col in colunas:
            if col in df.columns:
                df[col] = df[col].apply(_normalizar)
        return df

    @staticmethod
    def aplicar_filtro_temporal(df: pd.DataFrame, coluna_tempo: str, data_corte: str) -> pd.DataFrame:
        if df.empty or coluna_tempo not in df.columns:
            return df
        return df[df[coluna_tempo] >= data_corte]

    @staticmethod
    def enriquecer_dataset(df_mestre: pd.DataFrame, df_dimensao: pd.DataFrame) -> pd.DataFrame:
        """Realiza os Joins para criar a Tabela OBT (One Big Table)."""
        # Join de Enriquecimento
        df_final = pd.merge(
            df_mestre,
            df_dimensao,
            left_on='ID_OPERADORA',
            right_on='registro_operadora',
            how='left'
        )
        return df_final

    @staticmethod
    def calcular_kpis(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula métricas derivadas (Gold Layer)."""
        if df.empty:
            return df
            
        # Ordenação necessária para cálculos de variação (pct_change)
        df = df.sort_values(['ID_OPERADORA', 'ID_TRIMESTRE'])
        
        # Variações
        df['VAR_PCT_VIDAS'] = df.groupby('ID_OPERADORA')['NR_BENEF_T'].pct_change().fillna(0)
        df['VAR_PCT_RECEITA'] = df.groupby('ID_OPERADORA')['VL_SALDO_FINAL'].pct_change().fillna(0)

        # KPIs Compostos
        df['CUSTO_POR_VIDA'] = np.where(
            df['NR_BENEF_T'] > 0, 
            df['VL_SALDO_FINAL'] / df['NR_BENEF_T'], 
            0
        )
        return df
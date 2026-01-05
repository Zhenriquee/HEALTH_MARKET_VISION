import pandas as pd
from infra.db_connector import ConexaoSQLite
from backend.repository import AnsRepository
from backend.config import settings
from backend.processing.processor import DataProcessor

class DataEngine:
    def __init__(self):
        # 1. Infraestrutura (Conexão) - Agora usa settings.DB_PATH
        # Idealmente, injetaríamos isso no __init__, mas manteremos assim por enquanto
        self.connector = ConexaoSQLite(str(settings.DB_PATH))
        
        # 2. Repositório (Acesso a Dados)
        self.repository = AnsRepository(self.connector, str(settings.QUERIES_DIR))
        
        # 3. Processador (Lógica de Transformação)
        self.processor = DataProcessor()

    def _extrair_dados(self):
        """Etapa de Extração (Bronze Layer)"""
        print("Extraindo dados brutos...")
        return (
            self.repository.buscar_dados_brutos("etl/load_dim_operadoras.sql"),
            self.repository.buscar_dados_brutos("etl/load_beneficiarios.sql"),
            self.repository.buscar_dados_brutos("etl/load_financeiro.sql")
        )

    def gerar_dataset_mestre(self):
        """
        Pipeline ETL Principal:
        1. Extração (SQL)
        2. Transformação Silver (Normalização/Limpeza)
        3. Transformação Gold (Enriquecimento/KPIs)
        """
        # 1. Extração
        df_dim, df_ben, df_fin = self._extrair_dados()
        
        if df_dim.empty: return pd.DataFrame()

        # 2. Transformação Silver (Normalização)
        df_dim = self.processor.normalizar_chaves(df_dim, ['registro_operadora'])
        df_ben = self.processor.normalizar_chaves(df_ben, ['CD_OPERADO'])
        df_fin = self.processor.normalizar_chaves(df_fin, ['REG_ANS'])

        # 2.1 Filtros Temporais
        df_ben = self.processor.aplicar_filtro_temporal(df_ben, 'ID_TRIMESTRE', settings.DATA_CORTE_INICIO)
        df_fin = self.processor.aplicar_filtro_temporal(df_fin, 'ID_TRIMESTRE', settings.DATA_CORTE_INICIO)

        # 3. Transformação Gold (Consolidação)
        # Join Full entre Fatos (Beneficiários + Financeiro)
        df_mestre = pd.merge(
            df_ben, df_fin,
            left_on=['CD_OPERADO', 'ID_TRIMESTRE'],
            right_on=['REG_ANS', 'ID_TRIMESTRE'],
            how='outer'
        )

        # Tratamento de Nulos pós-join
        df_mestre['ID_OPERADORA'] = df_mestre['CD_OPERADO'].fillna(df_mestre['REG_ANS'])
        df_mestre['NR_BENEF_T'] = df_mestre['NR_BENEF_T'].fillna(0)
        df_mestre['VL_SALDO_FINAL'] = df_mestre['VL_SALDO_FINAL'].fillna(0)

        # Enriquecimento com Dimensão (Left Join)
        df_final = self.processor.enriquecer_dataset(df_mestre, df_dim)

        # 4. Cálculo de KPIs
        df_final = self.processor.calcular_kpis(df_final)

        # Seleção Final de Colunas (Cleanup)
        cols_desejadas = [
            'ID_TRIMESTRE', 'ID_OPERADORA', 'razao_social', 'cnpj', 'uf', 'modalidade',
            'cidade', 'representante', 'cargo_representante', 'Data_Registro_ANS',
            'descredenciada_em', 'descredenciamento_motivo',
            'NR_BENEF_T', 'VL_SALDO_FINAL', 
            'VAR_PCT_VIDAS', 'VAR_PCT_RECEITA', 'CUSTO_POR_VIDA'
        ]
        cols_existentes = [c for c in cols_desejadas if c in df_final.columns]
        
        return df_final[cols_existentes]
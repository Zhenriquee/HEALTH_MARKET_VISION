import os
import pandas as pd
import numpy as np
from infra.db_connector import ConexaoSQLite
from backend.repository import AnsRepository

class DataEngine:
    def __init__(self):
        # Inicializa o conector
        self.connector = ConexaoSQLite()
        
        # Configura o caminho absoluto para a pasta de queries
        # Assume que a estrutura é: projeto/queries/
        base_dir = os.getcwd()
        queries_path = os.path.join(base_dir, 'queries')
        
        # Inicializa o Repositório injetando o conector e o caminho
        self.repository = AnsRepository(self.connector, queries_path)

    def _carregar_tabelas_brutas(self):
        """
        Lê as tabelas do banco utilizando o Repository Pattern.
        O SQL agora reside em arquivos externos .sql na pasta queries/etl/
        """
        print("Carregando tabelas para memória via Repository...")
        
        # 1. Dimensão Operadoras
        df_dim = self.repository.buscar_dados_brutos(
            nome_query="etl/load_dim_operadoras.sql"
        )

        # 2. Beneficiários
        df_ben = self.repository.buscar_dados_brutos(
            nome_query="etl/load_beneficiarios.sql"
        )

        # 3. Financeiro
        df_fin = self.repository.buscar_dados_brutos(
            nome_query="etl/load_financeiro.sql"
        )

        return df_dim, df_ben, df_fin

    def gerar_dataset_mestre(self):
        """
        Gera o dataset único, aplicando filtro temporal >= 2012-T1
        Mantém a lógica de transformação Python, mas a extração foi delegada.
        """
        df_dim, df_ben, df_fin = self._carregar_tabelas_brutas()

        if df_dim.empty: 
            return pd.DataFrame()

        # --- PREPARAÇÃO DE TIPOS E NORMALIZAÇÃO ---
        def normalizar_ans(valor):
            return str(valor).split('.')[0].strip().zfill(6)

        # Aplicação segura da normalização
        if not df_dim.empty:
            df_dim['registro_operadora'] = df_dim['registro_operadora'].apply(normalizar_ans)
            
        if not df_ben.empty:
            df_ben['CD_OPERADO'] = df_ben['CD_OPERADO'].apply(normalizar_ans)
            
        if not df_fin.empty:
            df_fin['REG_ANS'] = df_fin['REG_ANS'].apply(normalizar_ans)

        # --- FILTRO TEMPORAL (>= 2012-T1) ---
        DATA_CORTE = '2012-T1'
        
        if not df_ben.empty:
            df_ben = df_ben[df_ben['ID_TRIMESTRE'] >= DATA_CORTE]
            
        if not df_fin.empty:
            df_fin = df_fin[df_fin['ID_TRIMESTRE'] >= DATA_CORTE]

        # --- JOIN 1: Beneficiários + Financeiro (FULL OUTER JOIN) ---
        df_mestre = pd.merge(
            df_ben,
            df_fin,
            left_on=['CD_OPERADO', 'ID_TRIMESTRE'],
            right_on=['REG_ANS', 'ID_TRIMESTRE'],
            how='outer'
        )

        # Unificar coluna de Operadora
        df_mestre['ID_OPERADORA'] = df_mestre['CD_OPERADO'].fillna(df_mestre['REG_ANS'])
        
        # Preencher vazios numéricos com 0
        df_mestre['NR_BENEF_T'] = df_mestre['NR_BENEF_T'].fillna(0)
        df_mestre['VL_SALDO_FINAL'] = df_mestre['VL_SALDO_FINAL'].fillna(0)

        # --- JOIN 2: Adicionar Dados Cadastrais (LEFT JOIN) ---
        df_final = pd.merge(
            df_mestre,
            df_dim,
            left_on='ID_OPERADORA',
            right_on='registro_operadora',
            how='left'
        )

        # Seleção de colunas finais
        cols_desejadas = [
            'ID_TRIMESTRE', 'ID_OPERADORA', 'razao_social', 'cnpj', 'uf', 'modalidade',
            'cidade', 'representante', 'cargo_representante', 'Data_Registro_ANS',
            'descredenciada_em', 'descredenciamento_motivo',
            'NR_BENEF_T', 'VL_SALDO_FINAL'
        ]
        
        # Filtra apenas as colunas que realmente existem após os joins
        cols_existentes = [c for c in cols_desejadas if c in df_final.columns]
        df_final = df_final[cols_existentes]

        # Ordenação Obrigatória
        if not df_final.empty:
            df_final = df_final.sort_values(['ID_OPERADORA', 'ID_TRIMESTRE'])

        # --- CÁLCULOS DE BUSINESS INTELLIGENCE ---
        # Garante que não hajam divisões por zero ou NaNs indesejados
        if not df_final.empty:
            df_final['VAR_PCT_VIDAS'] = df_final.groupby('ID_OPERADORA')['NR_BENEF_T'].pct_change().fillna(0)
            df_final['VAR_PCT_RECEITA'] = df_final.groupby('ID_OPERADORA')['VL_SALDO_FINAL'].pct_change().fillna(0)

            df_final['CUSTO_POR_VIDA'] = np.where(
                df_final['NR_BENEF_T'] > 0, 
                df_final['VL_SALDO_FINAL'] / df_final['NR_BENEF_T'], 
                0
            )

        return df_final
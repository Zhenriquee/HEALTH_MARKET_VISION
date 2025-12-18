import pandas as pd
from infra.db_connector import ConexaoSQLite

class DataEngine:
    def __init__(self):
        self.connector = ConexaoSQLite()

    def _carregar_tabelas_brutas(self):
        """Lê as tabelas do banco sem processamento pesado"""
        print("Carregando tabelas para memória...")
        
        # 1. Dimensão Operadoras
        sql_dim = """
            SELECT registro_operadora, cnpj, razao_social, uf, cidade, modalidade, representante, cargo_representante 
            FROM dim_operadoras
        """
        df_dim = self.connector.executar_query(sql_dim)

        # 2. Beneficiários
        sql_ben = "SELECT CD_OPERADO, ID_TRIMESTRE, NR_BENEF_T FROM beneficiarios_agrupados"
        df_ben = self.connector.executar_query(sql_ben)

        # 3. Financeiro
        sql_fin = "SELECT REG_ANS, ID_TRIMESTRE, VL_SALDO_FINAL FROM demonstracoes_contabeis"
        df_fin = self.connector.executar_query(sql_fin)

        return df_dim, df_ben, df_fin

    def gerar_dataset_mestre(self):
        """
        Gera o dataset único, aplicando filtro temporal >= 2012-T1
        """
        df_dim, df_ben, df_fin = self._carregar_tabelas_brutas()

        if df_dim.empty: return pd.DataFrame()

        # --- PREPARAÇÃO DE TIPOS ---
        df_dim['registro_operadora'] = df_dim['registro_operadora'].astype(str).str.strip()
        df_ben['CD_OPERADO'] = df_ben['CD_OPERADO'].astype(str).str.strip()
        df_fin['REG_ANS'] = df_fin['REG_ANS'].astype(str).str.strip()

        # --- NOVA ETAPA: FILTRO TEMPORAL (>= 2012-T1) ---
        # Aplicamos antes do Merge para o processo ser mais leve e rápido
        DATA_CORTE = '2012-T1'
        
        print(f"Aplicando filtro temporal: >= {DATA_CORTE}")
        
        # Como o formato é 'AAAA-TX', a comparação de string funciona perfeitamente
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
        
        # Preencher vazios
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
        cols_para_manter = [
            'ID_TRIMESTRE', 'ID_OPERADORA', 'razao_social', 'cnpj', 'uf', 'modalidade',
            'NR_BENEF_T', 'VL_SALDO_FINAL'
        ]
        
        cols_finais = [c for c in cols_para_manter if c in df_final.columns]
        df_final = df_final[cols_finais]

        # --- KPI CALCULADO ---
        df_final['CUSTO_POR_VIDA'] = df_final.apply(
            lambda row: row['VL_SALDO_FINAL'] / row['NR_BENEF_T'] if row['NR_BENEF_T'] > 0 else 0, 
            axis=1
        )

        # Ordenação final para garantir gráficos bonitos
        df_final = df_final.sort_values(['ID_OPERADORA', 'ID_TRIMESTRE'])

        print(f"Dataset Mestre Gerado (Pós-2012): {len(df_final)} linhas.")
        return df_final
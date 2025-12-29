import pandas as pd 
from pathlib import Path
from backend.repository import AnsRepository

class FilterService:
    def __init__(self, repository:AnsRepository):
        self.repo = repository

    def get_todas_operadoras(self):
        """ esse metodo tem como objetivo retornar todas as operadoras disponiveis na base de dados
        as colunas são: registro operadora, cnpj, razao social e nome fantasia
        """
        base_dir = Path(__file__).resolve().parents[2]

        sql_path = base_dir / 'queries' / 'filtros' / 'listar_todas_operadoras.sql'

        df = self.repo.buscar_dados_brutos(sql_path)
        if df.empty:
            return pd.DataFrame()
        if 'nome_fantasia' in df.columns:
            df['nome_fantasia'] = df['nome_fantasia'].fillna(df['razao_social'])
        return df
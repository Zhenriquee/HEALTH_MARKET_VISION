from pathlib import Path

# Define a raiz do projeto (navega 2 níveis acima de backend/config.py)
ROOT_DIR = Path(__file__).parent.parent.resolve()

class Settings:
    # Caminhos de Dados
    DATA_DIR = ROOT_DIR / "data"
    DB_PATH = DATA_DIR / "base_ans_paralela.db"
    
    # Caminhos de Queries
    QUERIES_DIR = ROOT_DIR / "queries"
    ETL_QUERIES = QUERIES_DIR / "etl"
    FILTER_QUERIES = QUERIES_DIR / "filtros"

    # Configurações de Negócio
    DATA_CORTE_INICIO = '2012-T1'

# Instância Singleton
settings = Settings()
import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FOLDER = os.path.join(BASE_DIR, 'data')
DB_NAME = 'dados_ans_paralela.db'
base_dire = Path(__file__).resolve().parents[2]

DATABASE_PATH = base_dire / 'queries' / 'filtros' / 'listar_todas_operadoras.sql' #'/workspaces/ANALISE_OPERADORAS/data/base_ans_paralela.db'#os.path.join(DB_FOLDER, DB_NAME)

QUERIES_PATH = os.path.join(BASE_DIR, 'queries')

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
import sqlite3
import pandas as pd
import os
import logging
from backend.infra.contract import IDatabaseConnector
from configuracoes import DATABASE_PATH

# Configuração básica de log para observabilidade
logger = logging.getLogger(__name__)

class SQLiteConnector(IDatabaseConnector):
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._validar_caminho()
        self._conn = None

    def _validar_caminho(self):
        if not os.path.exists(self.db_path):
            error_msg = f"CRITICAL: Banco de dados não encontrado em {self.db_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

    def conectar(self):
        if not self._conn:
            try:
                self._conn = sqlite3.connect(self.db_path)
            except sqlite3.Error as e:
                logger.error(f"Erro ao conectar ao SQLite: {e}")
                raise

    def desconectar(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def executar_query(self, query: str, parametros: dict = None) -> pd.DataFrame:
        try:
            self.conectar()
            return pd.read_sql_query(query, self._conn, params=parametros)
        except Exception as e:
            logger.error(f"Falha na execução da query: {e} | Query: {query[:50]}...")
            # Em produção, dependendo da criticidade, poderíamos levantar o erro ou retornar vazio.
            # Para manter compatibilidade com seu código atual, retornamos vazio, mas logamos.
            return pd.DataFrame()
        finally:
            self.desconectar()
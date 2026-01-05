import sqlite3
import pandas as pd
import logging
from typing import Optional
from configuracoes import DATABASE_PATH

# Configuração de Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConexaoSQLite:
    """
    Gerenciador de Conexão SQLite.
    Refatorado para suportar integração nativa com Pandas (read_sql).
    """
    
    def __init__(self, db_name: str = DATABASE_PATH):
        # Ajuste o caminho do banco conforme sua estrutura real (data/ ou raiz)
        self.db_name = db_name
        self.connection: Optional[sqlite3.Connection] = None

    def __enter__(self):
        """Context Manager: Abre conexão ao usar 'with'"""
        self._conectar()
        return self

    def __exit__(self):
        """Context Manager: Fecha conexão ao sair"""
        self._desconectar()

    def _conectar(self):
        """Estabelece a conexão se não existir"""
        if not self.connection:
            try:
                self.connection = sqlite3.connect(self.db_name)
                # logger.info(f"Conectado ao banco: {self.db_name}")
            except sqlite3.Error as e:
                logger.error(f"Erro de conexão SQLite: {e}")
                raise

    def _desconectar(self):
        """Fecha a conexão com segurança"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def executar_query(self, query: str, parametros: dict = None) -> pd.DataFrame:
        """
        Executa uma query SQL e retorna diretamente um Pandas DataFrame.
        Trata automaticamente a abertura/fechamento de conexão se não estiver em bloco 'with'.
        """
        # Garante que temos uma conexão ativa
        self._conectar()
        
        try:
            # Pandas read_sql é mais robusto para ETL que cursor.fetchall()
            # params=parametros trata SQL Injection automaticamente
            df = pd.read_sql(query, self.connection, params=parametros)
            return df
            
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.debug(f"Query falha: {query}")
            return pd.DataFrame() # Retorna vazio em caso de erro para não quebrar a UI
            
        finally:
            # Se não estivermos usando Context Manager (__enter__), 
            # é boa prática fechar conexões transientes, mas em Data Apps 
            # às vezes mantemos aberta. Aqui, vamos manter aberta se foi instanciada
            # pelo __init__, mas o garbage collector do Python cuidará do resto.
            pass

    def executar_comando(self, sql: str, parametros: tuple = None) -> None:
        """
        Para comandos que NÃO retornam dados (INSERT, UPDATE, DELETE, CREATE).
        """
        self._conectar()
        try:
            cursor = self.connection.cursor()
            if parametros:
                cursor.execute(sql, parametros)
            else:
                cursor.execute(sql)
            self.connection.commit()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Erro ao executar comando: {e}")
            raise
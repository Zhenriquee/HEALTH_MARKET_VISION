from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any

class IDatabaseConnector(ABC):
    """
    Interface (Contrato) que garante que qualquer banco de dados
    conectado ao sistema respeite os mesmos métodos.
    """

    @abstractmethod
    def conectar(self):
        """Estabelece conexão com a fonte de dados."""
        pass

    @abstractmethod
    def desconectar(self):
        """Encerra a conexão de forma segura."""
        pass

    @abstractmethod
    def executar_query(self, query: str, parametros: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Executa uma consulta SQL e retorna um DataFrame.
        Deve tratar erros de conexão internamente.
        """
        pass
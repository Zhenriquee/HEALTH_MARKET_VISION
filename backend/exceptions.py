class AppError(Exception):
    """Classe base para exceções da aplicação."""
    pass

class DataLoadError(AppError):
    """Erro ao carregar dados brutos."""
    pass

class ProcessingError(AppError):
    """Erro durante o processamento ou cálculos."""
    pass

class FilterError(AppError):
    """Erro ao aplicar filtros (dados vazios após filtro)."""
    pass
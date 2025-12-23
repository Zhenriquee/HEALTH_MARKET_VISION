import pandas as pd
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.filtros_mercado import filtrar_por_modalidade
from backend.analytics.calculadora_score import calcular_power_score
from backend.analytics.brand_intelligence import extrair_marca

class MarketOverviewUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def execute(self, trimestre: str, modalidades: list):
        """
        Executa a lógica de preparação de dados para o Panorama de Mercado.
        """
        try:
            # 1. Filtragem por Modalidade
            df_mercado_filtrado = filtrar_por_modalidade(self.df_mestre, modalidades)
            
            if df_mercado_filtrado.empty:
                raise FilterError(f"Nenhum dado encontrado para as modalidades: {modalidades}")

            # 2. Filtragem por Trimestre (Snapshot)
            df_snapshot = df_mercado_filtrado[df_mercado_filtrado['ID_TRIMESTRE'] == trimestre].copy()
            
            if df_snapshot.empty:
                raise FilterError(f"Nenhum dado encontrado para o trimestre {trimestre} com os filtros atuais.")

            # 3. Tratamento de Marca (Necessário para gráficos e agrupamentos)
            # Verifica se a coluna já existe para evitar reprocessamento desnecessário
            if 'Marca_Temp' not in self.df_mestre.columns:
                self.df_mestre['Marca_Temp'] = self.df_mestre['razao_social'].apply(extrair_marca)

            # 4. Cálculo de Score e Ranking
            try:
                df_ranqueado = calcular_power_score(df_snapshot)
                df_ranqueado['Rank_Geral'] = df_ranqueado['Power_Score'].rank(ascending=False, method='min')
                df_ranqueado['#'] = range(1, len(df_ranqueado) + 1) # Rank visual sequencial
            except Exception as e:
                raise ProcessingError(f"Erro ao calcular Power Score: {str(e)}")

            # 5. Identificação do Líder (Top 1)
            if df_ranqueado.empty:
                raise ProcessingError("O cálculo de ranking retornou uma tabela vazia.")
            
            top_1 = df_ranqueado.iloc[0]
            id_top_1 = str(top_1['ID_OPERADORA'])

            # 6. Preparação dos KPIs do Líder (Objeto DTO simples)
            kpis_lider = {
                'Vidas': top_1['NR_BENEF_T'],
                'Receita': top_1['VL_SALDO_FINAL'],
                'Ticket': top_1['VL_SALDO_FINAL'] / top_1['NR_BENEF_T'] if top_1['NR_BENEF_T'] > 0 else 0,
                'Var_Vidas_QoQ': top_1['VAR_PCT_VIDAS'],
                'Var_Receita_QoQ': top_1['VAR_PCT_RECEITA'],
                'Sede': f"{str(top_1.get('cidade','')).title()}/{str(top_1.get('uf',''))}"
            }

            # 7. Retorno Estruturado (DTO)
            return {
                "lider": {
                    "dados": top_1,
                    "kpis": kpis_lider,
                    "id": id_top_1
                },
                "ranking_top_30": df_ranqueado.head(30),
                "contexto_filtro": f"Filtro: {', '.join(modalidades)}" if modalidades else "Mercado Total",
                "df_mestre_atualizado": self.df_mestre # Retorna df_mestre caso tenha sido modificado (coluna Marca)
            }

        except (FilterError, ProcessingError) as e:
            # Repassa erros conhecidos
            raise e
        except Exception as e:
            # Captura erros genéricos não previstos
            raise ProcessingError(f"Erro inesperado ao processar Panorama: {str(e)}")
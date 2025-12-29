import pandas as pd
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_power_score

class OperatorAnalysisUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def _gerar_storytelling(self, nome_op, trimestre, kpis, df_trimestre, marca_grupo):
        """
        Método interno para gerar a narrativa de texto.
        """
        var_rec_op = kpis.get('Var_Receita_QoQ', 0) * 100
        var_vid_op = kpis.get('Var_Vidas_QoQ', 0) * 100
        
        # Garante que as colunas percentuais existem (para evitar KeyError se o backend mudar)
        col_rec = 'VAR_PCT_RECEITA'
        col_vid = 'VAR_PCT_VIDAS'
        
        if col_rec not in df_trimestre.columns or col_vid not in df_trimestre.columns:
            return "Dados insuficientes para gerar resumo narrativo."

        mediana_mkt_rec = df_trimestre[col_rec].median() * 100
        mediana_mkt_vid = df_trimestre[col_vid].median() * 100

        # Filtra grupo com segurança (a coluna Marca_Temp deve existir aqui)
        df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
        mediana_grp_rec = df_grupo[col_rec].median() * 100 if not df_grupo.empty else 0

        spread_mkt = var_rec_op - mediana_mkt_rec
        spread_grp = var_rec_op - mediana_grp_rec

        texto = f"##### 📝 Resumo Executivo: {trimestre}\n\n"
        texto += f"No **{trimestre}**, a operadora **{nome_op}** registrou uma variação de receita de **{var_rec_op:+.2f}%**. "

        if spread_mkt > 0:
            texto += f"Performance sólida, superando a média do mercado em **+{spread_mkt:.2f} p.p.** "
        elif spread_mkt < 0:
            texto += f"Desempenho financeiro ficou **{spread_mkt:.2f} p.p.** abaixo da média do mercado. "
        else:
            texto += "Desempenho alinhado à média do mercado. "

        if marca_grupo != "OUTROS" and len(df_grupo) > 1:
            texto += f"No grupo **{marca_grupo}**, a operadora "
            if spread_grp > 0:
                texto += f"destacou-se com **+{spread_grp:.2f} p.p.** acima dos pares."
            else:
                texto += f"ficou **{spread_grp:.2f} p.p.** abaixo da média do grupo."
        
        texto += f"\n\n> *Carteira de Clientes: **{var_vid_op:+.2f}%** (vs **{mediana_mkt_vid:+.2f}%** do mercado).*"
        return texto

    def execute(self, id_operadora: str, trimestre: str):
        """Executa a lógica de análise detalhada da operadora."""
        try:
            # 1. Preparação e Validação
            df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
            
            if df_tri.empty:
                raise FilterError(f"Sem dados disponíveis para o trimestre {trimestre}.")

            # Tipagem segura
            df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
            id_operadora = str(id_operadora)
            df_tri['Marca_Temp'] = df_tri.apply(
                lambda row: extrair_marca(row['razao_social'], row['ID_OPERADORA']), 
                axis=1
            )

            # Busca dados da operadora
            row_op = df_tri[df_tri['ID_OPERADORA'] == id_operadora]
            if row_op.empty:
                raise FilterError(f"Operadora ID {id_operadora} não encontrada no trimestre {trimestre}.")

            dados_op = row_op.iloc[0]
            marca = extrair_marca(dados_op['razao_social'], dados_op['ID_OPERADORA'])

            # 2. Cálculos de Score e Rankings
            try:
                # Score Geral
                df_score = calcular_power_score(df_tri)
                df_score['Rank_Geral'] = df_score['Power_Score'].rank(ascending=False, method='min')
                df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
                
                # Score Grupo
                # Como df_score vem de df_tri, teoricamente já teria a marca, mas garantimos:
                df_score['Marca_Temp'] = df_score.apply(
                    lambda row: extrair_marca(row['razao_social'], row['ID_OPERADORA']), 
                    axis=1
                )
                df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
                df_grupo['Rank_Grupo'] = df_grupo['Power_Score'].rank(ascending=False, method='min')

                # Extração dos valores individuais
                row_geral = df_score[df_score['ID_OPERADORA'] == id_operadora]
                r_geral = int(row_geral['Rank_Geral'].iloc[0]) if not row_geral.empty else "-"
                score = row_geral['Power_Score'].iloc[0] if not row_geral.empty else 0
                
                row_grupo = df_grupo[df_grupo['ID_OPERADORA'] == id_operadora]
                r_grupo = int(row_grupo['Rank_Grupo'].iloc[0]) if not row_grupo.empty else "-"
            
            except Exception:
                r_geral, score, r_grupo = "-", 0, "-"
            
            # 3. KPIs e Insights
            kpis = calcular_variacoes_operadora(self.df_mestre, id_operadora, trimestre)
            if not kpis:
                raise ProcessingError("Não foi possível calcular os KPIs da operadora (dados históricos insuficientes ou inconsistentes).")
                
            insights = analisar_performance_marca(df_tri, dados_op)

            # 4. Geração de Narrativa
            # Agora df_tri já possui 'Marca_Temp', então não vai dar erro
            resumo_narrativo = self._gerar_storytelling(dados_op['razao_social'], trimestre, kpis, df_tri, marca)

            # 5. Preparação de Tabelas
            df_view_grupo = df_grupo.sort_values('Power_Score', ascending=False).copy()
            df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)

            df_view_geral = df_score.sort_values('Power_Score', ascending=False).copy()
            df_view_geral['#'] = df_view_geral['Rank_Geral']

            # 6. Retorno (DTO)
            return {
                "info": {
                    "trimestre": trimestre,
                    "marca": marca,
                    "dados_op": dados_op,
                    "id_op": id_operadora
                },
                "metrics": {
                    "score": score,
                    "rank_geral": r_geral,
                    "rank_grupo": r_grupo,
                    "total_grupo": len(df_grupo),
                    "kpis": kpis,
                    "insights": insights
                },
                "content": {
                    "storytelling": resumo_narrativo,
                    "tabela_grupo": df_view_grupo,
                    "tabela_geral": df_view_geral,
                    "df_full": self.df_mestre # Necessário para gráficos históricos
                }
            }

        except (FilterError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Erro interno no processamento da operadora: {str(e)}")
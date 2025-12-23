import pandas as pd
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.comparativos import calcular_variacoes_operadora, calcular_kpis_vidas_avancados
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_score_vidas

class LivesAnalysisUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def _gerar_storytelling(self, nome_op, trimestre, kpis, kpis_avancados, df_trimestre, marca_grupo):
        """
        Gera diagnóstico focado em Volume de Vidas e estabilidade da carteira.
        """
        # Dados
        var_vid_op = kpis.get('Var_Vidas_QoQ', 0) * 100
        volatilidade = kpis_avancados.get('Volatilidade', 0)
        cagr = kpis_avancados.get('CAGR_1Ano', 0) * 100
        
        # Mercado
        mediana_mkt_vid = df_trimestre['VAR_PCT_VIDAS'].median() * 100
        spread_mkt = var_vid_op - mediana_mkt_vid

        # Grupo
        df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
        if not df_grupo.empty:
            mediana_grp_vid = df_grupo['VAR_PCT_VIDAS'].median() * 100
            spread_grp = var_vid_op - mediana_grp_vid
        else:
            spread_grp = 0

        texto = f"##### 👥 Diagnóstico de Carteira: {trimestre}\n\n"
        
        # 1. Performance Curto Prazo
        texto += f"**1. Variação de Carteira:** A operadora **{nome_op}** registrou variação de **{var_vid_op:+.2f}%** em vidas."
        if spread_mkt > 0:
            texto += f" O crescimento de base superou o mercado em **+{spread_mkt:.2f} p.p.**"
        else:
            texto += f" A captação ficou **{spread_mkt:.2f} p.p.** abaixo da média de mercado."

        # 2. Contexto Grupo
        if marca_grupo != "OUTROS" and len(df_grupo) > 1:
            texto += f"\n\n**2. Contexto Grupo {marca_grupo}:** "
            if spread_grp > 0:
                texto += f"Destaque positivo, ampliando a base **+{spread_grp:.2f} p.p.** acima dos pares."
            else:
                texto += f"Performance de carteira inferior à média do grupo (**{spread_grp:.2f} p.p.**)."

        # 3. Tendência
        texto += f"\n\n**3. Tendência e Estabilidade:** "
        texto += f"A base de clientes apresenta volatilidade de **{volatilidade:.1f}%**"
        texto += "." if volatilidade < 5 else " (alta rotatividade/churn implícito)."
        texto += f" O crescimento estrutural (CAGR 1 ano) é de **{cagr:+.1f}%**."

        return texto

    def execute(self, id_operadora: str, trimestre: str):
        """Executa a lógica de análise de carteira de vidas."""
        try:
            # 1. Preparação
            df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
            
            if df_tri.empty:
                raise FilterError(f"Sem dados disponíveis para o trimestre {trimestre}.")

            # Garante coluna de Marca e Tipagem
            df_tri['Marca_Temp'] = df_tri['razao_social'].apply(extrair_marca)
            df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
            id_operadora = str(id_operadora)

            row_op = df_tri[df_tri['ID_OPERADORA'] == id_operadora]
            if row_op.empty:
                raise FilterError(f"Operadora ID {id_operadora} não encontrada no trimestre {trimestre}.")

            dados_op = row_op.iloc[0]
            marca = extrair_marca(dados_op['razao_social'])

            # 2. Score de Vidas e Rankings
            try:
                df_score = calcular_score_vidas(df_tri)
                df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
                df_score['Rank_Geral'] = df_score['Lives_Score'].rank(ascending=False, method='min')
                
                df_score['Marca_Temp'] = df_score['razao_social'].apply(extrair_marca)
                df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
                df_grupo['Rank_Grupo'] = df_grupo['Lives_Score'].rank(ascending=False, method='min')
                
                # Extração
                row_geral = df_score[df_score['ID_OPERADORA'] == id_operadora]
                r_geral = int(row_geral['Rank_Geral'].iloc[0]) if not row_geral.empty else "-"
                score = row_geral['Lives_Score'].iloc[0] if not row_geral.empty else 0
                
                row_grp = df_grupo[df_grupo['ID_OPERADORA'] == id_operadora]
                r_grupo = int(row_grp['Rank_Grupo'].iloc[0]) if not row_grp.empty else "-"
            
            except Exception:
                r_geral, score, r_grupo = "-", 0, "-"
            
            # 3. KPIs
            kpis = calcular_variacoes_operadora(self.df_mestre, id_operadora, trimestre)
            if not kpis:
                raise ProcessingError("Dados históricos insuficientes.")
            
            kpis_avancados = calcular_kpis_vidas_avancados(self.df_mestre, id_operadora, trimestre)
            insights = analisar_performance_marca(df_tri, dados_op)

            # 4. Storytelling
            resumo_narrativo = self._gerar_storytelling(dados_op['razao_social'], trimestre, kpis, kpis_avancados, df_tri, marca)

            # 5. Tabelas (Ordenação por Lives_Score)
            df_view_grupo = df_grupo.rename(columns={'Lives_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False).copy()
            df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)

            df_view_geral = df_score.rename(columns={'Lives_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False).copy()
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
                    "kpis_avancados": kpis_avancados,
                    "insights": insights
                },
                "content": {
                    "storytelling": resumo_narrativo,
                    "tabela_grupo": df_view_grupo,
                    "tabela_geral": df_view_geral,
                    "df_full": self.df_mestre
                }
            }

        except (FilterError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Erro desconhecido na análise de vidas: {str(e)}")
import pandas as pd
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.comparativos import calcular_variacoes_operadora, calcular_kpis_financeiros_avancados
from backend.analytics.brand_intelligence import analisar_performance_marca, extrair_marca
from backend.analytics.calculadora_score import calcular_score_financeiro

class RevenueAnalysisUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def _gerar_storytelling(self, nome_op, trimestre, kpis, kpis_avancados, df_trimestre, marca_grupo):
        """
        Gera um diagnóstico financeiro COMPLETO (360º) baseado nos dados processados.
        """
        # Dados Básicos
        var_rec_op = kpis.get('Var_Receita_QoQ', 0) * 100
        var_ticket = kpis_avancados.get('Var_Ticket', 0) * 100
        volatilidade = kpis_avancados.get('Volatilidade', 0)
        cagr = kpis_avancados.get('CAGR_1Ano', 0) * 100
        
        # Referências de Mercado
        mediana_mkt_rec = df_trimestre['VAR_PCT_RECEITA'].median() * 100
        spread_mkt = var_rec_op - mediana_mkt_rec

        # Referências de Grupo
        df_grupo = df_trimestre[df_trimestre['Marca_Temp'] == marca_grupo]
        if not df_grupo.empty:
            mediana_grp_rec = df_grupo['VAR_PCT_RECEITA'].median() * 100
            spread_grp = var_rec_op - mediana_grp_rec
        else:
            spread_grp = 0

        # --- NARRATIVA ---
        texto = f"##### 💰 Diagnóstico Financeiro Completo: {trimestre}\n\n"
        
        # 1. Performance Trimestral vs Mercado
        texto += f"**1. Performance Curto Prazo:** A operadora **{nome_op}** variou sua receita em **{var_rec_op:+.2f}%**."
        if spread_mkt > 0:
            texto += f" O desempenho superou a tendência do mercado em **+{spread_mkt:.2f} p.p.**, indicando ganho de tração."
        else:
            texto += f" O desempenho ficou **{spread_mkt:.2f} p.p.** abaixo da média de mercado, sinalizando perda de share relativo."

        # 2. Qualidade da Receita (Ticket)
        texto += f"\n\n**2. Qualidade da Receita (Ticket):** "
        if var_ticket > 0:
            texto += f"O Ticket Médio **cresceu {var_ticket:+.2f}%**, sugerindo capacidade de repasse de preço ou melhora no mix de carteira."
        elif var_ticket < -1:
            texto += f"Houve queda de **{var_ticket:.2f}%** no Ticket Médio, o que pode indicar descontos comerciais agressivos ou perda de contratos premium."
        else:
            texto += "O Ticket Médio manteve-se estável."

        # 3. Visão Grupo
        if marca_grupo != "OUTROS" and len(df_grupo) > 1:
            texto += f"\n\n**3. Contexto Grupo {marca_grupo}:** "
            if spread_grp > 0:
                texto += f"Liderança relativa, crescendo **+{spread_grp:.2f} p.p.** acima dos pares do grupo."
            else:
                texto += f"Desempenho inferior à média do grupo (**{spread_grp:.2f} p.p.**)."

        # 4. Risco e Longo Prazo
        texto += f"\n\n**4. Risco e Tendência:** "
        texto += f"A volatilidade histórica é de **{volatilidade:.1f}%**"
        texto += " (estável)." if volatilidade < 5 else " (alta oscilação)."
        texto += f" O crescimento estrutural (CAGR 1 ano) está em **{cagr:+.1f}%**."

        return texto

    def execute(self, id_operadora: str, trimestre: str):
        """Executa a lógica de análise financeira da operadora."""
        try:
            # 1. Preparação
            df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
            
            if df_tri.empty:
                raise FilterError(f"Sem dados disponíveis para o trimestre {trimestre}.")

            # Garante coluna de Marca
            df_tri['Marca_Temp'] = df_tri['razao_social'].apply(extrair_marca)
            
            # Tipagem segura
            df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
            id_operadora = str(id_operadora)

            row_op = df_tri[df_tri['ID_OPERADORA'] == id_operadora]
            if row_op.empty:
                raise FilterError(f"Operadora ID {id_operadora} não encontrada no trimestre {trimestre}.")

            dados_op = row_op.iloc[0]
            marca = extrair_marca(dados_op['razao_social'])

            # 2. Scores e Rankings Financeiros
            try:
                df_score = calcular_score_financeiro(df_tri)
                
                # Garante tipagem no DF de score também
                df_score['ID_OPERADORA'] = df_score['ID_OPERADORA'].astype(str)
                df_score['Rank_Geral'] = df_score['Revenue_Score'].rank(ascending=False, method='min')
                
                df_score['Marca_Temp'] = df_score['razao_social'].apply(extrair_marca)
                df_grupo = df_score[df_score['Marca_Temp'] == marca].copy()
                df_grupo['Rank_Grupo'] = df_grupo['Revenue_Score'].rank(ascending=False, method='min')
                
                # Extração
                row_geral = df_score[df_score['ID_OPERADORA'] == id_operadora]
                r_geral = int(row_geral['Rank_Geral'].iloc[0]) if not row_geral.empty else "-"
                score = row_geral['Revenue_Score'].iloc[0] if not row_geral.empty else 0
                
                row_grupo = df_grupo[df_grupo['ID_OPERADORA'] == id_operadora]
                r_grupo = int(row_grupo['Rank_Grupo'].iloc[0]) if not row_grupo.empty else "-"
            
            except Exception:
                r_geral, score, r_grupo = "-", 0, "-"

            # 3. KPIs
            # Básicos
            kpis = calcular_variacoes_operadora(self.df_mestre, id_operadora, trimestre)
            if not kpis:
                raise ProcessingError("Dados históricos insuficientes para calcular variações (QoQ/YoY).")
                
            # Avançados (CAGR, Share, Volatilidade)
            kpis_avancados = calcular_kpis_financeiros_avancados(self.df_mestre, id_operadora, trimestre)
            
            # Insights de Marca
            insights = analisar_performance_marca(df_tri, dados_op)

            # 4. Storytelling
            resumo_narrativo = self._gerar_storytelling(dados_op['razao_social'], trimestre, kpis, kpis_avancados, df_tri, marca)

            # 5. Tabelas
            # Grupo
            df_view_grupo = df_grupo.rename(columns={'Revenue_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False).copy()
            df_view_grupo['#'] = range(1, len(df_view_grupo) + 1)

            # Geral
            df_view_geral = df_score.rename(columns={'Revenue_Score': 'Power_Score'}).sort_values('Power_Score', ascending=False).copy()
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
                    "df_full": self.df_mestre # Para gráficos históricos
                }
            }

        except (FilterError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Erro desconhecido na análise financeira: {str(e)}")
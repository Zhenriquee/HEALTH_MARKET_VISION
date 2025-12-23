import pandas as pd
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.comparativos import calcular_variacoes_operadora
from backend.analytics.calculadora_score import calcular_power_score
from backend.analytics.brand_intelligence import extrair_marca

class ComparisonAnalysisUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def _get_op_stats(self, id_op, df_scored, sel_trimestre):
        """Helper para extrair estatísticas de uma única operadora."""
        row = df_scored[df_scored['ID_OPERADORA'] == id_op]
        if row.empty: return None
        
        data = row.iloc[0]
        marca = extrair_marca(data['razao_social'])
        
        # Rank Grupo
        df_grupo = df_scored[df_scored['razao_social'].apply(extrair_marca) == marca]
        try:
            rank_grupo = df_grupo['Power_Score'].rank(ascending=False, method='min')[df_grupo['ID_OPERADORA'] == id_op].iloc[0]
        except:
            rank_grupo = "-"
            
        # KPIs
        kpis = calcular_variacoes_operadora(self.df_mestre, id_op, sel_trimestre)
        
        return {
            'Dados': data,
            'Marca': marca,
            'Rank_Geral': int(data['Rank_Geral']),
            'Rank_Grupo': int(rank_grupo) if rank_grupo != "-" else "-",
            'Total_Grupo': len(df_grupo),
            'KPIs': kpis
        }

    def _prepare_comparison_data(self, stats1, stats2):
        """Gera a estrutura de dados para a tabela comparativa."""
        k1 = stats1['KPIs']
        k2 = stats2['KPIs']
        
        metrics_config = [
            ("Vidas Totais", int(k1['Vidas']), int(k2['Vidas']), False),
            ("Cresc. Vidas (QoQ)", k1['Var_Vidas_QoQ']*100, k2['Var_Vidas_QoQ']*100, True),
            ("Receita Total", k1['Receita'], k2['Receita'], False),
            ("Cresc. Receita (QoQ)", k1['Var_Receita_QoQ']*100, k2['Var_Receita_QoQ']*100, True),
            ("Ticket Médio", k1['Ticket'], k2['Ticket'], False)
        ]
        
        comparison_rows = []
        for label, v1, v2, is_pct in metrics_config:
            if v1 > v2: winner = "op1"
            elif v2 > v1: winner = "op2"
            else: winner = "draw"
            
            comparison_rows.append({
                "label": label,
                "val1": v1,
                "val2": v2,
                "diff": v1 - v2,
                "is_pct": is_pct,
                "winner": winner
            })
            
        return comparison_rows

    def _prepare_radar_data(self, stats1, stats2):
        """
        Normaliza os dados para o gráfico de Radar (Eixos Fixos e Lógica da Versão Anterior).
        """
        # Eixos Fixos conforme versão anterior
        categories = ['Score', 'Vidas', 'Receita', 'Cresc. Vidas', 'Cresc. Receita']
        
        k1 = stats1['KPIs']
        k2 = stats2['KPIs']
        
        # Valores Brutos (Score + 4 KPIs Principais)
        vals1 = [stats1['Dados']['Power_Score'], k1['Vidas'], k1['Receita'], k1['Var_Vidas_QoQ'], k1['Var_Receita_QoQ']]
        vals2 = [stats2['Dados']['Power_Score'], k2['Vidas'], k2['Receita'], k2['Var_Vidas_QoQ'], k2['Var_Receita_QoQ']]
        
        norm_vals1 = []
        norm_vals2 = []
        
        for v1, v2 in zip(vals1, vals2):
            # Normalização baseada no MAIOR valor absoluto entre os dois (Escala Relativa 0-100)
            abs_v1, abs_v2 = abs(v1), abs(v2)
            max_val = max(abs_v1, abs_v2) if max(abs_v1, abs_v2) > 0 else 1
            
            norm_vals1.append((abs_v1 / max_val) * 100)
            norm_vals2.append((abs_v2 / max_val) * 100)
            
        return {
            "categories": categories,
            "norm1": norm_vals1,
            "norm2": norm_vals2,
            "name1": stats1['Dados']['razao_social'],
            "name2": stats2['Dados']['razao_social']
        }

    def execute(self, id_op1: str, id_op2: str, trimestre: str):
        """Executa a lógica completa de comparação."""
        try:
            # 1. Preparação
            df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
            if df_tri.empty:
                raise FilterError(f"Sem dados para {trimestre}.")

            df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
            id_op1 = str(id_op1)
            id_op2 = str(id_op2)
            
            # 2. Rankings Globais
            try:
                df_scored = calcular_power_score(df_tri)
                df_scored['Rank_Geral'] = df_scored['Power_Score'].rank(ascending=False, method='min')
                df_scored['ID_OPERADORA'] = df_scored['ID_OPERADORA'].astype(str)
            except Exception as e:
                raise ProcessingError(f"Erro ao calcular scores: {e}")

            # 3. Extração Individual
            stats1 = self._get_op_stats(id_op1, df_scored, trimestre)
            stats2 = self._get_op_stats(id_op2, df_scored, trimestre)
            
            if not stats1 or not stats2:
                raise FilterError("Uma das operadoras selecionadas não possui dados neste trimestre.")

            # 4. Comparação Direta (Tabela)
            comp_rows = self._prepare_comparison_data(stats1, stats2)
            
            # 5. Dados Radar (Gráfico - Usando a lógica fixa agora)
            # Removemos a dependência de comp_rows para garantir os eixos fixos
            radar_data = self._prepare_radar_data(stats1, stats2)

            return {
                "op1": stats1,
                "op2": stats2,
                "comparison_table": comp_rows,
                "radar_data": radar_data
            }

        except (FilterError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Erro desconhecido na comparação: {str(e)}")
import pandas as pd
import numpy as np
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.brand_intelligence import extrair_marca # Importante

class CalculationExplainerUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def execute(self, id_operadora: str, trimestre: str):
        """
        Reconstrói o cálculo do Power Score, Spreads e Métricas de Grupo passo a passo.
        """
        # 1. Universo de Comparação
        df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
        
        if df_tri.empty:
            raise FilterError(f"Sem dados no trimestre {trimestre}")

        # Garante coluna de Marca
        df_tri['Marca_Temp'] = df_tri['razao_social'].apply(extrair_marca)
        
        # Tipagem e Busca
        df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
        id_operadora = str(id_operadora)
        
        row_op = df_tri[df_tri['ID_OPERADORA'] == id_operadora]
        if row_op.empty:
            raise FilterError("Operadora não encontrada.")
            
        dados_op = row_op.iloc[0]
        
        # --- PARTE 1: POWER SCORE (Lógica Mantida) ---
        series_vidas = df_tri['NR_BENEF_T'].fillna(0)
        logs_mercado_vidas = np.log1p(series_vidas)
        min_v, max_v = logs_mercado_vidas.min(), logs_mercado_vidas.max()
        vidas_real = dados_op['NR_BENEF_T']
        vidas_log = np.log1p(vidas_real)
        score_vidas = ((vidas_log - min_v) / (max_v - min_v)) * 100 if max_v > min_v else 0

        series_rec = df_tri['VL_SALDO_FINAL'].fillna(0).clip(lower=0)
        logs_mercado_rec = np.log1p(series_rec)
        min_r, max_r = logs_mercado_rec.min(), logs_mercado_rec.max()
        rec_real = max(0, dados_op['VL_SALDO_FINAL'])
        rec_log = np.log1p(rec_real)
        score_rec = ((rec_log - min_r) / (max_r - min_r)) * 100 if max_r > min_r else 0

        growth_mkt = df_tri['VAR_PCT_VIDAS'].fillna(0).clip(-0.5, 0.5)
        min_p, max_p = growth_mkt.min(), growth_mkt.max()
        perf_real = dados_op.get('VAR_PCT_VIDAS', 0)
        perf_clip = max(min(perf_real, 0.5), -0.5)
        score_perf = ((perf_clip - min_p) / (max_p - min_p)) * 100 if max_p > min_p else 50
        
        final_score = (score_vidas * 0.4) + (score_rec * 0.4) + (score_perf * 0.2)

        # --- PARTE 2: EXTRAS (Spread e Grupo) ---
        
        # A. Performance Relativa (Spread)
        # Receita
        op_cresc_rec = dados_op.get('VAR_PCT_RECEITA', 0)
        mkt_mediana_rec = df_tri['VAR_PCT_RECEITA'].median()
        spread_rec = op_cresc_rec - mkt_mediana_rec
        
        # Vidas
        op_cresc_vid = dados_op.get('VAR_PCT_VIDAS', 0)
        mkt_mediana_vid = df_tri['VAR_PCT_VIDAS'].median()
        spread_vid = op_cresc_vid - mkt_mediana_vid
        
        # B. Métricas de Grupo
        marca = extrair_marca(dados_op['razao_social'])
        df_grupo = df_tri[df_tri['Marca_Temp'] == marca]
        
        # Share (Receita e Vidas)
        total_rec_grupo = df_grupo['VL_SALDO_FINAL'].sum()
        share_rec = (rec_real / total_rec_grupo) * 100 if total_rec_grupo > 0 else 0
        
        total_vid_grupo = df_grupo['NR_BENEF_T'].sum()
        share_vid = (vidas_real / total_vid_grupo) * 100 if total_vid_grupo > 0 else 0
        
        # Crescimento Grupo (Mediana)
        grp_mediana_vid = df_grupo['VAR_PCT_VIDAS'].median()

        return {
            "dados_op": dados_op,
            "passos_score": {
                "vidas": {"real": vidas_real, "log": vidas_log, "min": min_v, "max": max_v, "score": score_vidas},
                "receita": {"real": rec_real, "log": rec_log, "min": min_r, "max": max_r, "score": score_rec},
                "perf": {"real": perf_real, "clip": perf_clip, "min": min_p, "max": max_p, "score": score_perf},
                "final": final_score
            },
            "extras": {
                "spread_receita": {
                    "op": op_cresc_rec, "mkt": mkt_mediana_rec, "res": spread_rec
                },
                "spread_vidas": {
                    "op": op_cresc_vid, "mkt": mkt_mediana_vid, "res": spread_vid
                },
                "grupo": {
                    "marca": marca,
                    "total_op_rec": rec_real, "total_grp_rec": total_rec_grupo, "share_rec": share_rec,
                    "total_op_vid": vidas_real, "total_grp_vid": total_vid_grupo, "share_vid": share_vid,
                    "mediana_cresc_vid": grp_mediana_vid
                }
            }
        }
import pandas as pd
import numpy as np
from backend.exceptions import ProcessingError, FilterError
from backend.analytics.brand_intelligence import extrair_marca

class CalculationExplainerUseCase:
    def __init__(self, df_mestre):
        self.df_mestre = df_mestre

    def execute(self, id_operadora: str, trimestre: str):
        """
        Reconstrói o cálculo do Power Score (Lógica LINEAR oficial), Spreads e Métricas de Grupo.
        """
        # 1. Universo de Comparação
        df_tri = self.df_mestre[self.df_mestre['ID_TRIMESTRE'] == trimestre].copy()
        
        if df_tri.empty:
            raise FilterError(f"Sem dados no trimestre {trimestre}")

        # CORREÇÃO 1: Uso de lambda para passar razao_social E ID_OPERADORA
        df_tri['Marca_Temp'] = df_tri.apply(
            lambda row: extrair_marca(row['razao_social'], row['ID_OPERADORA']), 
            axis=1
        )
        
        df_tri['ID_OPERADORA'] = df_tri['ID_OPERADORA'].astype(str)
        id_operadora = str(id_operadora)
        
        row_op = df_tri[df_tri['ID_OPERADORA'] == id_operadora]
        if row_op.empty:
            raise FilterError("Operadora não encontrada.")
            
        dados_op = row_op.iloc[0]
        
        # --- PARTE 1: POWER SCORE (Lógica LINEAR - Igual calculadora_score.py) ---
        
        # A. VIDAS (Peso 40%) - Normalização Linear
        max_vidas = df_tri['NR_BENEF_T'].max() or 1
        vidas_real = dados_op['NR_BENEF_T']
        score_vidas = (vidas_real / max_vidas) * 100

        # B. RECEITA (Peso 40%) - Normalização Linear
        max_receita = df_tri['VL_SALDO_FINAL'].max() or 1
        rec_real = dados_op['VL_SALDO_FINAL']
        score_rec = (rec_real / max_receita) * 100

        # C. PERFORMANCE (Peso 20%) - Composta (Vidas + Receita)
        CLIP_MIN, CLIP_MAX = -0.10, 0.10
        
        # C1. Performance Vidas
        perf_vid_real = dados_op.get('VAR_PCT_VIDAS', 0)
        perf_vid_clip = max(min(perf_vid_real, CLIP_MAX), CLIP_MIN)
        score_p_vid = ((perf_vid_clip - CLIP_MIN) / (CLIP_MAX - CLIP_MIN)) * 100
        
        # C2. Performance Receita
        perf_rec_real = dados_op.get('VAR_PCT_RECEITA', 0)
        perf_rec_clip = max(min(perf_rec_real, CLIP_MAX), CLIP_MIN)
        score_p_rec = ((perf_rec_clip - CLIP_MIN) / (CLIP_MAX - CLIP_MIN)) * 100
        
        # C3. Performance Média
        score_perf_total = (score_p_vid + score_p_rec) / 2
        
        # D. FÓRMULA FINAL
        final_score = (score_vidas * 0.40) + (score_rec * 0.40) + (score_perf_total * 0.20)

        # --- PARTE 2: EXTRAS (Spread e Grupo) ---
        op_cresc_rec = dados_op.get('VAR_PCT_RECEITA', 0)
        mkt_mediana_rec = df_tri['VAR_PCT_RECEITA'].median()
        spread_rec = op_cresc_rec - mkt_mediana_rec
        
        op_cresc_vid = dados_op.get('VAR_PCT_VIDAS', 0)
        mkt_mediana_vid = df_tri['VAR_PCT_VIDAS'].median()
        spread_vid = op_cresc_vid - mkt_mediana_vid
        
        # CORREÇÃO 2: Passagem correta dos dois argumentos
        marca = extrair_marca(dados_op['razao_social'], dados_op['ID_OPERADORA'])
        
        df_grupo = df_tri[df_tri['Marca_Temp'] == marca]
        
        total_rec_grupo = df_grupo['VL_SALDO_FINAL'].sum()
        share_rec = (rec_real / total_rec_grupo) * 100 if total_rec_grupo > 0 else 0
        total_vid_grupo = df_grupo['NR_BENEF_T'].sum()
        share_vid = (vidas_real / total_vid_grupo) * 100 if total_vid_grupo > 0 else 0
        grp_mediana_vid = df_grupo['VAR_PCT_VIDAS'].median()

        return {
            "dados_op": dados_op,
            "passos_score": {
                "vidas": {
                    "real": vidas_real, 
                    "max_mkt": max_vidas, 
                    "score": score_vidas
                },
                "receita": {
                    "real": rec_real, 
                    "max_mkt": max_receita, 
                    "score": score_rec
                },
                "perf": {
                    "vid_real": perf_vid_real, "vid_clip": perf_vid_clip, "vid_score": score_p_vid,
                    "rec_real": perf_rec_real, "rec_clip": perf_rec_clip, "rec_score": score_p_rec,
                    "final_score": score_perf_total,
                    "clip_min": CLIP_MIN, "clip_max": CLIP_MAX
                },
                "final": final_score
            },
            "extras": {
                "spread_receita": {"op": op_cresc_rec, "mkt": mkt_mediana_rec, "res": spread_rec},
                "spread_vidas": {"op": op_cresc_vid, "mkt": mkt_mediana_vid, "res": spread_vid},
                "grupo": {
                    "marca": marca,
                    "total_op_rec": rec_real, "total_grp_rec": total_rec_grupo, "share_rec": share_rec,
                    "total_op_vid": vidas_real, "total_grp_vid": total_vid_grupo, "share_vid": share_vid,
                    "mediana_cresc_vid": grp_mediana_vid
                }
            }
        }
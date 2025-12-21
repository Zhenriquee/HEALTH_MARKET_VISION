import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_spread_chart(df_mestre, id_operadora, nome_operadora, tipo_kpi, tipo_comparacao, filtro_grupo=None):
    """
    Gera gráfico de Spread (Alpha).
    """
    col_valor = 'VL_SALDO_FINAL' if tipo_kpi == 'Receita' else 'NR_BENEF_T'
    col_var_pct = 'VAR_PCT_RECEITA' if tipo_kpi == 'Receita' else 'VAR_PCT_VIDAS'
    label_titulo = f"Spread {tipo_kpi}: {nome_operadora} vs {tipo_comparacao}"
    
    timeline_completa = sorted(df_mestre['ID_TRIMESTRE'].unique())

    # Dados Operadora
    df_op = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].copy()
    df_op = df_op.set_index('ID_TRIMESTRE').reindex(timeline_completa)
    s_op_pct = df_op[col_valor].pct_change() * 100

    # Dados Referência
    if tipo_comparacao == 'Grupo' and filtro_grupo:
        df_ref = df_mestre[df_mestre['Marca_Temp'] == filtro_grupo].copy()
    else:
        df_ref = df_mestre.copy() # Mercado Geral
        
    s_ref_pct = df_ref.groupby('ID_TRIMESTRE')[col_var_pct].median() * 100
    s_ref_pct = s_ref_pct.reindex(timeline_completa)

    s_spread = s_op_pct - s_ref_pct
    
    df_graf = pd.DataFrame({
        'ID_TRIMESTRE': timeline_completa,
        'SPREAD': s_spread.values,
        'OP_PCT': s_op_pct.values,
        'REF_PCT': s_ref_pct.values
    }).dropna(subset=['SPREAD']).sort_values('ID_TRIMESTRE')

    if df_graf.empty: return None

    df_graf['Cor'] = np.where(df_graf['SPREAD'] >= 0, 'Superou', 'Abaixo')
    
    fig = px.bar(
        df_graf, x='ID_TRIMESTRE', y='SPREAD', color='Cor',
        color_discrete_map={'Superou': '#2E8B57', 'Abaixo': '#CD5C5C'},
        custom_data=['OP_PCT', 'REF_PCT']
    )
    
    fig.update_layout(
        title=dict(text=label_titulo, font=dict(size=14)),
        xaxis={'categoryorder':'category ascending'},
        xaxis_title=None, yaxis_title="Spread (p.p.)",
        legend_title=None, hovermode="x unified", height=350,
        showlegend=False, yaxis=dict(ticksuffix=" p.p.")
    )
    
    fig.update_traces(
        hovertemplate="<br>".join([
            "<b>Spread: %{y:.2f} p.p.</b>",
            f"{nome_operadora}: %{{customdata[0]:.2f}}%",
            f"{tipo_comparacao}: %{{customdata[1]:.2f}}%"
        ])
    )
    fig.add_hline(y=0, line_width=1, line_color="black")
    return fig

def render_evolution_chart(df_mestre, id_operadora):
    """
    Gera gráfico de Evolução Histórica (Boca de Jacaré).
    """
    df_hist = df_mestre[df_mestre['ID_OPERADORA'] == str(id_operadora)].sort_values('ID_TRIMESTRE')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['NR_BENEF_T'], 
        name='Vidas', line=dict(color='#1f77b4', width=3), 
        hovertemplate='%{y:,.0f} Vidas'
    ))
    fig.add_trace(go.Scatter(
        x=df_hist['ID_TRIMESTRE'], y=df_hist['VL_SALDO_FINAL'], 
        name='Receita (R$)', line=dict(color='#2ca02c', width=3, dash='dot'), 
        yaxis='y2', hovertemplate='R$ %{y:,.2f}'
    ))
    
    fig.update_layout(
        title="", xaxis=dict(title="Trimestre"),
        yaxis=dict(
            title=dict(text="Vidas", font=dict(color="#1f77b4")), 
            tickfont=dict(color="#1f77b4"), tickformat=",.0f"
        ),
        yaxis2=dict(
            title=dict(text="Receita (R$)", font=dict(color="#2ca02c")), 
            tickfont=dict(color="#2ca02c"), 
            overlaying='y', side='right', tickprefix="R$ ", tickformat=",.2s"
        ),
        legend=dict(x=0, y=1.1, orientation='h'), 
        hovermode="x unified", height=400
    )
    return fig
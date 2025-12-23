def get_formula_explicacao(indicador: str):
    """
    Retorna o título, a fórmula matemática e a explicação textual do indicador.
    """
    formulas = {
        "Power Score": {
            "titulo": "⚡ Power Score (Nota Geral)",
            "formula": r"Score = (0.4 \times Vidas_{norm}) + (0.4 \times Receita_{norm}) + (0.2 \times Performance)",
            "texto": """
            **O que é:** Uma nota de 0 a 100 que equilibra tamanho e qualidade.
            
            **Passo a Passo:**
            1. **Normalização de Vidas (40%):** Comparamos o logaritmo das vidas da operadora com o máximo do mercado.
            2. **Normalização de Receita (40%):** O mesmo processo feito com o faturamento.
            3. **Performance (20%):** Baseado no crescimento recente (QoQ).
            
            *Isso evita que apenas operadoras gigantes tenham score alto, valorizando também as pequenas que crescem rápido.*
            """
        },
        "Spread": {
            "titulo": "📊 Spread (Diferencial de Crescimento)",
            "formula": r"Spread = \Delta\%_{Operadora} - \Delta\%_{Mercado}",
            "texto": """
            **O que é:** Mede se a operadora está ganhando ou perdendo terreno (Market Share) para a concorrência.
            
            **Exemplo:**
            * Se a operadora cresceu **15%**.
            * E o mercado cresceu **10%**.
            * O Spread é **+5 p.p.** (Pontos Percentuais).
            """
        },
        "Ticket Medio": {
            "titulo": "🎟️ Ticket Médio",
            "formula": r"Ticket = \frac{Receita Total (R\$)}{Total de Vidas}",
            "texto": """
            **O que é:** O valor médio que a operadora recebe por beneficiário por trimestre.
            Indica o poder de precificação e o perfil da carteira (Premium vs Popular).
            """
        },
        # Adicione outros aqui...
    }
    
    return formulas.get(indicador, {
        "titulo": f"Indefinido: {indicador}", 
        "formula": "", 
        "texto": "Sem explicação cadastrada."
    })
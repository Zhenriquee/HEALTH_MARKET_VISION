def aplicar_estilo_ranking(df):
    """
    Aplica a lógica de cores nas linhas do ranking para o Pandas Styler.
    """
    def colorir_linhas(row):
        # Garante que temos a coluna Rank ou usa o índice
        rank = row.get('Rank', row.name + 1)
        
        if rank <= 10:
            color = '#d4edda' # Verde (Top 10)
        elif rank <= 20:
            color = '#fff3cd' # Amarelo (Top 20)
        elif rank <= 30:
            color = '#ffeeba' # Laranja (Top 30)
        else:
            color = 'white'
            
        return [f'background-color: {color}; color: black'] * len(row)

    return df.style.apply(colorir_linhas, axis=1)
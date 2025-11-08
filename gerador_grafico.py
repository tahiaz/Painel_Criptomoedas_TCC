# Arquivo: gerador_grafico.py
# Lê os dados salvos pelo robô e cria uma visualização.

import pandas as pd
import matplotlib.pyplot as plt
import os

# --- Nome do arquivo de onde vamos ler os dados ---
ARQUIVO_HISTORICO = 'historico_precos.csv'

def gerar_grafico():
    """
    Lê o arquivo de histórico de preços e gera um gráfico com a evolução
    de cada criptomoeda ao longo do tempo.
    """
    print(f"Tentando gerar gráfico a partir do arquivo '{ARQUIVO_HISTORICO}'...")

    # --- Verificação 1: O arquivo de histórico existe? ---
    if not os.path.exists(ARQUIVO_HISTORICO):
        print(f"\033[91mERRO: O arquivo '{ARQUIVO_HISTORICO}' não foi encontrado.\033[0m")
        print("Por favor, execute o script 'rastreador_com_historico.py' primeiro para coletar alguns dados.")
        return

    # --- Verificação 2: O arquivo tem dados suficientes? ---
    try:
        # Usamos a biblioteca pandas para carregar os dados do CSV de forma muito fácil
        dados = pd.read_csv(ARQUIVO_HISTORICO)
        if dados.empty or len(dados) < 2:
            print(f"\033[93mAviso: O arquivo '{ARQUIVO_HISTORICO}' não tem dados suficientes para gerar um gráfico interessante.\033[0m")
            print("Deixe o 'rastreador_com_historico.py' rodar por mais tempo (pelo menos duas rodadas).")
            return
    except Exception as e:
        print(f"\033[91mERRO ao ler o arquivo CSV: {e}\033[0m")
        return

    print("Dados carregados com sucesso. Preparando o gráfico...")

    # --- Preparação dos Dados ---
    # Converte a coluna 'timestamp' de texto para um formato de data/hora real,
    # para que o eixo X do gráfico fique ordenado corretamente.
    dados['timestamp'] = pd.to_datetime(dados['timestamp'])

    # --- Criação do Gráfico ---
    plt.style.use('seaborn-v0_8-whitegrid') # Deixa o gráfico com um estilo bonito
    plt.figure(figsize=(12, 7)) # Define um bom tamanho para a janela do gráfico

    # Loop que desenha uma linha para cada moeda encontrada no arquivo
    for moeda in dados['moeda'].unique():
        # Filtra os dados para pegar apenas os de uma moeda por vez
        dados_da_moeda = dados[dados['moeda'] == moeda]
        
        # Desenha a linha no gráfico
        plt.plot(
            dados_da_moeda['timestamp'], 
            dados_da_moeda['preco_brl'], 
            marker='o',           # Adiciona um círculo em cada ponto de dado
            linestyle='-',        # Liga os pontos com uma linha
            label=moeda.capitalize() # Adiciona o nome da moeda na legenda
        )

    # --- Toques Finais e Títulos ---
    plt.title('Evolução dos Preços das Criptomoedas', fontsize=16)
    plt.xlabel('Data e Hora da Coleta', fontsize=12)
    plt.ylabel('Preço em Reais (BRL)', fontsize=12)
    plt.legend(title='Moedas', fontsize=10) # Mostra a legenda
    
    # Melhora a visualização das datas no eixo X
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout() # Ajusta o layout para não cortar os textos

    # --- Exibição do Gráfico ---
    print("\03-3[92mGráfico gerado com sucesso! Exibindo em uma nova janela...\033[0m")
    plt.show()


if __name__ == "__main__":
    gerar_grafico()
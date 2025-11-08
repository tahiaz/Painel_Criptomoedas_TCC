# Arquivo: rastreador_cripto_com_historico.py
# Baseado no seu protótipo funcional, agora com a capacidade de salvar dados.

import requests
import time
import json
import csv
from datetime import datetime

# --- CONFIGURAÇÃO ---
MOEDAS_PARA_MONITORAR = ["bitcoin", "ethereum", "cardano", "solana"]
ARQUIVO_HISTORICO = 'historico_precos.csv' # Nome do nosso "banco de dados"

# --- Dicionário para guardar os últimos preços vistos ---
precos_anteriores = {}

def iniciar_arquivo_csv():
    """Verifica se o arquivo de histórico existe. Se não, cria ele com o cabeçalho."""
    try:
        # O modo 'x' tenta criar um arquivo e dá erro se ele já existir.
        with open(ARQUIVO_HISTORICO, 'x', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'moeda', 'preco_brl']) # Escreve as colunas
            print(f"Arquivo de histórico '{ARQUIVO_HISTORICO}' criado.")
    except FileExistsError:
        # Se o arquivo já existe, apenas informamos.
        print(f"Arquivo de histórico '{ARQUIVO_HISTORICO}' já existe. Adicionando novos dados...")
        pass

def salvar_dado_csv(timestamp, moeda, preco):
    """Adiciona uma nova linha de dados ao nosso arquivo CSV."""
    # O modo 'a' (append) abre o arquivo e adiciona conteúdo no final.
    with open(ARQUIVO_HISTORICO, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, moeda, preco])

def buscar_precos_cripto(lista_de_moedas):
    """Busca os preços atuais das criptomoedas na API da CoinGecko."""
    ids_formatados = ",".join(lista_de_moedas)
    url_api = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_formatados}&vs_currencies=brl"
    
    print(f"Buscando preços para: {ids_formatados}...")
    try:
        resposta = requests.get(url_api)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        print(f"\033[91mERRO ao conectar na API: {e}\033[0m")
        return None

def monitorar():
    """Função principal que orquestra o monitoramento e salvamento."""
    iniciar_arquivo_csv() # Garante que o arquivo CSV está pronto
    
    while True:
        print("\n" + "="*50)
        print("  INICIANDO NOVA RODADA DE VERIFICAÇÃO DE PREÇOS")
        print("="*50)

        dados_precos = buscar_precos_cripto(MOEDAS_PARA_MONITORAR)

        if dados_precos:
            agora_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for moeda_id in MOEDAS_PARA_MONITORAR:
                if moeda_id in dados_precos and dados_precos[moeda_id].get('brl'):
                    preco_atual = dados_precos[moeda_id]['brl']
                    
                    print(f"  - {moeda_id.capitalize()}: R$ {preco_atual:,.2f}")
                    
                    # A MÁGICA ACONTECE AQUI: salvamos o dado coletado
                    salvar_dado_csv(agora_timestamp, moeda_id, preco_atual)
                    
                    # Compara com o preço anterior para exibir alerta
                    ultimo_preco = precos_anteriores.get(moeda_id)
                    if ultimo_preco:
                        if preco_atual < ultimo_preco:
                            print(f"    \033[92m--> CAIU!\033[0m")
                        elif preco_atual > ultimo_preco:
                            print(f"    \033[91m--> SUBIU!\033[0m")
                    precos_anteriores[moeda_id] = preco_atual
        
        intervalo = 60 # 1 minuto
        print(f"\n--- Dados salvos. Próxima rodada em {intervalo / 60:.0f} minutos. ---")
        time.sleep(intervalo)

if __name__ == "__main__":
    monitorar()
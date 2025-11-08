# Arquivo: rastreador_cripto.py (Versão Final - API Estável CoinGecko)

import requests
import time
import json

# --- CONFIGURAÇÃO ---
# IDs das moedas que vamos monitorar. Você pode encontrar mais IDs no site da CoinGecko.
# Por exemplo: bitcoin, ethereum, cardano, solana, dogecoin
MOEDAS_PARA_MONITORAR = ["bitcoin", "ethereum", "cardano"]

# --- Dicionário para guardar os últimos preços vistos ---
precos_anteriores = {}

def buscar_precos_cripto(lista_de_moedas):
    """
    Busca os preços atuais das criptomoedas na API da CoinGecko.
    A API permite buscar várias moedas em uma única chamada.
    """
    # Juntamos a lista de moedas em uma string separada por vírgula, ex: "bitcoin,ethereum,cardano"
    ids_formatados = ",".join(lista_de_moedas)
    
    # Este é o endereço da API. É público e não precisa de chave.
    url_api = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_formatados}&vs_currencies=brl"
    
    print(f"Buscando preços para: {ids_formatados}...")
    
    try:
        resposta = requests.get(url_api)
        resposta.raise_for_status() # Lança erro se a conexão falhar
        
        dados = resposta.json()
        
        # A API retorna um dicionário como: 
        # {'bitcoin': {'brl': 350000}, 'ethereum': {'brl': 20000}}
        return dados

    except requests.exceptions.RequestException as e:
        print(f"\033[91mERRO: Falha ao conectar na API da CoinGecko.\033[0m")
        print(f"Verifique sua conexão com a internet. Detalhe: {e}")
        return None
    except json.JSONDecodeError:
        print(f"\033[91mERRO: A resposta da API não foi um JSON válido.\033[0m")
        return None

def monitorar():
    """Função principal que orquestra o monitoramento."""
    
    while True:
        print("\n" + "="*50)
        print("  INICIANDO NOVA RODADA DE VERIFICAÇÃO DE PREÇOS CRIPTO")
        print("="*50)

        dados_precos = buscar_precos_cripto(MOEDAS_PARA_MONITORAR)

        if dados_precos:
            # Loop através das moedas que monitoramos
            for moeda_id in MOEDAS_PARA_MONITORAR:
                if moeda_id in dados_precos:
                    preco_atual = dados_precos[moeda_id].get('brl')
                    
                    if preco_atual:
                        print(f"  - {moeda_id.capitalize()}: R$ {preco_atual:,.2f}")
                        
                        ultimo_preco = precos_anteriores.get(moeda_id)
                        
                        if ultimo_preco:
                            if preco_atual < ultimo_preco:
                                print(f"    \033[92m--> O PREÇO CAIU! (Era R$ {ultimo_preco:,.2f})\033[0m")
                            elif preco_atual > ultimo_preco:
                                print(f"    \033[91m--> O PREÇO SUBIU! (Era R$ {ultimo_preco:,.2f})\033[0m")

                        precos_anteriores[moeda_id] = preco_atual
                else:
                    print(f"  - Não foi possível encontrar o preço para '{moeda_id}' na resposta.")
        
        intervalo = 300 # 5 minutos
        print(f"\n--- Verificação concluída. Próxima rodada em {intervalo / 60:.0f} minutos. ---")
        time.sleep(intervalo)

if __name__ == "__main__":
    monitorar()
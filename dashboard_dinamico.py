# Arquivo: dashboard_dinamico.py (Versão 10.4 - Carregamento Dinâmico)
# Este script agora lê as configurações do arquivo 'config_dashboard.json'

import requests
import time
import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.font_manager import FontProperties
import matplotlib.gridspec as gridspec
import os
import json # Importamos json para ler o arquivo de config

try:
    import mplfinance as mpf
except ImportError:
    print("ERRO: Biblioteca 'mplfinance' não encontrada. Instale com: pip install mplfinance")
    exit()

# --- MUDANÇA 1: Carregar a configuração do arquivo ---
try:
    with open('config_dashboard.json', 'r') as f:
        config = json.load(f)
    MOEDAS_PARA_MONITORAR = config.get('moedas', ["bitcoin", "ethereum", "cardano", "solana"])
    CORES_MOEDAS = config.get('cores', { "bitcoin": "#F7931A", "ethereum": "#627EEA", "cardano": "#0033AD", "solana": "#9945FF" })
    print(f"Configuração carregada. Monitorando: {MOEDAS_PARA_MONITORAR}")
except FileNotFoundError:
    print("AVISO: Arquivo 'config_dashboard.json' não encontrado. Usando moedas padrão.")
    print("Para configurar suas moedas, execute o 'iniciar_dashboard.py' primeiro.")
    MOEDAS_PARA_MONITORAR = ["bitcoin", "ethereum", "cardano", "solana"]
    CORES_MOEDAS = { "bitcoin": "#F7931A", "ethereum": "#627EEA", "cardano": "#0033AD", "solana": "#9945FF" }
# ----------------------------------------------------

# --- SEÇÃO DE ESTILO E FONTES ---
COR_FUNDO = '#131722'
COR_TEXTO_PRI = '#FFFFFF'
# (O resto das suas variáveis de estilo e fontes permanece igual)
COR_TEXTO_SEC = '#B2B5BE'
COR_GRID = '#2A2E39'
COR_VERDE = '#26A69A'
COR_VERMELHO = '#EF5350'
plt.rcParams['toolbar'] = 'none'

try:
    caminho_fonte = 'RobotoMono-Regular.ttf'
    fonte_titulo_painel = FontProperties(fname=caminho_fonte, size=20, weight='bold')
    fonte_titulo_moeda = FontProperties(fname=caminho_fonte, size=15, weight='bold')
    fonte_preco = FontProperties(fname=caminho_fonte, size=22, weight='bold')
    fonte_variacao = FontProperties(fname=caminho_fonte, size=12)
    fonte_relogio = FontProperties(fname=caminho_fonte, size=18, weight='bold')
except FileNotFoundError:
    print("AVISO: Fonte 'RobotoMono-Regular.ttf' não encontrada. Usando fonte padrão.")
    fonte_titulo_painel, fonte_titulo_moeda, fonte_preco, fonte_variacao, fonte_relogio = [None] * 5

# --- CONFIGURAÇÃO (Restante) ---
INTERVALO_DADOS_SEGUNDOS = 300
segundos_desde_ultima_att = INTERVALO_DADOS_SEGUNDOS
dados_atuais_cache = {}
dados_ohlc_cache = {}

# (Todo o resto do seu código - buscar_dados_ohlc, buscar_preco_atual, 
# animate, atualizar_plots_moedas, etc. - permanece EXATAMENTE IGUAL)

def buscar_dados_ohlc(moeda_id, dias=30):
    url = f"https://api.coingecko.com/api/v3/coins/{moeda_id}/ohlc?vs_currency=brl&days={dias}"
    try:
        time.sleep(1.2); resposta = requests.get(url, timeout=10); resposta.raise_for_status(); dados = resposta.json()
        df = pd.DataFrame(dados, columns=['time', 'open', 'high', 'low', 'close']); df['time'] = pd.to_datetime(df['time'], unit='ms'); df.set_index('time', inplace=True)
        return df
    except Exception: return None

def buscar_preco_atual(lista_de_moedas):
    ids = ",".join(lista_de_moedas)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl&include_24hr_change=true"
    try:
        resposta = requests.get(url, timeout=10); resposta.raise_for_status()
        return resposta.json()
    except Exception as e: print(f"\033[91mERRO ao conectar na API: {e}\033[0m"); return None

def animate(i):
    global segundos_desde_ultima_att, dados_atuais_cache, dados_ohlc_cache
    if segundos_desde_ultima_att >= INTERVALO_DADOS_SEGUNDOS:
        print("\n" + "="*50 + "\nINICIANDO NOVA RODADA DE VERIFICAÇÃO DE DADOS\n" + "="*50)
        dados_atuais_cache = buscar_preco_atual(MOEDAS_PARA_MONITORAR)
        if dados_atuais_cache:
            for moeda_id in MOEDAS_PARA_MONITORAR:
                dados_ohlc_cache[moeda_id] = buscar_dados_ohlc(moeda_id)
        segundos_desde_ultima_att = 0
    
    for ax in [ax1, ax2, ax3, ax4, ax_relogio]: ax.clear()
    atualizar_plots_moedas()
    atualizar_plot_relogio()
    segundos_desde_ultima_att += 1

def atualizar_plots_moedas():
    if not dados_atuais_cache: return
    for ax, moeda_id in zip([ax1, ax2, ax3, ax4], MOEDAS_PARA_MONITORAR):
        dados_ohlc = dados_ohlc_cache.get(moeda_id)
        if dados_ohlc is not None and moeda_id in dados_atuais_cache:
            preco_atual = dados_atuais_cache[moeda_id]['brl']
            variacao_24h = dados_atuais_cache[moeda_id]['brl_24h_change']
            desenhar_subplot_moeda(ax, moeda_id, preco_atual, variacao_24h, dados_ohlc)
        else:
            desenhar_subplot_carregando(ax, moeda_id) # Adicionando a função de carregamento

def atualizar_plot_relogio():
    ax_relogio.set_facecolor(COR_FUNDO)
    tempo_restante = INTERVALO_DADOS_SEGUNDOS - segundos_desde_ultima_att
    minutos, segundos = divmod(tempo_restante, 60)
    texto_relogio = f"{minutos:02d}:{segundos:02d}"
    progresso = segundos_desde_ultima_att / INTERVALO_DADOS_SEGUNDOS
    ax_relogio.pie([1], radius=1.0, colors=[COR_GRID], startangle=90)
    ax_relogio.pie([progresso, 1 - progresso], radius=1.0, colors=[COR_TEXTO_PRI, 'none'], startangle=90, counterclock=False)
    ax_relogio.pie([1], radius=0.8, colors=[COR_FUNDO], startangle=90)
    ax_relogio.text(0, 0, texto_relogio, ha='center', va='center', fontproperties=fonte_relogio, color=COR_TEXTO_PRI)
    ax_relogio.set(aspect="equal"); [spine.set_edgecolor('none') for spine in ax_relogio.spines.values()]

def desenhar_subplot_moeda(ax, moeda_id, preco_atual, variacao_24h, dados_ohlc):
    cor = CORES_MOEDAS.get(moeda_id, COR_TEXTO_PRI)
    cor_variacao = COR_VERDE if variacao_24h >= 0 else COR_VERMELHO
    
    mc = mpf.make_marketcolors(up=COR_VERDE, down=COR_VERMELHO, inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, facecolor=COR_FUNDO)
    
    mpf.plot(dados_ohlc, type='candle', ax=ax, style=s)
    ax.axhline(preco_atual, color=cor, linestyle='--', linewidth=1, alpha=0.8)
    ax.set_title(moeda_id.upper(), fontproperties=fonte_titulo_moeda, color=COR_TEXTO_PRI, loc='left', pad=10)
    ax.text(0.05, 0.75, f"R$ {preco_atual:,.2f}", transform=ax.transAxes, ha='left', va='top', fontproperties=fonte_preco, color=cor)
    ax.text(0.95, 0.95, f"{variacao_24h:+.2f}%", transform=ax.transAxes, ha='right', va='top', fontproperties=fonte_variacao, color=cor_variacao)
    ax.set_ylabel(''); ax.set_xlabel('')
    ax.tick_params(axis='y', colors=COR_TEXTO_SEC, labelsize=8); ax.tick_params(axis='x', colors=COR_TEXTO_SEC, labelsize=8)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))

# Função de fallback para o caso de dados ainda não estarem prontos
def desenhar_subplot_carregando(ax, moeda_id):
    ax.set_facecolor(COR_FUNDO)
    ax.text(0.5, 0.5, 'Carregando...', transform=ax.transAxes, 
            ha='center', va='center', fontproperties=fonte_variacao, color=COR_TEXTO_SEC)
    ax.set_title(moeda_id.upper(), fontproperties=fonte_titulo_moeda, color=COR_TEXTO_PRI, loc='left', pad=10)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_edgecolor('none')

# --- INÍCIO DO PROGRAMA PRINCIPAL ---
fig = plt.figure(figsize=(16, 9), facecolor=COR_FUNDO)
gs = gridspec.GridSpec(5, 5, figure=fig, hspace=0.5, wspace=0.4)
fig.suptitle('Painel de Criptomoedas', fontproperties=fonte_titulo_painel, color=COR_TEXTO_PRI)
ax1, ax2, ax3, ax4 = fig.add_subplot(gs[0:2, 0:2]), fig.add_subplot(gs[0:2, 3:5]), fig.add_subplot(gs[3:5, 0:2]), fig.add_subplot(gs[3:5, 3:5])
ax_relogio = fig.add_subplot(gs[2, 2])
ani = FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)
plt.show()

print("\nJanela do gráfico fechada. Script finalizado.")
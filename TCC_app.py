# Arquivo: TCC_App.py (Versão 13.7 - Carregamento Progressivo)

# Força o uso de um "motor gráfico" (backend) estável
import matplotlib
matplotlib.use('TkAgg')

# --- Bloco para corrigir o embaçado (DPI Awareness) ---
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Aviso: Não foi possível definir a ciência de DPI: {e}")
# --- Fim do Bloco ---

import requests
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import time
import csv
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.font_manager import FontProperties
import matplotlib.gridspec as gridspec
import os
import sys
import threading

try:
    import mplfinance as mpf
except ImportError:
    print("ERRO: Biblioteca 'mplfinance' não encontrada. Instale com: pip install mplfinance")
    exit()

# --- SEÇÃO DE ESTILO E FONTES (GLOBAL) ---
COR_FUNDO = '#131722'
COR_TEXTO_PRI = '#FFFFFF'
COR_TEXTO_SEC = '#B2B5BE'
COR_GRID = '#2A2E39'
COR_VERDE = '#26A69A'
COR_VERMELHO = '#EF5350'
plt.rcParams['toolbar'] = 'none'

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funcionando em dev e no PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

try:
    caminho_fonte = resource_path('RobotoMono-Regular.ttf')
    fonte_titulo_painel = FontProperties(fname=caminho_fonte, size=20, weight='bold')
    fonte_titulo_moeda = FontProperties(fname=caminho_fonte, size=15, weight='bold')
    fonte_preco = FontProperties(fname=caminho_fonte, size=20, weight='bold')
    fonte_variacao = FontProperties(fname=caminho_fonte, size=12)
    fonte_relogio = FontProperties(fname=caminho_fonte, size=18, weight='bold')
    fonte_erro = FontProperties(fname=caminho_fonte, size=12)
    fonte_metricas = FontProperties(fname=caminho_fonte, size=10)
except FileNotFoundError:
    print("AVISO: Fonte 'RobotoMono-Regular.ttf' não encontrada. Usando fonte padrão.")
    fonte_titulo_painel, fonte_titulo_moeda, fonte_preco, fonte_variacao, fonte_relogio, fonte_erro, fonte_metricas = [None] * 7

ICONE_APP = resource_path('app_icon.png')

try:
    with open('config_dashboard.json', 'r') as f:
        config = json.load(f)
    MOEDAS_PARA_MONITORAR = config.get('moedas')
    CORES_MOEDAS = config.get('cores')
    DIAS_HISTORICO = config.get('dias_historico', 30)
    if not MOEDAS_PARA_MONITORAR or len(MOEDAS_PARA_MONITORAR) != 3:
        raise Exception("Configuração inválida.")
    print(f"Configuração carregada. Monitorando: {MOEDAS_PARA_MONITORAR} | Período: {DIAS_HISTORICO} dias")
except Exception as e:
    print(f"AVISO: {e}. Usando moedas padrão.")
    MOEDAS_PARA_MONITORAR = ["bitcoin", "ethereum", "cardano"]
    CORES_MOEDAS = { "bitcoin": "#F7931A", "ethereum": "#627EEA", "cardano": "#0033AD" }
    DIAS_HISTORICO = 30

INTERVALO_DADOS_SEGUNDOS = 180 
contador_relogio = INTERVALO_DADOS_SEGUNDOS
dados_atuais_cache = {}
dados_ohlc_cache = {}
falha_ohlc_cache = set()
dados_prontos_para_desenhar = False
layout_feito = False 
# --- MUDANÇA 1: Adiciona flag para controlar a busca inicial ---
buscando_dados_worker = False

# =============================================================================
# PARTE 1: LÓGICA DO DASHBOARD
# =============================================================================

def buscar_dados_ohlc(moeda_id, dias):
    url = f"https://api.coingecko.com/api/v3/coins/{moeda_id}/ohlc?vs_currency=brl&days={dias}"
    try:
        print(f"Buscando histórico (OHLC) de {dias} dias para '{moeda_id}'...")
        resposta = requests.get(url, timeout=10); resposta.raise_for_status(); dados = resposta.json()
        df = pd.DataFrame(dados, columns=['time', 'open', 'high', 'low', 'close']); df['time'] = pd.to_datetime(df['time'], unit='ms'); df.set_index('time', inplace=True)
        falha_ohlc_cache.discard(moeda_id)
        return df
    except Exception as e:
        print(f"\033[91m   ERRO ao buscar OHLC para '{moeda_id}': {e}\033[0m")
        falha_ohlc_cache.add(moeda_id)
        return None

def buscar_dados_mercado(lista_de_moedas):
    ids = ",".join(lista_de_moedas)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&ids={ids}&order=market_cap_desc"
    try:
        print("Buscando dados de mercado atuais...")
        resposta = requests.get(url, timeout=10); resposta.raise_for_status()
        return {m['id']: m for m in resposta.json()}
    except Exception as e: print(f"\033[91mERRO ao conectar na API: {e}\033[0m"); return None

# --- MUDANÇA 2: Worker de CARREGAMENTO PROGRESSIVO ---
def worker_buscar_dados():
    global dados_atuais_cache, dados_ohlc_cache, dados_prontos_para_desenhar, buscando_dados_worker
    
    # Se já houver um worker rodando, não inicia outro.
    if buscando_dados_worker:
        print("(THREAD) Worker já está em execução. Nova busca ignorada.")
        return
        
    buscando_dados_worker = True
    print("\n" + "="*50 + "\n(THREAD) Iniciando busca de dados em segundo plano...\n" + "="*50)
    
    # 1. Busca os dados de mercado (preços, variação)
    novos_dados_atuais = buscar_dados_mercado(MOEDAS_PARA_MONITORAR)
    if novos_dados_atuais:
        dados_atuais_cache = novos_dados_atuais
        # SINALIZA para o relógio redesenhar (ainda sem gráfico)
        dados_prontos_para_desenhar = True
        
        print("(THREAD) Pausa de 10s após busca de mercado...")
        time.sleep(10.0) 
        
        # 2. Busca o histórico (OHLC) UMA MOEDA DE CADA VEZ
        novos_dados_ohlc = {}
        for i, moeda_id in enumerate(MOEDAS_PARA_MONITORAR):
            # Busca o histórico da moeda
            ohlc_data = buscar_dados_ohlc(moeda_id, dias=DIAS_HISTORICO)
            
            if ohlc_data is not None:
                # Adiciona ao cache e sinaliza para redesenhar
                dados_ohlc_cache[moeda_id] = ohlc_data
                dados_prontos_para_desenhar = True
                print(f"(THREAD) Dados de '{moeda_id}' carregados e prontos para desenhar.")
            
            # Pausa ANTES de buscar a próxima moeda (se não for a última)
            if i < len(MOEDAS_PARA_MONITORAR) - 1:
                print(f"(THREAD) Pausa de 15s antes de buscar a próxima moeda...")
                time.sleep(15.0) 
            
    print("(THREAD) Busca de dados em segundo plano concluída.")
    buscando_dados_worker = False
# --- Fim da Mudança 2 ---

def animate_dados(i):
    global contador_relogio
    print("Disparando thread de busca de dados...")
    thread = threading.Thread(target=worker_buscar_dados, daemon=True)
    thread.start()
    contador_relogio = INTERVALO_DADOS_SEGUNDOS

def animate_relogio(i):
    global contador_relogio, dados_prontos_para_desenhar, layout_feito

    # --- Bloco para corrigir o layout UMA VEZ ---
    if not layout_feito:
        try:
            print("Ajustando layout...")
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            layout_feito = True
        except Exception as e:
            print(f"Erro ao ajustar layout: {e}")
    # --- Fim do Bloco ---

    ax_relogio.clear(); ax_relogio.set_facecolor(COR_FUNDO)
    minutos, segundos = divmod(contador_relogio, 60)
    texto_relogio = f"{minutos:02d}:{segundos:02d}"
    progresso = contador_relogio / INTERVALO_DADOS_SEGUNDOS
    ax_relogio.pie([1], radius=1.0, colors=[COR_GRID], startangle=90)
    ax_relogio.pie([progresso, 1 - progresso], radius=1.0, colors=[COR_TEXTO_PRI, 'none'], startangle=90)
    ax_relogio.pie([1], radius=0.8, colors=[COR_FUNDO], startangle=90)
    ax_relogio.text(0, 0, texto_relogio, ha='center', va='center', fontproperties=fonte_relogio, color=COR_TEXTO_PRI)
    ax_relogio.set(aspect="equal"); [spine.set_edgecolor('none') for spine in ax_relogio.spines.values()]
    
    if contador_relogio > 0:
        contador_relogio -= 1
        
    # --- MUDANÇA 3: Redesenha e reseta a flag ---
    # Se o worker sinalizou que há dados novos (de 1 ou todas as moedas)
    if dados_prontos_para_desenhar:
        print("Dados novos recebidos! Redesenhando gráficos...")
        atualizar_plots_moedas()
        # Reseta a flag para que o redesenho só ocorra quando o worker mandar
        dados_prontos_para_desenhar = False
    # --- Fim da Mudança 3 ---

def atualizar_plots_moedas():
    # Esta função agora é chamada progressivamente.
    # Ela vai desenhar o que TIVER no cache.
    
    for ax, moeda_id in zip([ax1, ax2, ax3], MOEDAS_PARA_MONITORAR):
        ax.clear()
        
        dados_ohlc = dados_ohlc_cache.get(moeda_id)
        dados_api = dados_atuais_cache.get(moeda_id)

        # Se TEM o OHLC e TEM os dados de mercado...
        if dados_ohlc is not None and dados_api is not None:
            preco_atual = dados_api.get('current_price', 0)
            variacao_24h = dados_api.get('price_change_percentage_24h', 0)
            high_24h = dados_api.get('high_24h', 0)
            low_24h = dados_api.get('low_24h', 0)
            total_volume = dados_api.get('total_volume', 0)
            desenhar_subplot_moeda(ax, moeda_id, preco_atual, variacao_24h, dados_ohlc, high_24h, low_24h, total_volume)
        
        # Se NÃO TEM o OHLC (mas pode já ter o de mercado)...
        elif dados_ohlc is None:
            # Verifica se já tentou e falhou
            if moeda_id in falha_ohlc_cache:
                desenhar_subplot_feedback(ax, moeda_id, "Falha na API (OHLC)")
            else:
                # Se não falhou, ainda está carregando
                desenhar_subplot_feedback(ax, moeda_id, "Carregando...")
        
        # Se não tem NADA (primeiro carregamento)
        else:
             desenhar_subplot_feedback(ax, moeda_id, "Carregando...")


def desenhar_subplot_moeda(ax, moeda_id, preco_atual, variacao_24h, dados_ohlc, high_24h, low_24h, total_volume):
    cor = CORES_MOEDAS.get(moeda_id, COR_TEXTO_PRI)
    cor_variacao = COR_VERDE if variacao_24h >= 0 else COR_VERMELHO
    mc = mpf.make_marketcolors(up=COR_VERDE, down=COR_VERMELHO, inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, facecolor=COR_FUNDO)
    
    mpf.plot(dados_ohlc, type='candle', ax=ax, style=s)
    ax.axhline(preco_atual, color=cor, linestyle='--', linewidth=1, alpha=0.8)
    
    # --- Bloco de Título e Preço (Esquerda) ---
    ax.set_title(moeda_id.upper(), fontproperties=fonte_titulo_moeda, color=COR_TEXTO_PRI, loc='left', pad=10)
    ax.text(0.05, 0.85, f"R$ {preco_atual:,.2f}", transform=ax.transAxes, ha='left', va='top', fontproperties=fonte_preco, color=cor)
    
    # --- Bloco de Variação (Direita) ---
    # (Este bloco fica sozinho na direita, bem no topo)
    ax.text(0.95, 0.95, f"{variacao_24h:+.2f}%", transform=ax.transAxes, ha='right', va='top', fontproperties=fonte_variacao, color=cor_variacao)
    
    # --- Bloco de Métricas (Esquerda-Inferior) ---
    # Formata o volume
    if total_volume > 1_000_000_000:
        vol_formatado = f"R$ {total_volume / 1_000_000_000:.1f}B"
    else:
        vol_formatado = f"R$ {total_volume / 1_000_000:.1f}M"
        
    # Texto das métricas
    texto_metricas = f"Máx 24h: R$ {high_24h:,.2f}\n" \
                     f"Mín 24h: R$ {low_24h:,.2f}\n" \
                     f"Vol 24h: {vol_formatado}"
    
    # Define a posição Y abaixo do preço (Preço está em 0.85)
    y_pos_esquerda = 0.70 
    
    # Adiciona o texto no lado esquerdo
    ax.text(0.05, y_pos_esquerda, texto_metricas, transform=ax.transAxes, ha='left', va='top', 
            fontproperties=fonte_metricas, color=COR_TEXTO_SEC, linespacing=1.5)
    
    ax.set_ylabel(''); ax.set_xlabel('')
    ax.tick_params(axis='y', colors=COR_TEXTO_SEC, labelsize=8); ax.tick_params(axis='x', colors=COR_TEXTO_SEC, labelsize=8)
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))

def desenhar_subplot_feedback(ax, moeda_id, mensagem):
    ax.set_facecolor(COR_FUNDO)
    ax.set_title(moeda_id.upper(), fontproperties=fonte_titulo_moeda, color=COR_TEXTO_PRI, loc='left', pad=10)
    ax.set_xticks([]); ax.set_yticks([]); [spine.set_edgecolor('none') for spine in ax.spines.values()]
    cor_msg = COR_VERMELHO if "Falha" in mensagem else COR_TEXTO_SEC
    ax.text(0.5, 0.5, mensagem, transform=ax.transAxes, ha='center', va='center', fontproperties=fonte_erro, color=cor_msg)

def iniciar_painel_principal(moedas_selecionadas, cores_selecionadas, dias_historico):
    global MOEDAS_PARA_MONITORAR, CORES_MOEDAS, DIAS_HISTORICO, fig, ax1, ax2, ax3, ax_relogio, layout_feito
    MOEDAS_PARA_MONITORAR = moedas_selecionadas
    CORES_MOEDAS = cores_selecionadas
    DIAS_HISTORICO = dias_historico
    layout_feito = False 
    
    fig = plt.figure(figsize=(20, 8), facecolor=COR_FUNDO) 
    
    fig.canvas.manager.set_window_title('Painel de Criptomoedas TCC - Leonardo Pinheiro')
    
    try:
        manager = plt.get_current_fig_manager()
        # Inicia em janela normal
        img = tk.PhotoImage(file=ICONE_APP)
        manager.window.icon_img = img
        manager.window.iconphoto(True, img)
    except Exception as e:
        print(f"Aviso: Não foi possível definir o ícone da janela do gráfico: {e}")
    
    gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[4, 1], hspace=0.15, wspace=0.2)
    
    titulo_painel = f'Painel de Criptomoedas (Histórico de {dias_historico} dias)'
    fig.suptitle(titulo_painel, fontproperties=fonte_titulo_painel, color=COR_TEXTO_PRI)
    
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1]); ax3 = fig.add_subplot(gs[0, 2])
    ax_relogio = fig.add_subplot(gs[1, 1])
    
    atualizar_plots_moedas()
    fig.canvas.draw_idle() 
    
    ani_dados_loop = FuncAnimation(fig, animate_dados, interval=INTERVALO_DADOS_SEGUNDOS * 1000, cache_frame_data=False)
    ani_relogio_loop = FuncAnimation(fig, animate_relogio, interval=1000, cache_frame_data=False)
    
    animate_dados(0) 
    
    plt.show()
    print("\nJanela do gráfico fechada. Script finalizado.")

# =============================================================================
# PARTE 2: LÓGICA DO LAUNCHER (Com seletor de período)
# =============================================================================

def buscar_top_moedas(limite=20):
    print(f"Buscando as {limite} moedas mais populares...")
    url_api = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&order=market_cap_desc&per_page={limite}&page=1"
    try:
        resposta = requests.get(url_api, timeout=10); resposta.raise_for_status()
        return resposta.json()
    except Exception as e: messagebox.showerror("Erro de API", f"Não foi possível buscar a lista de moedas: {e}"); return None

def iniciar_dashboard_clique(listbox, combo_periodo, moedas_disponiveis, root):
    indices_selecionados = listbox.curselection()
    moedas_selecionadas_obj = [moedas_disponiveis[i] for i in indices_selecionados]
    
    if len(moedas_selecionadas_obj) != 3:
        messagebox.showwarning("Seleção Inválida", "Você deve selecionar exatamente 3 moedas."); return

    ids_finais = [moeda['id'] for moeda in moedas_selecionadas_obj]
    cores_finais = { ids_finais[0]: "#F7931A", ids_finais[1]: "#627EEA", ids_finais[2]: "#26A69A" }
    
    periodo_str = combo_periodo.get()
    periodo_map = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}
    dias_historico = periodo_map.get(periodo_str, 30)
    
    print(f"Configuração salva. Monitorando: {ids_finais} | Período: {dias_historico} dias")
    root.destroy()
    iniciar_painel_principal(ids_finais, cores_finais, dias_historico)

def atualizar_estado_botao(event, listbox, botao_iniciar):
    try:
        contagem = len(listbox.curselection())
        
        if contagem == 3:
            botao_iniciar.config(state='normal', text="Iniciar Dashboard")
            botao_iniciar.config(style="Accent.TButton") 
        else:
            botao_iniciar.config(state='disabled') 
            botao_iniciar.config(style="TButton") 

            if contagem > 3:
                botao_iniciar.config(text="Selecione apenas 3 moedas")
            else: 
                botao_iniciar.config(text="Selecione 3 moedas")
                
    except tk.TclError:
        pass

def criar_janela_selecao():
    moedas_disponiveis = buscar_top_moedas()
    if not moedas_disponiveis: return

    root = tk.Tk()
    root.title("Configurar Painel de Criptomoedas")
    root.geometry("450x600")

    try:
        img = tk.PhotoImage(file=ICONE_APP)
        root.icon_img = img 
        root.iconphoto(True, img)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar 'app_icon.png': {e}")
    
    try: sv_ttk.set_theme("dark")
    except Exception: print("Biblioteca sv_ttk não encontrada. Usando tema padrão.")
    
    style = ttk.Style()
    style.configure("TLabel", font=("Consolas", 10))
    style.configure("Header.TLabel", font=("Consolas", 16, "bold"))
    style.configure("TButton", font=("Consolas", 11, "bold"))
    style.configure("TCombobox", font=("Consolas", 10))
    style.configure("Accent.TButton", font=("Consolas", 11, "bold"))


    frame_titulo = ttk.Frame(root, padding="20 20 20 10")
    frame_titulo.pack(fill='x')
    titulo = ttk.Label(frame_titulo, text="Selecione 3 Moedas", style="Header.TLabel")
    titulo.pack()

    frame_lista = ttk.Frame(root, padding="10 10 10 10")
    frame_lista.pack(fill='both', expand=True)

    listbox = tk.Listbox(frame_lista, selectmode='multiple', font=("Consolas", 12), height=12,
                         borderwidth=0, highlightthickness=0, bg=COR_FUNDO,
                         fg=COR_TEXTO_PRI, selectbackground="#007ACC", selectforeground="white")
    listbox.pack(side='left', fill='both', expand=True)

    for moeda in moedas_disponiveis:
        listbox.insert('end', f"   {moeda['name']} ({moeda['symbol'].upper()})")

    frame_controles = ttk.Frame(root, padding="20 10 20 20")
    frame_controles.pack(fill='x')
    
    ttk.Separator(frame_controles, orient='horizontal').pack(fill='x', pady=5)

    label_periodo = ttk.Label(frame_controles, text="Selecione o Período do Histórico:")
    label_periodo.pack(fill='x', pady=(10, 5))
    
    combo_periodo = ttk.Combobox(frame_controles, values=["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"], state="readonly", font=("Consolas", 11))
    combo_periodo.current(1)
    combo_periodo.pack(fill='x')

    botao_iniciar = ttk.Button(frame_controles, text="Selecione 3 moedas", 
                              command=lambda: iniciar_dashboard_clique(listbox, combo_periodo, moedas_disponiveis, root), 
                              style="TButton",
                              state='disabled')
    botao_iniciar.pack(fill='x', ipady=15, pady=(20, 0))
    
    listbox.bind('<<ListboxSelect>>', lambda e: atualizar_estado_botao(e, listbox, botao_iniciar))
    
    root.mainloop()

if __name__ == "__main__":
    criar_janela_selecao()
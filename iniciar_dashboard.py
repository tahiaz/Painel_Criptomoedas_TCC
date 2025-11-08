# Arquivo: iniciar_dashboard.py (Versão 2.1 - Correção do Tema)

import requests
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk # MUDANÇA 1: Corrigido o nome do import

def buscar_top_moedas(limite=20):
    """Busca as X moedas mais populares na CoinGecko."""
    print(f"Buscando as {limite} moedas mais populares...")
    url_api = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&order=market_cap_desc&per_page={limite}&page=1"
    try:
        resposta = requests.get(url_api, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        messagebox.showerror("Erro de API", f"Não foi possível buscar a lista de moedas: {e}")
        return None

def iniciar_dashboard(moedas_selecionadas, root):
    """Salva a configuração e inicia o script principal do dashboard."""
    
    if len(moedas_selecionadas) != 4:
        messagebox.showwarning("Seleção Inválida", "Você deve selecionar exatamente 4 moedas.")
        return

    ids_finais = [moeda['id'] for moeda in moedas_selecionadas]
    
    config = {
        'moedas': ids_finais,
        'cores': {
            ids_finais[0]: "#F7931A", ids_finais[1]: "#627EEA",
            ids_finais[2]: "#26A69A", ids_finais[3]: "#9945FF"
        }
    }
    
    with open('config_dashboard.json', 'w') as f:
        json.dump(config, f)
        
    print(f"Configuração salva. Monitorando: {ids_finais}")
    print("Iniciando o dashboard...")
    
    root.withdraw() 
    
    try:
        subprocess.run(['py', 'dashboard_dinamico.py'], check=True)
    except Exception as e:
        messagebox.showerror("Erro ao Iniciar", f"Não foi possível iniciar o 'dashboard_dinamico.py': {e}")
    
    root.destroy()

def criar_janela_selecao():
    moedas_disponiveis = buscar_top_moedas()
    if not moedas_disponiveis:
        return

    root = tk.Tk()
    root.title("Configurar Painel de Criptomoedas")
    root.geometry("450x550")
    
    # --- MUDANÇA 2: Corrigido o nome da função que aplica o tema ---
    sv_ttk.set_theme("dark")
    # -----------------------------------------------------------
    
    style = ttk.Style()
    style.configure("TLabel", font=("Roboto Mono", 11))
    style.configure("Header.TLabel", font=("Roboto Mono", 16, "bold"))
    style.configure("TButton", font=("Roboto Mono", 10, "bold"))

    frame_titulo = ttk.Frame(root, padding="20")
    frame_titulo.pack(fill='x')
    
    titulo = ttk.Label(frame_titulo, text="Selecione 4 Moedas", style="Header.TLabel")
    titulo.pack()
    
    instrucao = ttk.Label(frame_titulo, text="Segure 'Ctrl' para selecionar múltiplas moedas.")
    instrucao.pack(pady=5)

    frame_lista = ttk.Frame(root, padding="10 0 10 20")
    frame_lista.pack(fill='both', expand=True)

    listbox = tk.Listbox(frame_lista, selectmode='multiple', font=("Roboto Mono", 12), height=len(moedas_disponiveis),
                         bg="#2D2D2D", fg="white", selectbackground="#0078D7", borderwidth=0, highlightthickness=0)
    
    scrollbar = ttk.Scrollbar(frame_lista, orient='vertical', command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side='right', fill='y')
    listbox.pack(side='left', fill='both', expand=True)

    for moeda in moedas_disponiveis:
        listbox.insert('end', f" {moeda['name']} ({moeda['symbol'].upper()})")

    frame_botao = ttk.Frame(root, padding="20")
    frame_botao.pack(fill='x')

    def ao_clicar_iniciar():
        indices_selecionados = listbox.curselection()
        moedas_selecionadas = [moedas_disponiveis[i] for i in indices_selecionados]
        iniciar_dashboard(moedas_selecionadas, root)

    botao_iniciar = ttk.Button(frame_botao, text="Iniciar Dashboard", command=ao_clicar_iniciar, style="Accent.TButton")
    botao_iniciar.pack(fill='x', ipady=10)

    root.mainloop()

if __name__ == "__main__":
    criar_janela_selecao()
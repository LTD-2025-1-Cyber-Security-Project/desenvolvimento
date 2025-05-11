#!/usr/bin/env python3
"""
Versão simplificada do aplicativo NexusInfo para teste rápido.
Este arquivo implementa uma versão básica da interface para verificar se
as dependências estão instaladas corretamente.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage

# Tentar importar ttkbootstrap
try:
    import ttkbootstrap as ttkb
    USING_TTKBOOTSTRAP = True
    print("ttkbootstrap encontrado e será utilizado")
except ImportError:
    USING_TTKBOOTSTRAP = False
    print("ttkbootstrap não encontrado, usando ttk padrão")
    print("Para instalar: pip install ttkbootstrap")

# Tentar importar API Gemini
try:
    # Tentar o novo SDK
    from google import genai
    USING_GENAI = "new"
    print("SDK Google GenAI (novo) encontrado")
except ImportError:
    try:
        # Tentar o SDK antigo
        import google.generativeai as genai
        USING_GENAI = "old"
        print("SDK Google GenerativeAI (antigo) encontrado")
    except ImportError:
        USING_GENAI = None
        print("SDK do Google GenAI não encontrado")
        print("Para instalar: pip install google-genai")

class SimpleApp:
    """Aplicação simplificada para teste"""
    
    def __init__(self, root):
        """Inicializa a aplicação"""
        self.root = root
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        if USING_TTKBOOTSTRAP:
            main_frame = ttk.Frame(self.root, padding=20)
        else:
            main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="NexusInfo - Teste de Componentes", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Status das dependências
        deps_frame = ttk.LabelFrame(main_frame, text="Status das Dependências")
        deps_frame.pack(fill="x", padx=5, pady=5)
        
        # Cores para status - verde e vermelho são seguros em todas as versões do ttk
        success_style = {"foreground": "green"}
        error_style = {"foreground": "red"}
        
        # ttkbootstrap
        ttk_status = ttk.Label(
            deps_frame, 
            text=f"ttkbootstrap: {'Instalado' if USING_TTKBOOTSTRAP else 'Não encontrado'}", 
            **success_style if USING_TTKBOOTSTRAP else error_style
        )
        ttk_status.pack(anchor="w", padx=10, pady=5)
        
        # Gemini API
        gemini_status = ttk.Label(
            deps_frame, 
            text=f"API Gemini: {'SDK Novo' if USING_GENAI == 'new' else 'SDK Antigo' if USING_GENAI == 'old' else 'Não encontrado'}", 
            **success_style if USING_GENAI else error_style
        )
        gemini_status.pack(anchor="w", padx=10, pady=5)
        
        # Pillow
        try:
            from PIL import Image
            pillow_installed = True
        except ImportError:
            pillow_installed = False
        
        pillow_status = ttk.Label(
            deps_frame, 
            text=f"Pillow: {'Instalado' if pillow_installed else 'Não encontrado'}", 
            **success_style if pillow_installed else error_style
        )
        pillow_status.pack(anchor="w", padx=10, pady=5)
        
        # API Key
        api_key = os.getenv("GOOGLE_API_KEY")
        api_status = ttk.Label(
            deps_frame, 
            text=f"API Key: {'Configurada' if api_key else 'Não configurada'}", 
            **success_style if api_key else error_style
        )
        api_status.pack(anchor="w", padx=10, pady=5)
        
        # Sistema de temas
        themes_frame = ttk.LabelFrame(main_frame, text="Teste de Temas")
        themes_frame.pack(fill="x", padx=5, pady=15)
        
        themes_text = "Temas disponíveis:"
        
        if USING_TTKBOOTSTRAP:
            styles = ttkb.Style()
            available_themes = styles.theme_names()
            themes_text += f"\n{', '.join(available_themes)}"
            
            # Combobox para selecionar tema
            theme_var = tk.StringVar()
            theme_combobox = ttk.Combobox(
                themes_frame, 
                textvariable=theme_var,
                values=available_themes
            )
            theme_combobox.current(available_themes.index(styles.theme.name))
            theme_combobox.pack(padx=10, pady=10)
            
            # Botão para aplicar tema
            apply_button = ttk.Button(
                themes_frame, 
                text="Aplicar Tema", 
                command=lambda: styles.theme_use(theme_var.get())
            )
            apply_button.pack(padx=10, pady=10)
        else:
            style = ttk.Style()
            available_themes = style.theme_names()
            themes_text += f"\n{', '.join(available_themes)}"
            
            # Combobox para selecionar tema
            theme_var = tk.StringVar()
            theme_combobox = ttk.Combobox(
                themes_frame, 
                textvariable=theme_var,
                values=available_themes
            )
            theme_combobox.current(available_themes.index(style.theme_use()))
            theme_combobox.pack(padx=10, pady=10)
            
            # Botão para aplicar tema
            apply_button = ttk.Button(
                themes_frame, 
                text="Aplicar Tema",
                command=lambda: style.theme_use(theme_var.get())
            )
            apply_button.pack(padx=10, pady=10)
        
        themes_label = ttk.Label(themes_frame, text=themes_text)
        themes_label.pack(anchor="w", padx=10, pady=5)
        
        # Teste da API Gemini
        gemini_frame = ttk.LabelFrame(main_frame, text="Teste da API Gemini")
        gemini_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Se a API não estiver configurada, mostrar mensagem
        if not USING_GENAI:
            gemini_msg = ttk.Label(
                gemini_frame, 
                text="SDK da API Gemini não encontrado.\nInstale com: pip install google-genai", 
                **error_style
            )
            gemini_msg.pack(padx=10, pady=20)
            
            return  # Não mostrar mais nada
        
        # Se a API key não estiver configurada, mostrar campo para inserir
        if not api_key:
            api_key_frame = ttk.Frame(gemini_frame)
            api_key_frame.pack(fill="x", padx=10, pady=10)
            
            api_key_label = ttk.Label(api_key_frame, text="API Key:")
            api_key_label.pack(side="left", padx=(0, 5))
            
            api_key_var = tk.StringVar()
            api_key_entry = ttk.Entry(api_key_frame, textvariable=api_key_var, width=40)
            api_key_entry.pack(side="left", padx=5)
            
            set_key_button = ttk.Button(
                api_key_frame, 
                text="Definir API Key",
                command=lambda: self.set_api_key(api_key_var.get())
            )
            set_key_button.pack(side="left", padx=5)
        
        # Campo para teste de consulta
        query_frame = ttk.Frame(gemini_frame)
        query_frame.pack(fill="x", padx=10, pady=10)
        
        query_label = ttk.Label(query_frame, text="Consulta:")
        query_label.pack(side="left", padx=(0, 5))
        
        query_var = tk.StringVar(value="Quais são as últimas notícias sobre inteligência artificial?")
        query_entry = ttk.Entry(query_frame, textvariable=query_var, width=50)
        query_entry.pack(side="left", padx=5)
        
        query_button = ttk.Button(
            query_frame, 
            text="Consultar",
            command=lambda: self.test_gemini_query(query_var.get())
        )
        query_button.pack(side="left", padx=5)
        
        # Área para mostrar resposta
        if USING_TTKBOOTSTRAP:
            self.response_text = tk.Text(gemini_frame, height=10, wrap="word")
        else:
            self.response_text = tk.Text(gemini_frame, height=10, wrap="word")
        self.response_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Mensagem inicial
        self.response_text.insert("1.0", "Clique em 'Consultar' para testar a API Gemini.\n\n")
        self.response_text.insert("end", "A resposta será exibida aqui.")
    
    def set_api_key(self, api_key):
        """Define a API key para uso"""
        if not api_key:
            messagebox.showerror("Erro", "Por favor, insira uma API key válida.")
            return
        
        # Definir no ambiente
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Reiniciar a aplicação
        messagebox.showinfo(
            "API Key Configurada", 
            "A API key foi configurada. A aplicação será reiniciada."
        )
        
        # Reiniciar
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def test_gemini_query(self, query):
        """Testa uma consulta na API Gemini"""
        if not query:
            messagebox.showerror("Erro", "Por favor, insira uma consulta.")
            return
        
        # Limpar área de resposta
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", "Consultando API Gemini...\n\n")
        self.root.update()
        
        try:
            # Configurar API
            api_key = os.environ.get("GOOGLE_API_KEY")
            
            if USING_GENAI == "new":
                # Usar o novo SDK
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=query,
                )
                
                # Extrair texto da resposta
                response_text = ""
                for part in response.candidates[0].content.parts:
                    response_text += part.text
                    
            elif USING_GENAI == "old":
                # Usar o SDK antigo
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content(query)
                response_text = response.text
            
            # Exibir resposta
            self.response_text.delete("1.0", "end")
            self.response_text.insert("1.0", f"Consulta: {query}\n\n")
            self.response_text.insert("end", response_text)
            
        except Exception as e:
            # Limpar e mostrar erro
            self.response_text.delete("1.0", "end")
            self.response_text.insert("1.0", f"Erro ao consultar API Gemini: {str(e)}\n\n")
            self.response_text.insert("end", "Verifique sua API key e conexão com a internet.")

def main():
    """Função principal"""
    # Configurar janela
    if USING_TTKBOOTSTRAP:
        # Use a função de janela normal, não o Window personalizado
        root = tk.Tk()
        style = ttkb.Style(theme="darkly")
    else:
        root = tk.Tk()
        style = ttk.Style()
        
    root.title("NexusInfo - Teste")
    root.geometry("800x600+100+50")
    root.minsize(700, 500)
    
    # Inicializar app
    app = SimpleApp(root)
    
    # Iniciar loop
    root.mainloop()

if __name__ == "__main__":
    main()
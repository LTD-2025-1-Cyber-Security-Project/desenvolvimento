#!/usr/bin/env python3
"""
NexusInfo - Sistema de Notícias com IA

Aplicação desktop de notícias com interface gráfica moderna e sistema 
de busca de notícias usando IA Gemini com autenticação de usuários.

Funcionalidades principais:
- Interface gráfica moderna usando Tkinter e ttkbootstrap
- Autenticação de usuários (login, registro, recuperação de senha)
- Busca de notícias com IA Gemini
- Categorias específicas: Tecnologia, Cibersegurança, IA, IoT
- Salvamento e gerenciamento de notícias por usuário
"""

import os
import sys
import json
import sqlite3
import hashlib
import uuid
import datetime
import threading
import webbrowser
import tempfile
from pathlib import Path
from functools import partial
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage, simpledialog

# Importar ttkbootstrap para interface moderna
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledText
    from ttkbootstrap.toast import ToastNotification
    USING_TTKBOOTSTRAP = True
except ImportError:
    from tkinter import scrolledtext as ScrolledText
    USING_TTKBOOTSTRAP = False
    print("Aviso: ttkbootstrap não encontrado. Usando ttk padrão.")
    print("Instale ttkbootstrap com: pip install ttkbootstrap")

# Importar módulo de IA
from gemini_service import GeminiNewsService

# Importar módulos personalizados
from database_manager import DatabaseManager
from auth_manager import AuthManager, User

# Configuração de diretórios
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = DATA_DIR / "users"

# Garantir que os diretórios existam
DATA_DIR.mkdir(exist_ok=True)
USER_DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

class NexusInfoApp:
    """Classe principal da aplicação NexusInfo"""
    
    def __init__(self, root):
        """Inicializa a aplicação"""
        self.root = root
        self.current_user = None
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager(self.db_manager)
        self.gemini_service = GeminiNewsService()
        
        # Configurar janela principal
        self.setup_window()
        
        # Inicializar UI
        self.initialize_ui()
        
        # Começar com a tela de login
        self.show_login_screen()
    
    def setup_window(self):
        """Configura a janela principal da aplicação"""
        self.root.title("NexusInfo - Sistema de Notícias com IA")
        
        # Define o tamanho da janela para 80% do tamanho da tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Centraliza a janela
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.root.minsize(800, 600)
        
        # Configurar ícone se disponível
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self.root.iconphoto(True, PhotoImage(file=str(icon_path)))
        
        # Configurar tema
        if USING_TTKBOOTSTRAP:
            # O tema já está configurado pelo ttkbootstrap
            pass
        else:
            # Usar tema padrão ttk
            ttk_style = ttk.Style()
            ttk_style.theme_use("clam")  # Usar um tema mais moderno do ttk
    
    def initialize_ui(self):
        """Inicializa os elementos da interface principal"""
        # Container para alternar entre frames
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        # Criar todos os frames de tela, mas não mostrá-los ainda
        self.setup_login_frame()
        self.setup_register_frame()
        self.setup_dashboard_frame()
        
        # Preparar o menu principal (será mostrado após login)
        self.create_main_menu()
    
    def setup_login_frame(self):
        """Configura o frame de login"""
        if USING_TTKBOOTSTRAP:
            self.login_frame = ttkb.Frame(self.main_container, bootstyle="light")
        else:
            self.login_frame = ttk.Frame(self.main_container)
        
        # Criando widgets para o frame de login com estilo ttkbootstrap
        login_title_frame = ttk.Frame(self.login_frame)
        login_title_frame.pack(pady=(50, 30))
        
        title_font = ("Helvetica", 28, "bold")
        title_label = ttk.Label(login_title_frame, text="NexusInfo", font=title_font)
        title_label.pack()
        
        subtitle_font = ("Helvetica", 12)
        subtitle_label = ttk.Label(login_title_frame, 
                                 text="Sistema Avançado de Notícias com IA", 
                                 font=subtitle_font)
        subtitle_label.pack(pady=(5, 0))
        
        # Frame do formulário de login
        login_form_frame = ttk.Frame(self.login_frame)
        login_form_frame.pack(pady=20)
        
        # Estilos dos campos de login
        field_width = 30
        
        # Username
        username_frame = ttk.Frame(login_form_frame)
        username_frame.pack(pady=10, fill="x")
        
        username_label = ttk.Label(username_frame, text="Usuário:", width=10, anchor="w")
        username_label.pack(side="left", padx=(0, 5))
        
        self.username_entry = ttk.Entry(username_frame, width=field_width)
        self.username_entry.pack(side="left", padx=5)
        
        # Password
        password_frame = ttk.Frame(login_form_frame)
        password_frame.pack(pady=10, fill="x")
        
        password_label = ttk.Label(password_frame, text="Senha:", width=10, anchor="w")
        password_label.pack(side="left", padx=(0, 5))
        
        self.password_entry = ttk.Entry(password_frame, width=field_width, show="*")
        self.password_entry.pack(side="left", padx=5)
        
        # Botões
        buttons_frame = ttk.Frame(login_form_frame)
        buttons_frame.pack(pady=(20, 10))
        
        if USING_TTKBOOTSTRAP:
            login_button = ttkb.Button(
                buttons_frame, 
                text="Entrar", 
                bootstyle="primary",
                command=self.handle_login
            )
        else:
            login_button = ttk.Button(
                buttons_frame, 
                text="Entrar",
                command=self.handle_login
            )
            
        login_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            register_button = ttkb.Button(
                buttons_frame, 
                text="Registrar", 
                bootstyle="secondary outline",
                command=self.show_register_screen
            )
        else:
            register_button = ttk.Button(
                buttons_frame, 
                text="Registrar",
                command=self.show_register_screen
            )
            
        register_button.pack(side="left", padx=10)
        
        # Link para redefinir senha
        forgot_password_frame = ttk.Frame(login_form_frame)
        forgot_password_frame.pack(pady=(5, 0))
        
        forgot_password_label = ttk.Label(
            forgot_password_frame, 
            text="Esqueceu a senha?", 
            cursor="hand2",
            foreground="blue"
        )
        forgot_password_label.pack()
        forgot_password_label.bind("<Button-1>", self.forgot_password)
    
    def setup_register_frame(self):
        """Configura o frame de registro"""
        if USING_TTKBOOTSTRAP:
            self.register_frame = ttkb.Frame(self.main_container, bootstyle="light")
        else:
            self.register_frame = ttk.Frame(self.main_container)
        
        # Título
        register_title_frame = ttk.Frame(self.register_frame)
        register_title_frame.pack(pady=(50, 30))
        
        title_font = ("Helvetica", 24, "bold")
        title_label = ttk.Label(register_title_frame, text="Criar Nova Conta", font=title_font)
        title_label.pack()
        
        # Frame do formulário
        register_form_frame = ttk.Frame(self.register_frame)
        register_form_frame.pack(pady=20)
        
        # Estilos dos campos
        field_width = 30
        
        # Nome completo
        fullname_frame = ttk.Frame(register_form_frame)
        fullname_frame.pack(pady=10, fill="x")
        
        fullname_label = ttk.Label(fullname_frame, text="Nome completo:", width=15, anchor="w")
        fullname_label.pack(side="left", padx=(0, 5))
        
        self.fullname_entry = ttk.Entry(fullname_frame, width=field_width)
        self.fullname_entry.pack(side="left", padx=5)
        
        # Email
        email_frame = ttk.Frame(register_form_frame)
        email_frame.pack(pady=10, fill="x")
        
        email_label = ttk.Label(email_frame, text="Email:", width=15, anchor="w")
        email_label.pack(side="left", padx=(0, 5))
        
        self.email_entry = ttk.Entry(email_frame, width=field_width)
        self.email_entry.pack(side="left", padx=5)
        
        # Username
        reg_username_frame = ttk.Frame(register_form_frame)
        reg_username_frame.pack(pady=10, fill="x")
        
        reg_username_label = ttk.Label(reg_username_frame, text="Usuário:", width=15, anchor="w")
        reg_username_label.pack(side="left", padx=(0, 5))
        
        self.reg_username_entry = ttk.Entry(reg_username_frame, width=field_width)
        self.reg_username_entry.pack(side="left", padx=5)
        
        # Password
        reg_password_frame = ttk.Frame(register_form_frame)
        reg_password_frame.pack(pady=10, fill="x")
        
        reg_password_label = ttk.Label(reg_password_frame, text="Senha:", width=15, anchor="w")
        reg_password_label.pack(side="left", padx=(0, 5))
        
        self.reg_password_entry = ttk.Entry(reg_password_frame, width=field_width, show="*")
        self.reg_password_entry.pack(side="left", padx=5)
        
        # Confirm Password
        confirm_password_frame = ttk.Frame(register_form_frame)
        confirm_password_frame.pack(pady=10, fill="x")
        
        confirm_password_label = ttk.Label(confirm_password_frame, text="Confirmar senha:", width=15, anchor="w")
        confirm_password_label.pack(side="left", padx=(0, 5))
        
        self.confirm_password_entry = ttk.Entry(confirm_password_frame, width=field_width, show="*")
        self.confirm_password_entry.pack(side="left", padx=5)
        
        # Botões
        reg_buttons_frame = ttk.Frame(register_form_frame)
        reg_buttons_frame.pack(pady=(20, 10))
        
        if USING_TTKBOOTSTRAP:
            create_account_button = ttkb.Button(
                reg_buttons_frame, 
                text="Criar Conta", 
                bootstyle="success",
                command=self.handle_register
            )
        else:
            create_account_button = ttk.Button(
                reg_buttons_frame, 
                text="Criar Conta",
                command=self.handle_register
            )
            
        create_account_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            back_to_login_button = ttkb.Button(
                reg_buttons_frame, 
                text="Voltar", 
                bootstyle="secondary outline",
                command=self.show_login_screen
            )
        else:
            back_to_login_button = ttk.Button(
                reg_buttons_frame, 
                text="Voltar",
                command=self.show_login_screen
            )
            
        back_to_login_button.pack(side="left", padx=10)
    
    def setup_dashboard_frame(self):
        """Configura o frame principal do dashboard"""
        if USING_TTKBOOTSTRAP:
            self.dashboard_frame = ttkb.Frame(self.main_container)
        else:
            self.dashboard_frame = ttk.Frame(self.main_container)
        
        # Frame para a barra superior
        self.top_bar_frame = ttk.Frame(self.dashboard_frame)
        self.top_bar_frame.pack(fill="x", pady=5, padx=10)
        
        # Barra de pesquisa
        search_frame = ttk.Frame(self.top_bar_frame)
        search_frame.pack(side="left", fill="x", expand=True)
        
        # Componentes da barra de pesquisa
        self.search_var = tk.StringVar()
        
        if USING_TTKBOOTSTRAP:
            self.search_entry = ttkb.Entry(
                search_frame, 
                textvariable=self.search_var,
                width=40, 
                bootstyle="primary"
            )
        else:
            self.search_entry = ttk.Entry(
                search_frame, 
                textvariable=self.search_var,
                width=40
            )
        
        self.search_entry.pack(side="left", padx=(0, 5))
        
        if USING_TTKBOOTSTRAP:
            search_button = ttkb.Button(
                search_frame, 
                text="Pesquisar", 
                bootstyle="primary",
                command=self.handle_search
            )
        else:
            search_button = ttk.Button(
                search_frame, 
                text="Pesquisar",
                command=self.handle_search
            )
        
        search_button.pack(side="left")
        
        # Frame para informações do usuário
        user_info_frame = ttk.Frame(self.top_bar_frame)
        user_info_frame.pack(side="right", padx=(20, 0))
        
        self.user_label = ttk.Label(user_info_frame, text="Olá, Usuário")
        self.user_label.pack(side="left", padx=(0, 10))
        
        if USING_TTKBOOTSTRAP:
            logout_button = ttkb.Button(
                user_info_frame, 
                text="Sair", 
                bootstyle="danger outline",
                command=self.handle_logout
            )
        else:
            logout_button = ttk.Button(
                user_info_frame, 
                text="Sair",
                command=self.handle_logout
            )
        
        logout_button.pack(side="left")
        
        # Painel principal - usando notebook para as abas
        if USING_TTKBOOTSTRAP:
            self.main_notebook = ttkb.Notebook(self.dashboard_frame)
        else:
            self.main_notebook = ttk.Notebook(self.dashboard_frame)
            
        self.main_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Criar todas as abas
        self.setup_home_tab()
        self.setup_technology_tab()
        self.setup_cybersecurity_tab()
        self.setup_ai_tab()
        self.setup_iot_tab()
        self.setup_saved_news_tab()
        
        # Barra de status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        
        if USING_TTKBOOTSTRAP:
            self.status_bar = ttkb.Label(
                self.dashboard_frame, 
                textvariable=self.status_var, 
                relief="sunken", 
                anchor="w",
                bootstyle="secondary"
            )
        else:
            self.status_bar = ttk.Label(
                self.dashboard_frame, 
                textvariable=self.status_var, 
                relief="sunken", 
                anchor="w"
            )
            
        self.status_bar.pack(side="bottom", fill="x")
    
    def setup_home_tab(self):
        """Configura a aba inicial"""
        if USING_TTKBOOTSTRAP:
            home_frame = ttkb.Frame(self.main_notebook, padding=10)
        else:
            home_frame = ttk.Frame(self.main_notebook, padding=10)
            
        self.main_notebook.add(home_frame, text="Início")
        
        # Título de boas-vindas
        welcome_frame = ttk.Frame(home_frame)
        welcome_frame.pack(fill="x", pady=(0, 20))
        
        title_font = ("Helvetica", 16, "bold")
        welcome_title = ttk.Label(
            welcome_frame, 
            text="Bem-vindo ao NexusInfo - Seu Portal de Notícias com IA", 
            font=title_font
        )
        welcome_title.pack()
        
        # Colunas para os destaques
        highlights_frame = ttk.Frame(home_frame)
        highlights_frame.pack(fill="both", expand=True)
        
        # Configurar colunas com peso igual
        highlights_frame.columnconfigure(0, weight=1)
        highlights_frame.columnconfigure(1, weight=1)
        
        # Frame para notícias recentes
        recent_news_frame = ttk.LabelFrame(highlights_frame, text="Notícias Recentes")
        recent_news_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Listbox para notícias recentes
        if USING_TTKBOOTSTRAP:
            self.recent_news_list = ttkb.Treeview(
                recent_news_frame,
                columns=("title",),
                show="headings",
                height=10
            )
        else:
            self.recent_news_list = ttk.Treeview(
                recent_news_frame,
                columns=("title",),
                show="headings",
                height=10
            )
            
        self.recent_news_list.heading("title", text="Título")
        self.recent_news_list.column("title", width=300)
        self.recent_news_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Associar evento de duplo clique
        self.recent_news_list.bind("<Double-1>", self.open_selected_news)
        
        # Frame para tendências
        trends_frame = ttk.LabelFrame(highlights_frame, text="Tendências")
        trends_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Lista de tendências
        if USING_TTKBOOTSTRAP:
            self.trends_list = ttkb.Treeview(
                trends_frame,
                columns=("topic",),
                show="headings",
                height=10
            )
        else:
            self.trends_list = ttk.Treeview(
                trends_frame,
                columns=("topic",),
                show="headings",
                height=10
            )
            
        self.trends_list.heading("topic", text="Tópico em Alta")
        self.trends_list.column("topic", width=300)
        self.trends_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Associar evento de clique para buscar o tópico
        self.trends_list.bind("<Double-1>", self.search_trend_topic)
        
        # Painel inferior para botões de ação rápida
        quick_actions_frame = ttk.Frame(home_frame)
        quick_actions_frame.pack(fill="x", pady=(20, 0))
        
        # Botões de ação rápida para categorias
        if USING_TTKBOOTSTRAP:
            tech_button = ttkb.Button(
                quick_actions_frame, 
                text="Tecnologia", 
                bootstyle="info",
                command=lambda: self.main_notebook.select(1)
            )
        else:
            tech_button = ttk.Button(
                quick_actions_frame, 
                text="Tecnologia",
                command=lambda: self.main_notebook.select(1)
            )
            
        tech_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            security_button = ttkb.Button(
                quick_actions_frame, 
                text="Cibersegurança", 
                bootstyle="danger",
                command=lambda: self.main_notebook.select(2)
            )
        else:
            security_button = ttk.Button(
                quick_actions_frame, 
                text="Cibersegurança",
                command=lambda: self.main_notebook.select(2)
            )
            
        security_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            ai_button = ttkb.Button(
                quick_actions_frame, 
                text="Inteligência Artificial", 
                bootstyle="success",
                command=lambda: self.main_notebook.select(3)
            )
        else:
            ai_button = ttk.Button(
                quick_actions_frame, 
                text="Inteligência Artificial",
                command=lambda: self.main_notebook.select(3)
            )
            
        ai_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            iot_button = ttkb.Button(
                quick_actions_frame, 
                text="Internet das Coisas", 
                bootstyle="warning",
                command=lambda: self.main_notebook.select(4)
            )
        else:
            iot_button = ttk.Button(
                quick_actions_frame, 
                text="Internet das Coisas",
                command=lambda: self.main_notebook.select(4)
            )
            
        iot_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            saved_button = ttkb.Button(
                quick_actions_frame, 
                text="Minhas Notícias", 
                bootstyle="secondary",
                command=lambda: self.main_notebook.select(5)
            )
        else:
            saved_button = ttk.Button(
                quick_actions_frame, 
                text="Minhas Notícias",
                command=lambda: self.main_notebook.select(5)
            )
            
        saved_button.pack(side="left", padx=5)
        
        # Configurar dados iniciais
        self.populate_home_tab()
    
    def setup_technology_tab(self):
        """Configura a aba de Tecnologia"""
        self.setup_category_tab("Tecnologia", 1, "info")
    
    def setup_cybersecurity_tab(self):
        """Configura a aba de Cibersegurança"""
        self.setup_category_tab("Cibersegurança", 2, "danger")
    
    def setup_ai_tab(self):
        """Configura a aba de Inteligência Artificial"""
        self.setup_category_tab("Inteligência Artificial", 3, "success")
    
    def setup_iot_tab(self):
        """Configura a aba de Internet das Coisas"""
        self.setup_category_tab("Internet das Coisas", 4, "warning")
    
    def setup_category_tab(self, category_name, tab_index, bootstyle):
        """Configura uma aba de categoria genérica"""
        if USING_TTKBOOTSTRAP:
            category_frame = ttkb.Frame(self.main_notebook, padding=10)
        else:
            category_frame = ttk.Frame(self.main_notebook, padding=10)
            
        self.main_notebook.add(category_frame, text=category_name)
        
        # Barra superior com título e ações
        header_frame = ttk.Frame(category_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_font = ("Helvetica", 14, "bold")
        category_title = ttk.Label(header_frame, text=f"Notícias de {category_name}", font=title_font)
        category_title.pack(side="left")
        
        # Botão para buscar notícias da categoria
        if USING_TTKBOOTSTRAP:
            refresh_button = ttkb.Button(
                header_frame, 
                text="Atualizar", 
                bootstyle=f"{bootstyle}",
                command=lambda: self.fetch_category_news(category_name, tab_index)
            )
        else:
            refresh_button = ttk.Button(
                header_frame, 
                text="Atualizar",
                command=lambda: self.fetch_category_news(category_name, tab_index)
            )
            
        refresh_button.pack(side="right")
        
        # Frame principal para o conteúdo
        content_frame = ttk.Frame(category_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Painel de notícias em lista
        news_list_frame = ttk.LabelFrame(content_frame, text="Últimas Notícias")
        news_list_frame.pack(fill="both", expand=True, side="left", padx=(0, 5))
        
        # Lista de notícias
        if USING_TTKBOOTSTRAP:
            news_list = ttkb.Treeview(
                news_list_frame,
                columns=("title", "date"),
                show="headings",
                height=15
            )
        else:
            news_list = ttk.Treeview(
                news_list_frame,
                columns=("title", "date"),
                show="headings",
                height=15
            )
            
        news_list.heading("title", text="Título")
        news_list.heading("date", text="Data")
        news_list.column("title", width=450)
        news_list.column("date", width=150)
        news_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar para a lista
        list_scrollbar = ttk.Scrollbar(news_list_frame, orient="vertical", command=news_list.yview)
        list_scrollbar.pack(side="right", fill="y")
        news_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Armazenar a lista no atributo para atualização posterior
        setattr(self, f"{category_name.lower().replace(' ', '_')}_news_list", news_list)
        
        # Associar evento de duplo clique
        news_list.bind("<Double-1>", lambda e: self.open_category_news(e, category_name))
        
        # Painel lateral para detalhes
        details_frame = ttk.LabelFrame(content_frame, text="Detalhes")
        details_frame.pack(fill="both", expand=True, side="right", padx=(5, 0))
        
        # Área de texto para detalhes
        if USING_TTKBOOTSTRAP:
            details_text = ScrolledText(details_frame, width=40, height=15, bootstyle=bootstyle)
        else:
            details_text = ScrolledText(details_frame, width=40, height=15)
            
        details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar texto inicial
        details_text.insert("1.0", f"Selecione uma notícia na lista para ver os detalhes.\n\n")
        details_text.insert("end", f"Clique em 'Atualizar' para buscar as últimas notícias de {category_name}.")
        details_text.configure(state="disabled")
        
        # Armazenar o widget de texto para atualização posterior
        setattr(self, f"{category_name.lower().replace(' ', '_')}_details_text", details_text)
        
        # Botões de ação
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill="x", pady=5)
        
        if USING_TTKBOOTSTRAP:
            save_button = ttkb.Button(
                action_frame, 
                text="Salvar", 
                bootstyle=f"{bootstyle}",
                command=lambda: self.save_selected_news(category_name)
            )
        else:
            save_button = ttk.Button(
                action_frame, 
                text="Salvar",
                command=lambda: self.save_selected_news(category_action_frame, 
                text="Salvar",
                command=lambda: self.save_selected_news(category_name)
            ))
            
        save_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            share_button = ttkb.Button(
                action_frame, 
                text="Compartilhar", 
                bootstyle=f"{bootstyle} outline",
                command=lambda: self.share_selected_news(category_name)
            )
        else:
            share_button = ttk.Button(
                action_frame, 
                text="Compartilhar",
                command=lambda: self.share_selected_news(category_name)
            )
            
        share_button.pack(side="left", padx=5)
    
    def setup_saved_news_tab(self):
        """Configura a aba de notícias salvas"""
        if USING_TTKBOOTSTRAP:
            saved_frame = ttkb.Frame(self.main_notebook, padding=10)
        else:
            saved_frame = ttk.Frame(self.main_notebook, padding=10)
            
        self.main_notebook.add(saved_frame, text="Minhas Notícias")
        
        # Barra superior com título e ações
        header_frame = ttk.Frame(saved_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_font = ("Helvetica", 14, "bold")
        saved_title = ttk.Label(header_frame, text="Minhas Notícias Salvas", font=title_font)
        saved_title.pack(side="left")
        
        # Botão para atualizar
        if USING_TTKBOOTSTRAP:
            refresh_saved_button = ttkb.Button(
                header_frame, 
                text="Atualizar", 
                bootstyle="secondary",
                command=self.refresh_saved_news
            )
        else:
            refresh_saved_button = ttk.Button(
                header_frame, 
                text="Atualizar",
                command=self.refresh_saved_news
            )
            
        refresh_saved_button.pack(side="right")
        
        # Frame principal para o conteúdo
        saved_content_frame = ttk.Frame(saved_frame)
        saved_content_frame.pack(fill="both", expand=True)
        
        # Configuração de colunas com pesos
        saved_content_frame.columnconfigure(0, weight=3)
        saved_content_frame.columnconfigure(1, weight=2)
        
        # Painel de notícias em lista
        saved_list_frame = ttk.LabelFrame(saved_content_frame, text="Notícias Salvas")
        saved_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Lista de notícias salvas
        if USING_TTKBOOTSTRAP:
            self.saved_news_list = ttkb.Treeview(
                saved_list_frame,
                columns=("title", "category", "date"),
                show="headings",
                height=15
            )
        else:
            self.saved_news_list = ttk.Treeview(
                saved_list_frame,
                columns=("title", "category", "date"),
                show="headings",
                height=15
            )
            
        self.saved_news_list.heading("title", text="Título")
        self.saved_news_list.heading("category", text="Categoria")
        self.saved_news_list.heading("date", text="Data")
        self.saved_news_list.column("title", width=300)
        self.saved_news_list.column("category", width=100)
        self.saved_news_list.column("date", width=100)
        self.saved_news_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar para a lista
        saved_scrollbar = ttk.Scrollbar(saved_list_frame, orient="vertical", command=self.saved_news_list.yview)
        saved_scrollbar.pack(side="right", fill="y")
        self.saved_news_list.configure(yscrollcommand=saved_scrollbar.set)
        
        # Associar evento de duplo clique
        self.saved_news_list.bind("<Double-1>", self.open_saved_news)
        
        # Painel direito para detalhes
        saved_details_frame = ttk.LabelFrame(saved_content_frame, text="Detalhes")
        saved_details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Área de texto para detalhes
        if USING_TTKBOOTSTRAP:
            self.saved_details_text = ScrolledText(
                saved_details_frame, 
                width=40, 
                height=15, 
                bootstyle="secondary"
            )
        else:
            self.saved_details_text = ScrolledText(
                saved_details_frame, 
                width=40, 
                height=15
            )
            
        self.saved_details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar texto inicial
        self.saved_details_text.insert("1.0", "Selecione uma notícia na lista para ver os detalhes.\n\n")
        self.saved_details_text.insert("end", "Aqui você encontra todas as notícias que salvou para leitura posterior.")
        self.saved_details_text.configure(state="disabled")
        
        # Botões de ação
        saved_action_frame = ttk.Frame(saved_details_frame)
        saved_action_frame.pack(fill="x", pady=5)
        
        if USING_TTKBOOTSTRAP:
            delete_button = ttkb.Button(
                saved_action_frame, 
                text="Excluir", 
                bootstyle="danger",
                command=self.delete_saved_news
            )
        else:
            delete_button = ttk.Button(
                saved_action_frame, 
                text="Excluir",
                command=self.delete_saved_news
            )
            
        delete_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            export_button = ttkb.Button(
                saved_action_frame, 
                text="Exportar", 
                bootstyle="secondary",
                command=self.export_saved_news
            )
        else:
            export_button = ttk.Button(
                saved_action_frame, 
                text="Exportar",
                command=self.export_saved_news
            )
            
        export_button.pack(side="left", padx=5)
    
    def create_main_menu(self):
        """Cria o menu principal da aplicação"""
        self.menu_bar = tk.Menu(self.root)
        
        # Menu Arquivo
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Nova Pesquisa", command=self.new_search)
        file_menu.add_command(label="Atualizar", command=self.refresh_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Notícias", command=self.export_saved_news)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.handle_logout)
        
        # Menu Categorias
        categories_menu = tk.Menu(self.menu_bar, tearoff=0)
        categories_menu.add_command(label="Tecnologia", command=lambda: self.main_notebook.select(1))
        categories_menu.add_command(label="Cibersegurança", command=lambda: self.main_notebook.select(2))
        categories_menu.add_command(label="Inteligência Artificial", command=lambda: self.main_notebook.select(3))
        categories_menu.add_command(label="Internet das Coisas", command=lambda: self.main_notebook.select(4))
        categories_menu.add_separator()
        categories_menu.add_command(label="Minhas Notícias", command=lambda: self.main_notebook.select(5))
        
        # Menu Usuário
        user_menu = tk.Menu(self.menu_bar, tearoff=0)
        user_menu.add_command(label="Meu Perfil", command=self.show_profile)
        user_menu.add_command(label="Alterar Senha", command=self.change_password)
        user_menu.add_separator()
        user_menu.add_command(label="Configurações", command=self.show_settings)
        
        # Menu Ajuda
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self.show_about)
        help_menu.add_command(label="Tutorial", command=self.show_tutorial)
        help_menu.add_separator()
        help_menu.add_command(label="Site do Projeto", command=lambda: webbrowser.open("https://github.com/google-gemini"))
        
        # Adicionar menus à barra de menus
        self.menu_bar.add_cascade(label="Arquivo", menu=file_menu)
        self.menu_bar.add_cascade(label="Categorias", menu=categories_menu)
        self.menu_bar.add_cascade(label="Usuário", menu=user_menu)
        self.menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    
    # === Métodos para navegação entre frames ===
    
    def show_login_screen(self):
        """Mostra a tela de login"""
        # Esconder todos os frames
        for frame in [self.login_frame, self.register_frame, self.dashboard_frame]:
            frame.pack_forget()
        
        # Mostrar apenas o frame de login
        self.login_frame.pack(fill="both", expand=True)
        
        # Reset do menu principal
        self.root.config(menu="")
        
        # Limpar campos
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        
        # Foco no usuário
        self.username_entry.focus_set()
    
    def show_register_screen(self):
        """Mostra a tela de registro"""
        # Esconder todos os frames
        for frame in [self.login_frame, self.register_frame, self.dashboard_frame]:
            frame.pack_forget()
        
        # Mostrar apenas o frame de registro
        self.register_frame.pack(fill="both", expand=True)
        
        # Limpar campos
        self.fullname_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.reg_username_entry.delete(0, tk.END)
        self.reg_password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)
        
        # Foco no nome
        self.fullname_entry.focus_set()
    
    def show_dashboard(self):
        """Mostra o dashboard principal"""
        # Esconder todos os frames
        for frame in [self.login_frame, self.register_frame, self.dashboard_frame]:
            frame.pack_forget()
        
        # Atualizar rótulo do usuário
        if self.current_user:
            self.user_label.config(text=f"Olá, {self.current_user.username}")
        
        # Mostrar apenas o frame de dashboard
        self.dashboard_frame.pack(fill="both", expand=True)
        
        # Configurar menu principal
        self.root.config(menu=self.menu_bar)
        
        # Carregar dados iniciais
        self.populate_dashboard()
    
    # === Métodos para autenticação ===
    
    def handle_login(self):
        """Processa o login do usuário"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
            return
        
        try:
            # Tentar fazer login
            user = self.auth_manager.login(username, password)
            if user:
                self.current_user = user
                self.show_dashboard()
                
                # Notificar o usuário
                if USING_TTKBOOTSTRAP:
                    toast = ToastNotification(
                        title="Login realizado",
                        message=f"Bem-vindo de volta, {username}!",
                        duration=3000,
                        bootstyle="success"
                    )
                    toast.show_toast()
                else:
                    self.status_var.set(f"Bem-vindo de volta, {username}!")
            else:
                messagebox.showerror("Erro", "Usuário ou senha incorretos.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fazer login: {str(e)}")
    
    def handle_register(self):
        """Processa o registro de um novo usuário"""
        fullname = self.fullname_entry.get()
        email = self.email_entry.get()
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validações
        if not all([fullname, email, username, password, confirm_password]):
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
            return
        
        if password != confirm_password:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
        
        try:
            # Tentar registrar o usuário
            user = self.auth_manager.register(username, password, email, fullname)
            if user:
                messagebox.showinfo("Sucesso", "Conta criada com sucesso! Agora você pode fazer login.")
                self.show_login_screen()
            else:
                messagebox.showerror("Erro", "Não foi possível criar a conta. Tente novamente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar: {str(e)}")
    
    def handle_logout(self):
        """Processa o logout do usuário"""
        if messagebox.askyesno("Sair", "Tem certeza que deseja sair?"):
            self.current_user = None
            self.show_login_screen()
    
    def forgot_password(self, event=None):
        """Processo de recuperação de senha"""
        username = simpledialog.askstring("Recuperar Senha", "Digite seu nome de usuário:")
        if not username:
            return
        
        email = self.auth_manager.get_user_email(username)
        if not email:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        
        # Em um sistema real, enviaria um email com link para redefinir a senha
        # Aqui vamos apenas simular o processo
        messagebox.showinfo(
            "Recuperação de Senha", 
            f"Um email de recuperação de senha foi enviado para {email[:3]}...{email[-10:]}."
        )
    
    def change_password(self):
        """Altera a senha do usuário atual"""
        if not self.current_user:
            messagebox.showerror("Erro", "Você precisa estar logado para alterar a senha.")
            return
        
        # Pedir senha atual
        current_password = simpledialog.askstring(
            "Alterar Senha", 
            "Digite sua senha atual:",
            show="*"
        )
        
        if not current_password:
            return
        
        # Verificar senha atual
        if not self.auth_manager.verify_password(self.current_user.username, current_password):
            messagebox.showerror("Erro", "Senha incorreta.")
            return
        
        # Pedir nova senha
        new_password = simpledialog.askstring(
            "Alterar Senha", 
            "Digite a nova senha:",
            show="*"
        )
        
        if not new_password:
            return
        
        # Confirmar nova senha
        confirm_password = simpledialog.askstring(
            "Alterar Senha", 
            "Confirme a nova senha:",
            show="*"
        )
        
        if new_password != confirm_password:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
        
        # Atualizar senha
        if self.auth_manager.update_password(self.current_user.username, new_password):
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
        else:
            messagebox.showerror("Erro", "Não foi possível alterar a senha.")
    
    # === Métodos para o dashboard ===
    
    def populate_dashboard(self):
        """Popula o dashboard com dados iniciais"""
        self.populate_home_tab()
        self.fetch_category_news("Tecnologia", 1)
        self.fetch_category_news("Cibersegurança", 2)
        self.fetch_category_news("Inteligência Artificial", 3)
        self.fetch_category_news("Internet das Coisas", 4)
        self.refresh_saved_news()
    
    def populate_home_tab(self):
        """Popula a aba inicial com dados"""
        # Limpar listas existentes
        for item in self.recent_news_list.get_children():
            self.recent_news_list.delete(item)
            
        for item in self.trends_list.get_children():
            self.trends_list.delete(item)
        
        # Buscar notícias recentes (exemplo)
        recent_news = [
            {"id": 1, "title": "Nova versão do TensorFlow lançada com recursos avançados"},
            {"id": 2, "title": "Ataque hacker expõe dados de milhões de usuários"},
            {"id": 3, "title": "Avanços em IA generativa impressionam especialistas"},
            {"id": 4, "title": "Dispositivos IoT revolucionam indústria de manufatura"},
            {"id": 5, "title": "Novo padrão de segurança para redes 5G é anunciado"},
        ]
        
        # Adicionar à lista
        for news in recent_news:
            self.recent_news_list.insert("", "end", values=(news["title"],), tags=(str(news["id"]),))
        
        # Buscar tendências (exemplo)
        trends = [
            {"id": 1, "topic": "Impacto da IA na economia global"},
            {"id": 2, "topic": "Vulnerabilidades em sistemas IoT"},
            {"id": 3, "topic": "Avanços em computação quântica"},
            {"id": 4, "topic": "Segurança de APIs e microserviços"},
            {"id": 5, "topic": "Metaverso e aplicações empresariais"},
        ]
        
        # Adicionar à lista
        for trend in trends:
            self.trends_list.insert("", "end", values=(trend["topic"],), tags=(str(trend["id"]),))
        
        # Em um sistema real, usaríamos o Gemini para buscar essas informações
        # self.update_status("Dados iniciais carregados.")
    
    def fetch_category_news(self, category, tab_index):
        """Busca notícias para uma categoria específica"""
        # Obter widgets relevantes
        list_name = f"{category.lower().replace(' ', '_')}_news_list"
        news_list = getattr(self, list_name)
        
        details_name = f"{category.lower().replace(' ', '_')}_details_text"
        details_text = getattr(self, details_name)
        
        # Limpar lista existente
        for item in news_list.get_children():
            news_list.delete(item)
        
        # Atualizar área de detalhes
        details_text.configure(state="normal")
        details_text.delete("1.0", "end")
        details_text.insert("1.0", f"Buscando notícias de {category}...\n\n")
        details_text.insert("end", "Isso pode levar alguns instantes.")
        details_text.configure(state="disabled")
        
        # Atualizar status
        self.status_var.set(f"Buscando notícias de {category}...")
        
        # Executar em uma thread para não bloquear a UI
        threading.Thread(
            target=self._async_fetch_category_news,
            args=(category, tab_index, news_list, details_text),
            daemon=True
        ).start()
    
    def _async_fetch_category_news(self, category, tab_index, news_list, details_text):
        """Busca notícias de forma assíncrona"""
        try:
            # Buscar notícias com o Gemini
            query = f"Principais notícias recentes de {category}"
            news_data = self.gemini_service.fetch_news(query)
            
            # Formatar dados para exibição
            news_items = []
            if news_data and "items" in news_data:
                news_items = news_data["items"]
            elif not news_data:
                # Dados de exemplo para demonstração
                news_items = self._get_sample_news(category)
            
            # Atualizar a UI no thread principal
            self.root.after(0, lambda: self._update_news_list(news_list, details_text, news_items, category))
            
        except Exception as e:
            # Lidar com erros
            error_msg = f"Erro ao buscar notícias: {str(e)}"
            self.root.after(0, lambda: self._show_news_error(news_list, details_text, error_msg))
    
    def _update_news_list(self, news_list, details_text, news_items, category):
        """Atualiza a lista de notícias com os dados recebidos"""
        # Limpar lista
        for item in news_list.get_children():
            news_list.delete(item)
        
        # Adicionar items à lista
        for i, news in enumerate(news_items):
            date = news.get("date", "")
            news_list.insert("", "end", values=(news["title"], date), tags=(str(i),))
        
        # Atualizar área de detalhes
        details_text.configure(state="normal")
        details_text.delete("1.0", "end")
        details_text.insert("1.0", f"Notícias de {category} atualizadas.\n\n")
        details_text.insert("end", "Selecione uma notícia na lista para ver os detalhes.")
        details_text.configure(state="disabled")
        
        # Atualizar status
        self.status_var.set(f"Notícias de {category} atualizadas.")
        
        # Notificar o usuário
        if USING_TTKBOOTSTRAP:
            toast = ToastNotification(
                title=f"Notícias de {category}",
                message=f"{len(news_items)} notícias encontradas.",
                duration=3000,
                bootstyle="success"
            )
            toast.show_toast()
    
    def _show_news_error(self, news_list, details_text, error_msg):
        """Exibe mensagem de erro ao buscar notícias"""
        # Atualizar área de detalhes
        details_text.configure(state="normal")
        details_text.delete("1.0", "end")
        details_text.insert("1.0", "Erro ao buscar notícias.\n\n")
        details_text.insert("end", error_msg)
        details_text.configure(state="disabled")
        
        # Atualizar status
        self.status_var.set("Erro ao buscar notícias.")
    
    def _get_sample_news(self, category):
        """Retorna notícias de exemplo para uma categoria"""
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        
        if category == "Tecnologia":
            return [
                {"id": 1, "title": "Apple anuncia novo MacBook Pro com chip M3", "date": current_date, "content": "A Apple anunciou hoje seu novo MacBook Pro equipado com o chip M3, prometendo desempenho até 40% superior ao modelo anterior."},
                {"id": 2, "title": "Microsoft lança atualização do Windows 11", "date": current_date, "content": "A Microsoft lançou uma grande atualização para o Windows 11, trazendo novos recursos de IA e melhorias de segurança."},
                {"id": 3, "title": "Samsung revela planos para dobráveis de próxima geração", "date": current_date, "content": "A Samsung apresentou um roadmap para seus próximos smartphones dobráveis, incluindo inovações em durabilidade e usabilidade."},
                {"id": 4, "title": "Nova tecnologia de bateria promete autonomia de uma semana", "date": current_date, "content": "Pesquisadores desenvolveram uma nova tecnologia de bateria que pode permitir que smartphones funcionem por uma semana sem recarga."},
                {"id": 5, "title": "Intel apresenta processadores de 13ª geração", "date": current_date, "content": "A Intel revelou sua nova linha de processadores de 13ª geração, com foco em eficiência energética e desempenho em multitarefa."}
            ]
        elif category == "Cibersegurança":
            return [
                {"id": 1, "title": "Novo ransomware ataca sistemas hospitalares", "date": current_date, "content": "Um novo tipo de ransomware está circulando e já afetou sistemas de hospitais em vários países, causando preocupação no setor de saúde."},
                {"id": 2, "title": "Falha crítica descoberta no protocolo SSH", "date": current_date, "content": "Pesquisadores de segurança identificaram uma vulnerabilidade crítica no protocolo SSH que pode permitir acesso não autorizado a sistemas remotos."},
                {"id": 3, "title": "Aumento de 300% em ataques de phishing no último trimestre", "date": current_date, "content": "Relatório revela um aumento alarmante nos ataques de phishing, com novas técnicas que conseguem burlar filtros tradicionais."},
                {"id": 4, "title": "Nova regulamentação de cibersegurança entra em vigor na UE", "date": current_date, "content": "A União Europeia implementou novas regras de cibersegurança que exigem relatórios de incidentes em até 24 horas."},
                {"id": 5, "title": "Hackers exploram vulnerabilidade zero-day em navegadores populares", "date": current_date, "content": "Uma nova vulnerabilidade de dia zero está sendo ativamente explorada em navegadores como Chrome e Firefox, permitindo execução remota de código."}
            ]
        elif category == "Inteligência Artificial":
            return [
                {"id": 1, "title": "OpenAI lança novo modelo com capacidades multimodais", "date": current_date, "content": "A OpenAI anunciou seu mais recente modelo de IA que pode processar simultaneamente texto, imagens e áudio com precisão sem precedentes."},
                {"id": 2, "title": "IA supera médicos no diagnóstico de câncer de pele", "date": current_date, "content": "Um sistema de IA desenvolvido por pesquisadores da Universidade de Stanford demonstrou maior precisão que dermatologistas experientes na detecção de melanoma."},
                {"id": 3, "title": "Google apresenta nova arquitetura para modelos de linguagem", "date": current_date, "content": "O Google Research revelou uma arquitetura inovadora para modelos de linguagem que reduz drasticamente requisitos computacionais enquanto melhora o desempenho."},
                {"id": 4, "title": "IA generativa revoluciona indústria de design gráfico", "date": current_date, "content": "Ferramentas de IA generativa estão transformando o fluxo de trabalho de designers gráficos, permitindo criação de conceitos em segundos."},
                {"id": 5, "title": "Novo benchmark para avaliar segurança de modelos de IA", "date": current_date, "content": "Um consórcio de organizações de pesquisa lançou um benchmark abrangente para avaliar a segurança e robustez de modelos de IA de grande escala."}
            ]
        elif category == "Internet das Coisas":
            return [
                {"id": 1, "title": "Novo protocolo de segurança para dispositivos IoT é anunciado", "date": current_date, "content": "Um consórcio de empresas anunciou um novo protocolo de segurança específico para dispositivos IoT, visando combater vulnerabilidades comuns."},
                {"id": 2, "title": "Cidades inteligentes implementam redes IoT para monitoramento ambiental", "date": current_date, "content": "Várias cidades ao redor do mundo estão implementando redes IoT para monitorar qualidade do ar, níveis de ruído e outros parâmetros ambientais."},
                {"id": 3, "title": "Fabricantes adotam IoT para manutenção preditiva", "date": current_date, "content": "A indústria de manufatura está cada vez mais adotando sensores IoT para detectar falhas potenciais em equipamentos antes que elas ocorram."},
                {"id": 4, "title": "Novo chip para IoT consome 70% menos energia", "date": current_date, "content": "Uma empresa de semicondutores desenvolveu um chip específico para IoT que promete aumentar a vida útil da bateria dos dispositivos em até 70%."},
                {"id": 5, "title": "Sistemas IoT transformam agricultura de precisão", "date": current_date, "content": "Agricultores estão implementando sistemas IoT para monitoramento de solo, irrigação automatizada e detecção precoce de doenças em plantações, aumentando a produtividade."}
            ]
        else:
            return [
                {"id": 1, "title": "Notícia de exemplo 1", "date": current_date, "content": "Conteúdo da notícia de exemplo 1."},
                {"id": 2, "title": "Notícia de exemplo 2", "date": current_date, "content": "Conteúdo da notícia de exemplo 2."},
                {"id": 3, "title": "Notícia de exemplo 3", "date": current_date, "content": "Conteúdo da notícia de exemplo 3."},
                {"id": 4, "title": "Notícia de exemplo 4", "date": current_date, "content": "Conteúdo da notícia de exemplo 4."},
                {"id": 5, "title": "Notícia de exemplo 5", "date": current_date, "content": "Conteúdo da notícia de exemplo 5."}
            ]
    
    def open_category_news(self, event, category):
        """Abre a notícia selecionada na categoria"""
        # Obter widgets relevantes
        list_name = f"{category.lower().replace(' ', '_')}_news_list"
        news_list = getattr(self, list_name)
        
        details_name = f"{category.lower().replace(' ', '_')}_details_text"
        details_text = getattr(self, details_name)
        
        # Obter item selecionado
        selection = news_list.selection()
        if not selection:
            return
        
        # Obter dados do item
        item = news_list.item(selection)
        title = item["values"][0]
        date = item["values"][1] if len(item["values"]) > 1 else ""
        
        # Obter conteúdo completo
        # Em um sistema real, buscaria o conteúdo completo da notícia
        # Aqui vamos simular com dados de exemplo
        sample_news = self._get_sample_news(category)
        
        # Encontrar a notícia pelo título
        content = "Conteúdo não disponível."
        for news in sample_news:
            if news["title"] == title:
                content = news["content"]
                break
        
        # Atualizar área de detalhes
        details_text.configure(state="normal")
        details_text.delete("1.0", "end")
        details_text.insert("1.0", f"{title}\n", "title")
        details_text.insert("end", f"Data: {date}\n\n", "date")
        details_text.insert("end", f"{content}\n\n", "content")
        
        # Adicionar tags para estilização
        details_text.tag_configure("title", font=("Helvetica", 12, "bold"))
        details_text.tag_configure("date", font=("Helvetica", 10, "italic"))
        details_text.tag_configure("content", font=("Helvetica", 11))
        
        details_text.configure(state="disabled")
    
    def open_selected_news(self, event):
        """Abre a notícia selecionada na aba inicial"""
        # Obter item selecionado
        selection = self.recent_news_list.selection()
        if not selection:
            return
        
        # Obter título
        item = self.recent_news_list.item(selection)
        title = item["values"][0]
        
        # Buscar notícia completa - em um sistema real, isso seria buscado no banco de dados
        # Aqui vamos apenas abrir em uma janela simples
        self.show_news_detail_window(title, "Notícia da aba inicial")
    
    def open_saved_news(self, event):
        """Abre uma notícia salva"""
        # Obter item selecionado
        selection = self.saved_news_list.selection()
        if not selection:
            return
        
        # Obter dados do item
        item = self.saved_news_list.item(selection)
        title = item["values"][0]
        category = item["values"][1] if len(item["values"]) > 1 else ""
        date = item["values"][2] if len(item["values"]) > 2 else ""
        
        # Buscar conteúdo completo
        # Em um sistema real, buscaria do banco de dados
        content = "Este é o conteúdo completo da notícia salva."
        
        # Atualizar área de detalhes
        self.saved_details_text.configure(state="normal")
        self.saved_details_text.delete("1.0", "end")
        self.saved_details_text.insert("1.0", f"{title}\n", "title")
        self.saved_details_text.insert("end", f"Categoria: {category}\n", "category")
        self.saved_details_text.insert("end", f"Data: {date}\n\n", "date")
        self.saved_details_text.insert("end", f"{content}\n\n", "content")
        
        # Adicionar tags para estilização
        self.saved_details_text.tag_configure("title", font=("Helvetica", 12, "bold"))
        self.saved_details_text.tag_configure("category", font=("Helvetica", 10))
        self.saved_details_text.tag_configure("date", font=("Helvetica", 10, "italic"))
        self.saved_details_text.tag_configure("content", font=("Helvetica", 11))
        
        self.saved_details_text.configure(state="disabled")
    
    def show_news_detail_window(self, title, content):
        """Mostra uma janela com os detalhes da notícia"""
        # Criar janela de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.minsize(400, 300)
        
        # Configurar como modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Adicionar conteúdo
        if USING_TTKBOOTSTRAP:
            content_text = ScrolledText(dialog, bootstyle="default")
        else:
            content_text = ScrolledText(dialog)
            
        content_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Inserir conteúdo
        content_text.insert("1.0", f"{title}\n\n", "title")
        content_text.insert("end", content, "content")
        
        # Estilizar
        content_text.tag_configure("title", font=("Helvetica", 14, "bold"))
        content_text.tag_configure("content", font=("Helvetica", 12))
        
        # Desabilitar edição
        content_text.configure(state="disabled")
        
        # Botão de fechar
        close_frame = ttk.Frame(dialog)
        close_frame.pack(pady=10)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                close_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=dialog.destroy
            )
        else:
            close_button = ttk.Button(
                close_frame, 
                text="Fechar",
                command=dialog.destroy
            )
            
        close_button.pack()
        
        # Centralizar a janela
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def search_trend_topic(self, event):
        """Busca um tópico em tendência"""
        # Obter item selecionado
        selection = self.trends_list.selection()
        if not selection:
            return
        
        # Obter título
        item = self.trends_list.item(selection)
        topic = item["values"][0]
        
        # Colocar o tópico na barra de pesquisa
        self.search_var.set(topic)
        
        # Realizar a pesquisa
        self.handle_search()
    
    def handle_search(self):
        """Processa a pesquisa de notícias"""
        # Obter query
        query = self.search_var.get().strip()
        if not query:
            return
        
        # Atualizar status
        self.status_var.set(f"Pesquisando: {query}...")
        
        # Criar nova janela para exibir resultados
        self.show_search_results_window(query)
    
    def show_search_results_window(self, query):
        """Mostra janela com resultados da pesquisa"""
        # Criar janela de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Resultados para: {query}")
        dialog.geometry("800x600")
        dialog.minsize(600, 400)
        
        # Configurar layout principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, 
            text=f"Resultados da pesquisa: {query}", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(side="left")
        
        # Área de status
        status_var = tk.StringVar()
        status_var.set("Buscando resultados...")
        
        status_label = ttk.Label(title_frame, textvariable=status_var)
        status_label.pack(side="right")
        
        # Container principal
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Lista de resultados
        results_frame = ttk.LabelFrame(content_frame, text="Notícias encontradas")
        results_frame.pack(fill="both", expand=True, side="left", padx=(0, 5))
        
        # Criar lista
        if USING_TTKBOOTSTRAP:
            results_list = ttkb.Treeview(
                results_frame,
                columns=("title", "source", "date"),
                show="headings",
                height=15
            )
        else:
            results_list = ttk.Treeview(
                results_frame,
                columns=("title", "source", "date"),
                show="headings",
                height=15
            )
            
        results_list.heading("title", text="Título")
        results_list.heading("source", text="Fonte")
        results_list.heading("date", text="Data")
        results_list.column("title", width=350)
        results_list.column("source", width=150)
        results_list.column("date", width=100)
        results_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=results_list.yview)
        results_scrollbar.pack(side="right", fill="y")
        results_list.configure(yscrollcommand=results_scrollbar.set)
        
        # Área de preview
        preview_frame = ttk.LabelFrame(content_frame, text="Prévia")
        preview_frame.pack(fill="both", expand=True, side="right", padx=(5, 0))
        
        # Texto de preview
        if USING_TTKBOOTSTRAP:
            preview_text = ScrolledText(preview_frame, height=15, bootstyle="default")
        else:
            preview_text = ScrolledText(preview_frame, height=15)
            
        preview_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Texto inicial
        preview_text.insert("1.0", "Selecione uma notícia na lista para ver a prévia.\n\n")
        preview_text.insert("end", "Dica: Clique duas vezes para ver a notícia completa.")
        preview_text.configure(state="disabled")
        
        # Botões de ação
        buttons_frame = ttk.Frame(preview_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        if USING_TTKBOOTSTRAP:
            view_button = ttkb.Button(
                buttons_frame, 
                text="Ver Completo", 
                bootstyle="primary",
                command=lambda: self.view_search_result(results_list, query)
            )
        else:
            view_button = ttk.Button(
                buttons_frame, 
                text="Ver Completo",
                command=lambda: self.view_search_result(results_list, query)
            )
            
        view_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            save_button = ttkb.Button(
                buttons_frame, 
                text="Salvar", 
                bootstyle="success",
                command=lambda: self.save_search_result(results_list, query)
            )
        else:
            save_button = ttk.Button(
                buttons_frame, 
                text="Salvar",
                command=lambda: self.save_search_result(results_list, query)
            )
            
        save_button.pack(side="left", padx=5)
        
        # Rodapé
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill="x", pady=(10, 0))
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                footer_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=dialog.destroy
            )
        else:
            close_button = ttk.Button(
                footer_frame, 
                text="Fechar",
                command=dialog.destroy
            )
            
        close_button.pack(side="right")
        
        # Associar eventos
        results_list.bind("<ButtonRelease-1>", lambda e: self.preview_search_result(e, results_list, preview_text))
        results_list.bind("<Double-1>", lambda e: self.view_search_result(results_list, query))
        
        # Executar busca em uma thread
        threading.Thread(
            target=self._async_search,
            args=(query, results_list, status_var, preview_text),
            daemon=True
        ).start()
        
        # Centralizar a janela
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _async_search(self, query, results_list, status_var, preview_text):
        """Realiza a busca de forma assíncrona"""
        try:
            # Usar o serviço Gemini para buscar notícias
            results = self.gemini_service.search_news(query)
            
            # Formatar resultados para exibição
            news_items = []
            if results and "items" in results:
                news_items = results["items"]
            elif not results:
                # Dados de exemplo para demonstração
                news_items = self._get_sample_search_results(query)
            
            # Atualizar a UI no thread principal
            self.root.after(0, lambda: self._update_search_results(results_list, status_var, preview_text, news_items, query))
            
        except Exception as e:
            # Lidar com erros
            error_msg = f"Erro ao buscar notícias: {str(e)}"
            self.root.after(0, lambda: self._show_search_error(results_list, status_var, preview_text, error_msg))
    
    def _update_search_results(self, results_list, status_var, preview_text, news_items, query):
        """Atualiza a lista de resultados com os dados recebidos"""
        # Limpar lista
        for item in results_list.get_children():
            results_list.delete(item)
        
        # Adicionar items à lista
        for i, news in enumerate(news_items):
            source = news.get("source", "")
            date = news.get("date", "")
            results_list.insert("", "end", values=(news["title"], source, date), tags=(str(i),))
        
        # Atualizar status
        status_var.set(f"{len(news_items)} resultados encontrados.")
        
        # Atualizar texto de preview
        preview_text.configure(state="normal")
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", f"Pesquisa concluída para: {query}\n\n")
        preview_text.insert("end", f"{len(news_items)} resultados encontrados.\n\n")
        preview_text.insert("end", "Selecione uma notícia na lista para ver a prévia.")
        preview_text.configure(state="disabled")
    
    def _show_search_error(self, results_list, status_var, preview_text, error_msg):
        """Exibe mensagem de erro ao buscar resultados"""
        # Atualizar status
        status_var.set("Erro na pesquisa.")
        
        # Atualizar texto de preview
        preview_text.configure(state="normal")
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", "Erro ao buscar resultados.\n\n")
        preview_text.insert("end", error_msg)
        preview_text.configure(state="disabled")
    
    def _get_sample_search_results(self, query):
        """Retorna resultados de pesquisa de exemplo"""
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Resultados genéricos baseados na consulta
        return [
            {"id": 1, "title": f"Notícia recente sobre {query}", "source": "TechNews", "date": current_date, "content": f"Este é um artigo detalhado sobre {query}, abordando os desenvolvimentos mais recentes e implicações para o futuro."},
            {"id": 2, "title": f"Análise: O impacto de {query} na indústria", "source": "AnalyticsTech", "date": current_date, "content": f"Esta análise aprofundada examina como {query} está transformando a indústria e quais serão os próximos passos."},
            {"id": 3, "title": f"Especialistas discutem tendências em {query}", "source": "Tech Insider", "date": current_date, "content": f"Um painel de especialistas discutiu as tendências atuais e futuras relacionadas a {query} durante conferência internacional."},
            {"id": 4, "title": f"5 coisas que você precisa saber sobre {query}", "source": "Digital Daily", "date": current_date, "content": f"Este guia rápido explica os cinco pontos mais importantes sobre {query} que todo profissional de tecnologia deveria conhecer."},
            {"id": 5, "title": f"Como {query} está mudando o mercado de trabalho", "source": "Future Work", "date": current_date, "content": f"Um estudo recente mostra como {query} está criando novas oportunidades e desafios no mercado de trabalho global."}
        ]
    
    def preview_search_result(self, event, results_list, preview_text):
        """Mostra prévia do resultado de pesquisa selecionado"""
        # Obter item selecionado
        selection = results_list.selection()
        if not selection:
            return
        
        # Obter dados do item
        item = results_list.item(selection)
        title = item["values"][0]
        source = item["values"][1] if len(item["values"]) > 1 else ""
        date = item["values"][2] if len(item["values"]) > 2 else ""
        
        # Simular o conteúdo
        content = f"Este é um resumo da notícia '{title}' de {source}, publicada em {date}. Clique duas vezes para ler o conteúdo completo."
        
        # Atualizar texto de preview
        preview_text.configure(state="normal")
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", f"{title}\n", "title")
        preview_text.insert("end", f"Fonte: {source}\n", "source")
        preview_text.insert("end", f"Data: {date}\n\n", "date")
        preview_text.insert("end", f"{content}\n\n", "content")
        
        # Adicionar tags para estilização
        preview_text.tag_configure("title", font=("Helvetica", 12, "bold"))
        preview_text.tag_configure("source", font=("Helvetica", 10))
        preview_text.tag_configure("date", font=("Helvetica", 10, "italic"))
        preview_text.tag_configure("content", font=("Helvetica", 11))
        
        preview_text.configure(state="disabled")
    
    def view_search_result(self, results_list, query):
        """Visualiza o resultado completo da pesquisa"""
        # Obter item selecionado
        selection = results_list.selection()
        if not selection:
            messagebox.showinfo("Informação", "Selecione uma notícia na lista para visualizar.")
            return
        
        # Obter dados do item
        item = results_list.item(selection)
        title = item["values"][0]
        source = item["values"][1] if len(item["values"]) > 1 else ""
        date = item["values"][2] if len(item["values"]) > 2 else ""
        
        # Em um sistema real, buscaria o conteúdo completo
        # Aqui vamos simular com dados de exemplo
        sample_results = self._get_sample_search_results(query)
        
        # Encontrar o conteúdo pelo título
        content = f"Conteúdo completo da notícia '{title}' não disponível."
        for result in sample_results:
            if result["title"] == title:
                content = result["content"]
                break
        
        # Montar conteúdo completo
        full_content = f"Fonte: {source}\nData: {date}\n\n{content}\n\n"
        full_content += f"Esta notícia foi recuperada como parte da pesquisa por '{query}'."
        
        # Mostrar janela com conteúdo completo
        self.show_news_detail_window(title, full_content)
    
    def save_search_result(self, results_list, query):
        """Salva o resultado da pesquisa para o usuário atual"""
        # Verificar se usuário está logado
        if not self.current_user:
            messagebox.showerror("Erro", "Você precisa estar logado para salvar notícias.")
            return
        
        # Obter item selecionado
        selection = results_list.selection()
        if not selection:
            messagebox.showinfo("Informação", "Selecione uma notícia na lista para salvar.")
            return
        
        # Obter dados do item
        item = results_list.item(selection)
        title = item["values"][0]
        source = item["values"][1] if len(item["values"]) > 1 else ""
        date = item["values"][2] if len(item["values"]) > 2 else ""
        
        # Em um sistema real, salvaria no banco de dados
        # Aqui vamos apenas mostrar uma mensagem
        messagebox.showinfo(
            "Notícia Salva", 
            f"A notícia '{title}' foi salva com sucesso na sua lista de notícias."
        )
        
        # Atualizar a lista de notícias salvas
        self.refresh_saved_news()
        
        # Notificar o usuário
        if USING_TTKBOOTSTRAP:
            toast = ToastNotification(
                title="Notícia Salva",
                message=f"'{title}' adicionada à sua lista",
                duration=3000,
                bootstyle="success"
            )
            toast.show_toast()
        else:
            self.status_var.set(f"Notícia salva: {title}")
    
    def save_selected_news(self, category):
        """Salva a notícia selecionada na categoria"""
        # Verificar se usuário está logado
        if not self.current_user:
            messagebox.showerror("Erro", "Você precisa estar logado para salvar notícias.")
            return
        
        # Obter widgets relevantes
        list_name = f"{category.lower().replace(' ', '_')}_news_list"
        news_list = getattr(self, list_name)
        
        # Obter item selecionado
        selection = news_list.selection()
        if not selection:
            messagebox.showinfo("Informação", "Selecione uma notícia na lista para salvar.")
            return
        
        # Obter dados do item
        item = news_list.item(selection)
        title = item["values"][0]
        date = item["values"][1] if len(item["values"]) > 1 else ""
        
        # Em um sistema real, salvaria no banco de dados
        # Aqui vamos apenas mostrar uma mensagem
        messagebox.showinfo(
            "Notícia Salva", 
            f"A notícia '{title}' foi salva com sucesso na sua lista de notícias."
        )
        
        # Atualizar a lista de notícias salvas
        self.refresh_saved_news()
    
    def share_selected_news(self, category):
        """Compartilha a notícia selecionada"""
        # Obter widgets relevantes
        list_name = f"{category.lower().replace(' ', '_')}_news_list"
        news_list = getattr(self, list_name)
        
        # Obter item selecionado
        selection = news_list.selection()
        if not selection:
            messagebox.showinfo("Informação", "Selecione uma notícia na lista para compartilhar.")
            return
        
        # Obter dados do item
        item = news_list.item(selection)
        title = item["values"][0]
        
        # Em um sistema real, abriria opções de compartilhamento
        # Aqui vamos apenas mostrar uma janela com as opções
        share_dialog = tk.Toplevel(self.root)
        share_dialog.title("Compartilhar Notícia")
        share_dialog.geometry("400x300")
        share_dialog.minsize(350, 250)
        
        # Configurar como modal
        share_dialog.transient(self.root)
        share_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(share_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Compartilhar Notícia", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Notícia
        news_frame = ttk.LabelFrame(content_frame, text="Notícia")
        news_frame.pack(fill="x", padx=5, pady=5)
        
        news_title = ttk.Label(news_frame, text=title, wraplength=350)
        news_title.pack(padx=10, pady=10)
        
        # Opções de compartilhamento
        share_options_frame = ttk.LabelFrame(content_frame, text="Compartilhar via")
        share_options_frame.pack(fill="x", padx=5, pady=5)
        
        # Botões
        if USING_TTKBOOTSTRAP:
            email_button = ttkb.Button(
                share_options_frame, 
                text="Email", 
                bootstyle="info",
                command=lambda: self.show_share_confirmation("email", title)
            )
        else:
            email_button = ttk.Button(
                share_options_frame, 
                text="Email",
                command=lambda: self.show_share_confirmation("email", title)
            )
            
        email_button.pack(side="left", padx=10, pady=10)
        
        if USING_TTKBOOTSTRAP:
            whatsapp_button = ttkb.Button(
                share_options_frame, 
                text="WhatsApp", 
                bootstyle="success",
                command=lambda: self.show_share_confirmation("WhatsApp", title)
            )
        else:
            whatsapp_button = ttk.Button(
                share_options_frame, 
                text="WhatsApp",
                command=lambda: self.show_share_confirmation("WhatsApp", title)
            )
            
        whatsapp_button.pack(side="left", padx=10, pady=10)
        
        if USING_TTKBOOTSTRAP:
            twitter_button = ttkb.Button(
                share_options_frame, 
                text="Twitter/X", 
                bootstyle="primary",
                command=lambda: self.show_share_confirmation("Twitter/X", title)
            )
        else:
            twitter_button = ttk.Button(
                share_options_frame, 
                text="Twitter/X",
                command=lambda: self.show_share_confirmation("Twitter/X", title)
            )
            
        twitter_button.pack(side="left", padx=10, pady=10)
        
        # Botão de fechar
        close_frame = ttk.Frame(content_frame)
        close_frame.pack(pady=15)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                close_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=share_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                close_frame, 
                text="Fechar",
                command=share_dialog.destroy
            )
            
        close_button.pack()
        
        # Centralizar a janela
        share_dialog.update_idletasks()
        width = share_dialog.winfo_width()
        height = share_dialog.winfo_height()
        x = (share_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (share_dialog.winfo_screenheight() // 2) - (height // 2)
        share_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_share_confirmation(self, method, title):
        """Mostra confirmação de compartilhamento"""
        messagebox.showinfo(
            "Notícia Compartilhada", 
            f"A notícia '{title}' foi compartilhada via {method}."
        )
    
    def refresh_saved_news(self):
        """Atualiza a lista de notícias salvas"""
        # Verificar se usuário está logado
        if not self.current_user:
            return
        
        # Limpar lista existente
        for item in self.saved_news_list.get_children():
            self.saved_news_list.delete(item)
        
        # Em um sistema real, buscaria as notícias salvas do banco de dados
        # Aqui vamos usar dados de exemplo
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        saved_news = [
            {"id": 1, "title": "Novo tipo de ransomware ataca sistemas empresariais", "category": "Cibersegurança", "date": current_date},
            {"id": 2, "title": "Avanços em deep learning para processamento de linguagem natural", "category": "IA", "date": current_date},
            {"id": 3, "title": "Como dispositivos IoT estão transformando a indústria de saúde", "category": "IoT", "date": current_date},
            {"id": 4, "title": "Nova geração de processadores quânticos promete revolucionar computação", "category": "Tecnologia", "date": current_date},
            {"id": 5, "title": "Melhores práticas para segurança em ambientes de nuvem híbrida", "category": "Cibersegurança", "date": current_date},
        ]
        
        # Adicionar à lista
        for news in saved_news:
            self.saved_news_list.insert(
                "", "end", 
                values=(news["title"], news["category"], news["date"]), 
                tags=(str(news["id"]),)
            )
        
        # Atualizar área de detalhes
        self.saved_details_text.configure(state="normal")
        self.saved_details_text.delete("1.0", "end")
        self.saved_details_text.insert("1.0", "Suas notícias salvas foram atualizadas.\n\n")
        self.saved_details_text.insert("end", "Selecione uma notícia na lista para ver os detalhes.")
        self.saved_details_text.configure(state="disabled")
        
        # Atualizar status
        self.status_var.set(f"{len(saved_news)} notícias salvas encontradas.")
    
    def delete_saved_news(self):
        """Exclui a notícia salva selecionada"""
        # Obter item selecionado
        selection = self.saved_news_list.selection()
        if not selection:
            messagebox.showinfo("Informação", "Selecione uma notícia na lista para excluir.")
            return
        
        # Obter dados do item
        item = self.saved_news_list.item(selection)
        title = item["values"][0]
        
        # Confirmação
        if not messagebox.askyesno("Confirmar exclusão", f"Tem certeza que deseja excluir a notícia '{title}'?"):
            return
        
        # Em um sistema real, excluiria do banco de dados
        # Aqui vamos apenas remover da lista
        self.saved_news_list.delete(selection)
        
        # Atualizar área de detalhes
        self.saved_details_text.configure(state="normal")
        self.saved_details_text.delete("1.0", "end")
        self.saved_details_text.insert("1.0", "Notícia excluída com sucesso.\n\n")
        self.saved_details_text.insert("end", "Selecione outra notícia na lista para ver os detalhes.")
        self.saved_details_text.configure(state="disabled")
        
        # Notificar o usuário
        if USING_TTKBOOTSTRAP:
            toast = ToastNotification(
                title="Notícia Excluída",
                message="A notícia foi removida da sua lista",
                duration=3000,
                bootstyle="danger"
            )
            toast.show_toast()
        else:
            self.status_var.set("Notícia excluída.")
    
    def export_saved_news(self):
        """Exporta as notícias salvas para um arquivo"""
        # Verificar se há notícias salvas
        if not self.saved_news_list.get_children():
            messagebox.showinfo("Informação", "Não há notícias salvas para exportar.")
            return
        
        # Em um sistema real, exportaria todas as notícias salvas
        # Aqui vamos apenas criar um arquivo de texto simples
        try:
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(
                prefix="nexusinfo_", 
                suffix=".txt", 
                mode="w", 
                delete=False, 
                encoding="utf-8"
            ) as temp_file:
                # Escrever cabeçalho
                temp_file.write("NexusInfo - Notícias Salvas\n")
                temp_file.write("=========================\n\n")
                temp_file.write(f"Usuário: {self.current_user.username}\n")
                temp_file.write(f"Data de exportação: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                # Escrever notícias
                for i, item_id in enumerate(self.saved_news_list.get_children()):
                    item = self.saved_news_list.item(item_id)
                    values = item["values"]
                    
                    temp_file.write(f"Notícia {i+1}: {values[0]}\n")
                    temp_file.write(f"Categoria: {values[1]}\n")
                    temp_file.write(f"Data: {values[2]}\n")
                    temp_file.write("Conteúdo: Este é um resumo da notícia salva.\n")
                    temp_file.write("-" * 50 + "\n\n")
                
                # Adicionar rodapé
                temp_file.write("\nExportado pelo NexusInfo - Sistema de Notícias com IA")
                
                # Guardar o caminho do arquivo
                filename = temp_file.name
            
            # Abrir o arquivo
            if sys.platform == "win32":
                os.startfile(filename)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open {filename}")
            else:  # Linux e outros
                os.system(f"xdg-open {filename}")
                
            # Notificar o usuário
            messagebox.showinfo(
                "Exportação Concluída", 
                f"Suas notícias foram exportadas para um arquivo de texto e abertas para visualização."
            )
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exportar as notícias: {str(e)}")
    
    def new_search(self):
        """Inicia uma nova pesquisa"""
        # Limpar a barra de pesquisa
        self.search_var.set("")
        
        # Dar foco à barra de pesquisa
        self.search_entry.focus_set()
    
    def refresh_current_tab(self):
        """Atualiza a aba atual"""
        current_tab = self.main_notebook.select()
        tab_index = self.main_notebook.index(current_tab)
        
        if tab_index == 0:  # Aba Início
            self.populate_home_tab()
        elif tab_index == 1:  # Aba Tecnologia
            self.fetch_category_news("Tecnologia", 1)
        elif tab_index == 2:  # Aba Cibersegurança
            self.fetch_category_news("Cibersegurança", 2)
        elif tab_index == 3:  # Aba IA
            self.fetch_category_news("Inteligência Artificial", 3)
        elif tab_index == 4:  # Aba IoT
            self.fetch_category_news("Internet das Coisas", 4)
        elif tab_index == 5:  # Aba Notícias Salvas
            self.refresh_saved_news()
    
    def show_profile(self):
        """Mostra o perfil do usuário"""
        if not self.current_user:
            messagebox.showerror("Erro", "Você precisa estar logado para ver o perfil.")
            return
        
        # Criar janela de diálogo
        profile_dialog = tk.Toplevel(self.root)
        profile_dialog.title("Meu Perfil")
        profile_dialog.geometry("500x400")
        profile_dialog.minsize(400, 300)
        
        # Configurar como modal
        profile_dialog.transient(self.root)
        profile_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(profile_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Perfil do Usuário", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Informações do usuário
        user_frame = ttk.LabelFrame(content_frame, text="Informações Pessoais")
        user_frame.pack(fill="x", padx=5, pady=5)
        
        # Grid para informações
        for i, (label, value) in enumerate([
            ("Nome completo:", self.current_user.fullname),
            ("Nome de usuário:", self.current_user.username),
            ("Email:", self.current_user.email),
            ("Data de registro:", self.current_user.created_at)
        ]):
            label_widget = ttk.Label(user_frame, text=label, font=("Helvetica", 11, "bold"))
            label_widget.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            value_widget = ttk.Label(user_frame, text=value, font=("Helvetica", 11))
            value_widget.grid(row=i, column=1, sticky="w", padx=10, pady=5)
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(content_frame, text="Estatísticas")
        stats_frame.pack(fill="x", padx=5, pady=15)
        
        # Grid para estatísticas
        for i, (label, value) in enumerate([
            ("Notícias salvas:", "5"),
            ("Pesquisas realizadas:", "12"),
            ("Último acesso:", datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        ]):
            stat_label = ttk.Label(stats_frame, text=label, font=("Helvetica", 11, "bold"))
            stat_label.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            stat_value = ttk.Label(stats_frame, text=value, font=("Helvetica", 11))
            stat_value.grid(row=i, column=1, sticky="w", padx=10, pady=5)
        
        # Botões de ação
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(pady=15)
        
        if USING_TTKBOOTSTRAP:
            edit_profile_button = ttkb.Button(
                buttons_frame, 
                text="Editar Perfil", 
                bootstyle="primary",
                command=self.edit_profile
            )
        else:
            edit_profile_button = ttk.Button(
                buttons_frame, 
                text="Editar Perfil",
                command=self.edit_profile
            )
            
        edit_profile_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            change_password_button = ttkb.Button(
                buttons_frame, 
                text="Alterar Senha", 
                bootstyle="warning",
                command=self.change_password
            )
        else:
            change_password_button = ttk.Button(
                buttons_frame, 
                text="Alterar Senha",
                command=self.change_password
            )
            
        change_password_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                buttons_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=profile_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                buttons_frame, 
                text="Fechar",
                command=profile_dialog.destroy
            )
            
        close_button.pack(side="left", padx=10)
        
        # Centralizar a janela
        profile_dialog.update_idletasks()
        width = profile_dialog.winfo_width()
        height = profile_dialog.winfo_height()
        x = (profile_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (profile_dialog.winfo_screenheight() // 2) - (height // 2)
        profile_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def edit_profile(self):
        """Edita o perfil do usuário"""
        if not self.current_user:
            messagebox.showerror("Erro", "Você precisa estar logado para editar o perfil.")
            return
        
        # Pedir novo nome
        new_fullname = simpledialog.askstring(
            "Editar Perfil", 
            "Digite seu nome completo:",
            initialvalue=self.current_user.fullname
        )
        
        if not new_fullname:
            return
        
        # Pedir novo email
        new_email = simpledialog.askstring(
            "Editar Perfil", 
            "Digite seu email:",
            initialvalue=self.current_user.email
        )
        
        if not new_email:
            return
        
        # Em um sistema real, atualizaria os dados no banco
        # Aqui vamos apenas atualizar o objeto do usuário
        self.current_user.fullname = new_fullname
        self.current_user.email = new_email
        
        # Notificar o usuário
        messagebox.showinfo("Sucesso", "Perfil atualizado com sucesso!")
    
    def show_settings(self):
        """Mostra as configurações do aplicativo"""
        # Criar janela de diálogo
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("Configurações")
        settings_dialog.geometry("500x400")
        settings_dialog.minsize(400, 300)
        
        # Configurar como modal
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(settings_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Configurações do Aplicativo", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Configurações de tema
        theme_frame = ttk.LabelFrame(content_frame, text="Aparência")
        theme_frame.pack(fill="x", padx=5, pady=5)
        
        theme_label = ttk.Label(theme_frame, text="Tema:", font=("Helvetica", 11))
        theme_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        theme_var = tk.StringVar(value="dark")
        
        if USING_TTKBOOTSTRAP:
            theme_options = ["light", "dark", "superhero", "cosmo", "flatly", "solar"]
            theme_combobox = ttkb.Combobox(
                theme_frame, 
                textvariable=theme_var,
                values=theme_options,
                bootstyle="default"
            )
        else:
            theme_options = ["light", "dark", "system"]
            theme_combobox = ttk.Combobox(
                theme_frame, 
                textvariable=theme_var,
                values=theme_options
            )
            
        theme_combobox.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        theme_combobox.current(1)  # Selecionar dark por padrão
        
        # Preferências de notificações
        notifications_frame = ttk.LabelFrame(content_frame, text="Notificações")
        notifications_frame.pack(fill="x", padx=5, pady=15)
        
        # Checkbox para notificações
        notifications_var = tk.BooleanVar(value=True)
        
        if USING_TTKBOOTSTRAP:
            notifications_checkbutton = ttkb.Checkbutton(
                notifications_frame, 
                text="Ativar notificações", 
                variable=notifications_var,
                bootstyle="success-round-toggle"
            )
        else:
            notifications_checkbutton = ttk.Checkbutton(
                notifications_frame, 
                text="Ativar notificações", 
                variable=notifications_var
            )
            
        notifications_checkbutton.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Checkbox para sons
        sounds_var = tk.BooleanVar(value=True)
        
        if USING_TTKBOOTSTRAP:
            sounds_checkbutton = ttkb.Checkbutton(
                notifications_frame, 
                text="Ativar sons", 
                variable=sounds_var,
                bootstyle="success-round-toggle"
            )
        else:
            sounds_checkbutton = ttk.Checkbutton(
                notifications_frame, 
                text="Ativar sons", 
                variable=sounds_var
            )
            
        sounds_checkbutton.grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        # Configurações de API
        api_frame = ttk.LabelFrame(content_frame, text="API Gemini")
        api_frame.pack(fill="x", padx=5, pady=5)
        
        api_key_label = ttk.Label(api_frame, text="API Key:", font=("Helvetica", 11))
        api_key_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Mascarar a key atual
        masked_key = "●" * len(self.gemini_service.api_key)
        
        api_key_var = tk.StringVar(value=masked_key)
        api_key_entry = ttk.Entry(
            api_frame, 
            textvariable=api_key_var, 
            width=30
        )
        api_key_entry.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Botões de ação
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(pady=15)
        
        if USING_TTKBOOTSTRAP:
            save_button = ttkb.Button(
                buttons_frame, 
                text="Salvar", 
                bootstyle="success",
                command=lambda: self.save_settings(theme_var.get(), notifications_var.get(), sounds_var.get(), api_key_var.get(), settings_dialog)
            )
        else:
            save_button = ttk.Button(
                buttons_frame, 
                text="Salvar",
                command=lambda: self.save_settings(theme_var.get(), notifications_var.get(), sounds_var.get(), api_key_var.get(), settings_dialog)
            )
            
        save_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                buttons_frame, 
                text="Cancelar", 
                bootstyle="secondary",
                command=settings_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                buttons_frame, 
                text="Cancelar",
                command=settings_dialog.destroy
            )
            
        close_button.pack(side="left", padx=10)
        
        # Botão para resetar configurações
        if USING_TTKBOOTSTRAP:
            reset_button = ttkb.Button(
                buttons_frame, 
                text="Restaurar Padrões", 
                bootstyle="danger",
                command=lambda: self.reset_settings(theme_combobox, notifications_var, sounds_var, api_key_var)
            )
        else:
            reset_button = ttk.Button(
                buttons_frame, 
                text="Restaurar Padrões",
                command=lambda: self.reset_settings(theme_combobox, notifications_var, sounds_var, api_key_var)
            )
            
        reset_button.pack(side="left", padx=10)
        
        # Centralizar a janela
        settings_dialog.update_idletasks()
        width = settings_dialog.winfo_width()
        height = settings_dialog.winfo_height()
        x = (settings_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_dialog.winfo_screenheight() // 2) - (height // 2)
        settings_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def save_settings(self, theme, notifications, sounds, api_key, dialog):
        """Salva as configurações do aplicativo"""
        # Em um sistema real, salvaria as configurações em um arquivo ou banco de dados
        # Aqui vamos apenas mostrar uma mensagem
        
        # API Key não foi alterada
        if all(c == "●" for c in api_key):
            masked = True
        else:
            masked = False
            # Atualizar API key se for diferente da mascarada
            self.gemini_service.api_key = api_key
        
        # Aplicar tema
        if USING_TTKBOOTSTRAP:
            try:
                # Alterar o tema é um pouco mais complexo no ttkbootstrap
                style = ttkb.Style()
                style.theme_use(theme)
            except:
                messagebox.showerror("Erro", f"Não foi possível aplicar o tema '{theme}'.")
        
        # Fechar diálogo
        dialog.destroy()
        
        # Notificar o usuário
        messagebox.showinfo(
            "Configurações Salvas", 
            f"Suas configurações foram salvas com sucesso!\n\n"
            f"Tema: {theme}\n"
            f"Notificações: {'Ativadas' if notifications else 'Desativadas'}\n"
            f"Sons: {'Ativados' if sounds else 'Desativados'}\n"
            f"API Key: {'Não alterada' if masked else 'Atualizada'}"
        )
    
    def reset_settings(self, theme_combobox, notifications_var, sounds_var, api_key_var):
        """Restaura as configurações padrão"""
        # Restaurar valores
        theme_combobox.current(1)  # dark
        notifications_var.set(True)
        sounds_var.set(True)
        
        # Restaurar API key (máscarada)
        masked_key = "●" * len(self.gemini_service.api_key)
        api_key_var.set(masked_key)
        
        # Notificar o usuário
        messagebox.showinfo(
            "Configurações Restauradas", 
            "As configurações foram restauradas para os valores padrão."
        )
    
    def show_about(self):
        """Mostra informações sobre o aplicativo"""
        # Criar janela de diálogo
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("Sobre o NexusInfo")
        about_dialog.geometry("500x400")
        about_dialog.minsize(400, 300)
        
        # Configurar como modal
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(about_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título e logo
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 20))
        
        # Tentar carregar o logo
        logo_path = ASSETS_DIR / "logo.png"
        logo_label = None
        
        if logo_path.exists():
            try:
                logo_image = PhotoImage(file=str(logo_path))
                logo_label = ttk.Label(title_frame, image=logo_image)
                logo_label.image = logo_image  # Manter referência
                logo_label.pack(pady=(0, 10))
            except:
                pass  # Falha ao carregar logo, ignorar
        
        title_font = ("Helvetica", 18, "bold")
        title_label = ttk.Label(
            title_frame, 
            text="NexusInfo", 
            font=title_font
        )
        title_label.pack()
        
        version_label = ttk.Label(
            title_frame, 
            text="Versão 1.0", 
            font=("Helvetica", 10)
        )
        version_label.pack()
        
        # Descrição
        desc_frame = ttk.LabelFrame(content_frame, text="Sobre")
        desc_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        desc_text = (
            "NexusInfo é um sistema avançado de notícias com inteligência artificial, "
            "que utiliza a API Gemini para buscar e processar notícias sobre tecnologia, "
            "cibersegurança, inteligência artificial e Internet das Coisas.\n\n"
            "Este aplicativo foi desenvolvido para demonstrar o uso da API Gemini "
            "em conjunto com uma interface gráfica moderna em Python/Tkinter."
        )
        
        if USING_TTKBOOTSTRAP:
            desc_label = ScrolledText(
                desc_frame, 
                wrap="word", 
                height=6, 
                bootstyle="default"
            )
        else:
            desc_label = ScrolledText(
                desc_frame, 
                wrap="word", 
                height=6
            )
            
        desc_label.pack(fill="both", expand=True, padx=5, pady=5)
        desc_label.insert("1.0", desc_text)
        desc_label.configure(state="disabled")
        
        # Créditos
        credits_frame = ttk.LabelFrame(content_frame, text="Créditos")
        credits_frame.pack(fill="x", padx=5, pady=5)
        
        credits_text = (
            "© 2025 NexusInfo Team\n"
            "Desenvolvido com Python, Tkinter e Google Gemini API\n"
            "Distribuído sob licença MIT"
        )
        
        credits_label = ttk.Label(
            credits_frame, 
            text=credits_text, 
            justify="center"
        )
        credits_label.pack(padx=10, pady=10)
        
        # Botões
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(pady=15)
        
        if USING_TTKBOOTSTRAP:
            website_button = ttkb.Button(
                buttons_frame, 
                text="Website", 
                bootstyle="info",
                command=lambda: webbrowser.open("https://github.com/google-gemini")
            )
        else:
            website_button = ttk.Button(
                buttons_frame, 
                text="Website",
                command=lambda: webbrowser.open("https://github.com/google-gemini")
            )
            
        website_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            license_button = ttkb.Button(
                buttons_frame, 
                text="Licença", 
                bootstyle="primary",
                command=self.show_license
            )
        else:
            license_button = ttk.Button(
                buttons_frame, 
                text="Licença",
                command=self.show_license
            )
            
        license_button.pack(side="left", padx=10)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                buttons_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=about_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                buttons_frame, 
                text="Fechar",
                command=about_dialog.destroy
            )
            
        close_button.pack(side="left", padx=10)
        
        # Centralizar a janela
        about_dialog.update_idletasks()
        width = about_dialog.winfo_width()
        height = about_dialog.winfo_height()
        x = (about_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (about_dialog.winfo_screenheight() // 2) - (height // 2)
        about_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_license(self):
        """Mostra a licença do aplicativo"""
        # Criar janela de diálogo
        license_dialog = tk.Toplevel(self.root)
        license_dialog.title("Licença")
        license_dialog.geometry("600x500")
        license_dialog.minsize(500, 400)
        
        # Configurar como modal
        license_dialog.transient(self.root)
        license_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(license_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Licença MIT", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Texto da licença
        license_text = """
        Copyright (c) 2025 NexusInfo Team

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        """
        
        if USING_TTKBOOTSTRAP:
            license_text_widget = ScrolledText(
                content_frame, 
                wrap="word", 
                height=15, 
                bootstyle="default"
            )
        else:
            license_text_widget = ScrolledText(
                content_frame, 
                wrap="word", 
                height=15
            )
            
        license_text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        license_text_widget.insert("1.0", license_text)
        license_text_widget.configure(state="disabled")
        
        # Botão de fechar
        close_frame = ttk.Frame(content_frame)
        close_frame.pack(pady=15)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                close_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=license_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                close_frame, 
                text="Fechar",
                command=license_dialog.destroy
            )
            
        close_button.pack()
        
        # Centralizar a janela
        license_dialog.update_idletasks()
        width = license_dialog.winfo_width()
        height = license_dialog.winfo_height()
        x = (license_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (license_dialog.winfo_screenheight() // 2) - (height // 2)
        license_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_tutorial(self):
        """Mostra o tutorial do aplicativo"""
        # Criar janela de diálogo
        tutorial_dialog = tk.Toplevel(self.root)
        tutorial_dialog.title("Tutorial")
        tutorial_dialog.geometry("700x500")
        tutorial_dialog.minsize(600, 400)
        
        # Configurar como modal
        tutorial_dialog.transient(self.root)
        tutorial_dialog.grab_set()
        
        # Conteúdo
        content_frame = ttk.Frame(tutorial_dialog, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Tutorial do NexusInfo", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Notebook para passos do tutorial
        if USING_TTKBOOTSTRAP:
            steps_notebook = ttkb.Notebook(content_frame)
        else:
            steps_notebook = ttk.Notebook(content_frame)
            
        steps_notebook.pack(fill="both", expand=True)
        
        # Passo 1: Visão Geral
        step1_frame = ttk.Frame(steps_notebook, padding=10)
        steps_notebook.add(step1_frame, text="Visão Geral")
        
        step1_text = """
        O NexusInfo é um sistema avançado de notícias que utiliza a API Gemini para buscar e processar notícias sobre tecnologia, cibersegurança, inteligência artificial e Internet das Coisas.

        Principais recursos:
        
        • Consulte notícias em tempo real de diversas fontes
        • Pesquise tópicos específicos de seu interesse
        • Salve notícias para leitura posterior
        • Compartilhe conteúdo interessante com amigos
        • Navegue por categorias especializadas em tecnologia

        Este tutorial irá guiá-lo pelos principais recursos do sistema.
        """
        
        if USING_TTKBOOTSTRAP:
            step1_text_widget = ScrolledText(
                step1_frame, 
                wrap="word",
                bootstyle="default"
            )
        else:
            step1_text_widget = ScrolledText(
                step1_frame, 
                wrap="word"
            )
            
        step1_text_widget.pack(fill="both", expand=True)
        step1_text_widget.insert("1.0", step1_text)
        step1_text_widget.configure(state="disabled")
        
        # Passo 2: Navegação
        step2_frame = ttk.Frame(steps_notebook, padding=10)
        steps_notebook.add(step2_frame, text="Navegação")
        
        step2_text = """
        O NexusInfo possui uma interface intuitiva organizada em abas:
        
        • Início: Página principal com notícias recentes e tendências
        • Tecnologia: Notícias específicas de tecnologia
        • Cibersegurança: Notícias sobre segurança digital
        • Inteligência Artificial: Novidades sobre IA e Machine Learning
        • Internet das Coisas: Notícias sobre dispositivos conectados
        • Minhas Notícias: Lista das notícias que você salvou

        Para navegar, basta clicar na aba desejada ou usar os botões de atalho na tela inicial.

        A barra de pesquisa no topo permite buscar notícias sobre qualquer tópico.
        """
        
        if USING_TTKBOOTSTRAP:
            step2_text_widget = ScrolledText(
                step2_frame, 
                wrap="word",
                bootstyle="default"
            )
        else:
            step2_text_widget = ScrolledText(
                step2_frame, 
                wrap="word"
            )
            
        step2_text_widget.pack(fill="both", expand=True)
        step2_text_widget.insert("1.0", step2_text)
        step2_text_widget.configure(state="disabled")
        
        # Passo 3: Pesquisa
        step3_frame = ttk.Frame(steps_notebook, padding=10)
        steps_notebook.add(step3_frame, text="Pesquisa")
        
        step3_text = """
        A pesquisa do NexusInfo é alimentada pela API Gemini, permitindo encontrar notícias relevantes e atualizadas.

        Para pesquisar:
        
        1. Digite sua consulta na barra de pesquisa no topo da janela
        2. Clique no botão "Pesquisar" ou pressione Enter
        3. Os resultados serão exibidos em uma nova janela
        4. Clique em um resultado para ver mais detalhes
        5. Você pode salvar ou compartilhar notícias a partir da janela de resultados

        Dicas de pesquisa:
        • Seja específico: "vulnerabilidades em IoT" em vez de apenas "IoT"
        • Use termos técnicos para resultados mais precisos
        • Você pode pesquisar por empresas, tecnologias ou conceitos específicos
        """
        
        if USING_TTKBOOTSTRAP:
            step3_text_widget = ScrolledText(
                step3_frame, 
                wrap="word",
                bootstyle="default"
            )
        else:
            step3_text_widget = ScrolledText(
                step3_frame, 
                wrap="word"
            )
            
        step3_text_widget.pack(fill="both", expand=True)
        step3_text_widget.insert("1.0", step3_text)
        step3_text_widget.configure(state="disabled")
        
        # Passo 4: Gerenciamento de Notícias
        step4_frame = ttk.Frame(steps_notebook, padding=10)
        steps_notebook.add(step4_frame, text="Gerenciar Notícias")
        
        step4_text = """
        O NexusInfo permite salvar e gerenciar notícias para consulta posterior:

        Para salvar uma notícia:
        
        1. Selecione uma notícia em qualquer categoria ou resultado de pesquisa
        2. Clique no botão "Salvar"
        3. A notícia será adicionada à sua lista pessoal

        Para gerenciar suas notícias salvas:
        
        1. Navegue até a aba "Minhas Notícias"
        2. Você verá todas as notícias salvas em uma lista
        3. Selecione uma notícia para ver seus detalhes
        4. Use o botão "Excluir" para remover uma notícia da sua lista
        5. O botão "Exportar" permite salvar todas as suas notícias em um arquivo de texto
        """
        
        if USING_TTKBOOTSTRAP:
            step4_text_widget = ScrolledText(
                step4_frame, 
                wrap="word",
                bootstyle="default"
            )
        else:
            step4_text_widget = ScrolledText(
                step4_frame, 
                wrap="word"
            )
            
        step4_text_widget.pack(fill="both", expand=True)
        step4_text_widget.insert("1.0", step4_text)
        step4_text_widget.configure(state="disabled")
        
        # Passo 5: Perfil e Configurações
        step5_frame = ttk.Frame(steps_notebook, padding=10)
        steps_notebook.add(step5_frame, text="Perfil e Configurações")
        
        step5_text = """
        Gerencie seu perfil e personalize o aplicativo:

        Perfil do Usuário:
        
        • Acesse seu perfil pelo menu "Usuário" > "Meu Perfil"
        • Visualize suas informações pessoais e estatísticas
        • Edite seu nome completo e email
        • Altere sua senha quando necessário

        Configurações do Aplicativo:
        
        • Acesse as configurações pelo menu "Usuário" > "Configurações"
        • Altere o tema da interface entre claro e escuro
        • Configure notificações e sons
        • Gerencie sua chave da API Gemini
        • Restaure as configurações padrão se necessário
        """
        
        if USING_TTKBOOTSTRAP:
            step5_text_widget = ScrolledText(
                step5_frame, 
                wrap="word",
                bootstyle="default"
            )
        else:
            step5_text_widget = ScrolledText(
                step5_frame, 
                wrap="word"
            )
            
        step5_text_widget.pack(fill="both", expand=True)
        step5_text_widget.insert("1.0", step5_text)
        step5_text_widget.configure(state="disabled")
        
        # Botões de navegação
        nav_frame = ttk.Frame(content_frame)
        nav_frame.pack(fill="x", pady=(10, 0))
        
        def go_prev():
            current = steps_notebook.index(steps_notebook.select())
            if current > 0:
                steps_notebook.select(current - 1)
        
        def go_next():
            current = steps_notebook.index(steps_notebook.select())
            if current < len(steps_notebook.tabs()) - 1:
                steps_notebook.select(current + 1)
        
        if USING_TTKBOOTSTRAP:
            prev_button = ttkb.Button(
                nav_frame, 
                text="Anterior", 
                bootstyle="secondary",
                command=go_prev
            )
        else:
            prev_button = ttk.Button(
                nav_frame, 
                text="Anterior",
                command=go_prev
            )
            
        prev_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            next_button = ttkb.Button(
                nav_frame, 
                text="Próximo", 
                bootstyle="primary",
                command=go_next
            )
        else:
            next_button = ttk.Button(
                nav_frame, 
                text="Próximo",
                command=go_next
            )
            
        next_button.pack(side="left", padx=5)
        
        if USING_TTKBOOTSTRAP:
            close_button = ttkb.Button(
                nav_frame, 
                text="Fechar", 
                bootstyle="secondary",
                command=tutorial_dialog.destroy
            )
        else:
            close_button = ttk.Button(
                nav_frame, 
                text="Fechar",
                command=tutorial_dialog.destroy
            )
            
        close_button.pack(side="right", padx=5)
        
        # Centralizar a janela
        tutorial_dialog.update_idletasks()
        width = tutorial_dialog.winfo_width()
        height = tutorial_dialog.winfo_height()
        x = (tutorial_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (tutorial_dialog.winfo_screenheight() // 2) - (height // 2)
        tutorial_dialog.geometry(f"{width}x{height}+{x}+{y}")

# Função principal para iniciar o aplicativo
def main():
    """Função principal que inicia o aplicativo"""
    # Obter configurações das variáveis de ambiente
    theme = os.getenv("NEXUSINFO_THEME", "darkly")  # Tema padrão
    debug = os.getenv("NEXUSINFO_DEBUG") == "1"
    
    if debug:
        print("Iniciando em modo de depuração")
        print(f"Tema: {theme}")
        print(f"API Gemini configurada: {'Sim' if os.getenv('GOOGLE_API_KEY') else 'Não'}")
    
    if USING_TTKBOOTSTRAP:
        # Usar tema do ttkbootstrap
        root = ttkb.Window(
            title="NexusInfo - Sistema de Notícias com IA",
            themename=theme,  # Tema configurado
            size=(1200, 800),
            position=(100, 50),
            minsize=(800, 600)
        )
    else:
        # Usar Tk padrão
        root = tk.Tk()
        root.title("NexusInfo - Sistema de Notícias com IA")
        root.geometry("1200x800+100+50")
        root.minsize(800, 600)
    
    # Configurar ícone se disponível
    icon_path = ASSETS_DIR / "icon.png"
    if icon_path.exists():
        root.iconphoto(True, PhotoImage(file=str(icon_path)))
    
    # Criar aplicação
    app = NexusInfoApp(root)
    
    # Iniciar loop principal
    root.mainloop()

if __name__ == "__main__":
    main()
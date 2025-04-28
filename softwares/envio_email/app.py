"""
Sistema de Envio de E-mails para Prefeituras
==========================================
Aplicativo desktop para gerenciamento e envio de e-mails institucionais
das prefeituras de São José e Florianópolis.

Autor: LTD
Data: Abril 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import smtplib
import ssl
import csv
import os
import json
import datetime
import threading
import schedule
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import pandas as pd
import hashlib

# Configuração de logging
logging.basicConfig(
    filename='prefeituras_email_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_system')

# Cores das prefeituras
CORES = {
    'sj': {
        'primaria': '#004A8F',  # Azul escuro
        'secundaria': '#1E1E1E',  # Preto escuro
        'destaque': '#F39200',  # Laranja
        'texto': '#FFFFFF',  # Branco
        'texto_secundario': '#CCCCCC',  # Cinza claro
        'fundo': '#333333',  # Preto
        'fundo_input': '#333333',  # Cinza escuro
    },
    'floripa': {
        'primaria': '#00529B',  # Azul escuro
        'secundaria': '#1E1E1E',  # Preto escuro
        'destaque': '#FF6B00',  # Laranja
        'texto': '#FFFFFF',  # Branco
        'texto_secundario': '#CCCCCC',  # Cinza claro
        'fundo': '#333333',  # Preto
        'fundo_input': '#333333',  # Cinza escuro
    }
}

# Diretório de recursos e configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

for directory in [RESOURCES_DIR, CONFIG_DIR, TEMPLATE_DIR, BACKUP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Arquivo de configuração
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Banco de dados
DB_FILE = os.path.join(BASE_DIR, 'prefeituras_email.db')

class SistemaEmail:
    """Classe principal do sistema de envio de e-mails."""
    
    def __init__(self, root):
        """Inicializa a aplicação."""
        self.root = root
        self.root.title("Sistema de Envio de E-mails - Prefeituras")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Carrega configurações
        self.config = self.carregar_configuracoes()
        
        # Seleciona a prefeitura inicial
        self.prefeitura_atual = self.config.get('prefeitura_padrao', 'sj')
        
        # Configura tema de cores
        self.cores = CORES[self.prefeitura_atual]
        
        # Inicializa o banco de dados
        self.inicializar_banco_dados()
        
        # Cria a interface
        self.criar_interface()
        
        # Inicia o agendador em uma thread separada
        self.agendar_thread = threading.Thread(target=self.executar_agendador, daemon=True)
        self.agendar_thread.start()

    def configurar_cores_texto(self):
        """Configura a cor do texto em todos os widgets para preto."""
        style = ttk.Style()
        
        # Configuração para Entry (campos de texto)
        style.configure('TEntry', foreground='black')
        
        # Configuração para Combobox
        style.configure('TCombobox', foreground='black')
        style.map('TCombobox', foreground=[('readonly', 'black')])
        
        # Configuração para Treeview (tabelas)
        style.configure('Treeview', foreground='black')
        style.map('Treeview', foreground=[('selected', 'black')])
        
    def carregar_configuracoes(self):
        """Carrega as configurações do arquivo JSON."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configurações: {e}")
                return self.configuracoes_padrao()
        else:
            return self.configuracoes_padrao()
    
    def salvar_configuracoes(self):
        """Salva as configurações no arquivo JSON."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info("Configurações salvas com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar as configurações: {e}")
            return False
    
    def configuracoes_padrao(self):
        """Retorna as configurações padrão do sistema."""
        return {
            'prefeitura_padrao': 'sj',
            'smtp': {
                'sj': {
                    'servidor': 'smtp.saojose.sc.gov.br',
                    'porta': 587,
                    'usuario': '',
                    'senha': '',
                    'tls': True,
                    'ssl': False
                },
                'floripa': {
                    'servidor': 'smtp.pmf.sc.gov.br',
                    'porta': 587,
                    'usuario': '',
                    'senha': '',
                    'tls': True,
                    'ssl': False
                }
            },
            'assinaturas': {
                'sj': {
                    'padrao': '''
                    <p>Atenciosamente,</p>
                    <p><strong>{nome}</strong><br>
                    {cargo}<br>
                    {departamento}<br>
                    Prefeitura Municipal de São José<br>
                    Telefone: {telefone}</p>
                    '''
                },
                'floripa': {
                    'padrao': '''
                    <p>Atenciosamente,</p>
                    <p><strong>{nome}</strong><br>
                    {cargo}<br>
                    {departamento}<br>
                    Prefeitura Municipal de Florianópolis<br>
                    Telefone: {telefone}</p>
                    '''
                }
            },
            'backup': {
                'automatico': True,
                'intervalo': 'diario',  # diario, semanal, mensal
                'hora': '23:00'
            }
        }
    
    def inicializar_banco_dados(self):
        """Inicializa o banco de dados SQLite."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                prefeitura TEXT NOT NULL,
                cargo TEXT,
                departamento TEXT,
                telefone TEXT,
                nivel_acesso INTEGER NOT NULL DEFAULT 1,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acesso TIMESTAMP
            )
            ''')
            
            # Tabela de funcionários
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cargo TEXT,
                departamento TEXT,
                telefone TEXT,
                prefeitura TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            )
            ''')
            
            # Tabela de grupos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS grupos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                prefeitura TEXT NOT NULL
            )
            ''')
            
            # Tabela de relacionamento entre grupos e funcionários
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS grupo_funcionario (
                grupo_id INTEGER,
                funcionario_id INTEGER,
                PRIMARY KEY (grupo_id, funcionario_id),
                FOREIGN KEY (grupo_id) REFERENCES grupos (id),
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
            )
            ''')
            
            # Tabela de templates
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                assunto TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                prefeitura TEXT NOT NULL,
                departamento TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabela de e-mails enviados
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                assunto TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                destinatarios TEXT NOT NULL,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')
            
            # Tabela de e-mails agendados
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails_agendados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                assunto TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                destinatarios TEXT NOT NULL,
                data_agendada TIMESTAMP NOT NULL,
                recorrencia TEXT, -- diario, semanal, mensal, nenhuma
                status TEXT NOT NULL DEFAULT 'pendente',
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')
            
            # Tabela de logs
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                descricao TEXT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')
            
            # Verifica se existe um usuário administrador, se não, cria um
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nivel_acesso = 3")
            if cursor.fetchone()[0] == 0:
                # Cria usuário admin com senha padrão 'admin'
                senha_hash = hashlib.sha256('admin'.encode()).hexdigest()
                cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, prefeitura, cargo, departamento, nivel_acesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ('Administrador', 'admin@admin.com', senha_hash, 'sj', 'Administrador', 'TI', 3))
            
            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            messagebox.showerror("Erro", f"Não foi possível inicializar o banco de dados: {e}")
    
    def criar_interface(self):
        """Cria a interface gráfica do sistema."""
        # Cria o painel principal
        self.frame_principal = ttk.Frame(self.root)
        self.frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Configura o tema escuro
        self.configurar_estilo_tema_escuro()

        # Configura a cor do texto para preto
        self.configurar_cores_texto()
        
        # Cria o painel de login
        self.criar_tela_login()
    
    def configurar_estilo_tema_escuro(self):
        """Configura o estilo visual do sistema para o tema escuro."""
        style = ttk.Style()
        
        # Definições globais
        style.configure('TFrame', background=self.cores['fundo'])
        style.configure('TLabel', background=self.cores['fundo'], foreground=self.cores['texto'])
        style.configure('TButton', background=self.cores['primaria'], foreground=self.cores['texto'])
        
        # Notebook (abas)
        style.configure('TNotebook', background=self.cores['fundo'])
        style.configure('TNotebook.Tab', background=self.cores['secundaria'], 
                        foreground=self.cores['texto'], padding=[10, 5])
        style.map('TNotebook.Tab', 
                background=[('selected', self.cores['primaria'])],
                foreground=[('selected', self.cores['texto'])])
        
        # Entry (campos de texto)
        style.configure('TEntry', fieldbackground=self.cores['fundo_input'], 
                    foreground=self.cores['texto'], insertcolor=self.cores['texto'])
        
        # Combobox
        style.configure('TCombobox', fieldbackground=self.cores['fundo_input'], 
                    background=self.cores['fundo_input'], foreground=self.cores['texto'])
        style.map('TCombobox', 
                fieldbackground=[('readonly', self.cores['fundo_input'])],
                selectbackground=[('readonly', self.cores['primaria'])])
        
        # Treeview (tabelas)
        style.configure('Treeview', 
                    background=self.cores['fundo_input'], 
                    fieldbackground=self.cores['fundo_input'], 
                    foreground=self.cores['texto'])
        style.map('Treeview', 
                background=[('selected', self.cores['primaria'])],
                foreground=[('selected', self.cores['texto'])])
        
        # Scrollbar
        style.configure('TScrollbar', background=self.cores['fundo_input'], 
                    troughcolor=self.cores['fundo'], 
                    activebackground=self.cores['primaria'])
        
        # Configurações para o menu
        style.configure('Menu.TFrame', background=self.cores['primaria'])
        style.configure('Menu.TLabel', background=self.cores['primaria'], foreground='black')
        style.configure('Menu.TButton', background=self.cores['destaque'], foreground='black')
    
    
    def criar_tela_login(self):
        """Cria a tela de login."""
        # Limpa a tela
        for widget in self.frame_principal.winfo_children():
            widget.destroy()

        # Frame de login
        frame_login = ttk.Frame(self.frame_principal, padding=20)
        frame_login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Logo
        try:
            if self.prefeitura_atual == 'sj':
                logo_path = os.path.join(RESOURCES_DIR, 'logo_sj.png')
            else:
                logo_path = os.path.join(RESOURCES_DIR, 'logo_floripa.png')
                
            # Se o arquivo não existir, cria um placeholder
            if not os.path.exists(logo_path):
                # Cria um diretório se não existir
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                
                # Cria uma imagem placeholder
                img = Image.new('RGB', (200, 100), color=(30, 30, 30))
                img.save(logo_path)
            
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 100), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ttk.Label(frame_login, image=logo_photo)
            logo_label.image = logo_photo  # Mantém uma referência
            logo_label.pack(pady=10)
        except Exception as e:
            logger.error(f"Erro ao carregar logo: {e}")
            # Cria um label de texto como fallback
            logo_label = ttk.Label(frame_login, text="Sistema de E-mail Institucional", 
                                    font=('Helvetica', 16, 'bold'))
            logo_label.pack(pady=10)
        
        # Título
        titulo = ttk.Label(frame_login, text="Login do Sistema", font=('Helvetica', 14, 'bold'))
        titulo.pack(pady=10)
        
        # Form de login
        frame_form = ttk.Frame(frame_login)
        frame_form.pack(pady=10, fill=tk.X)
        
        # Email
        ttk.Label(frame_form, text="E-mail:").pack(anchor=tk.W, pady=(5, 0))
        self.entry_email = ttk.Entry(frame_form, width=30)
        self.entry_email.pack(fill=tk.X, pady=(0, 10))
        
        # Senha
        ttk.Label(frame_form, text="Senha:").pack(anchor=tk.W, pady=(5, 0))
        self.entry_senha = ttk.Entry(frame_form, width=30, show="*")
        self.entry_senha.pack(fill=tk.X, pady=(0, 10))
        
        # Prefeitura
        ttk.Label(frame_form, text="Prefeitura:").pack(anchor=tk.W, pady=(5, 0))
        self.combo_prefeitura = ttk.Combobox(frame_form, 
                                        values=["São José", "Florianópolis"],
                                        state="readonly")
        self.combo_prefeitura.pack(fill=tk.X, pady=(0, 10))
        self.combo_prefeitura.current(0 if self.prefeitura_atual == 'sj' else 1)
        self.combo_prefeitura.bind("<<ComboboxSelected>>", self.alterar_prefeitura)
        
        # Botão de login
        btn_login = ttk.Button(frame_login, text="Entrar", command=self.fazer_login)
        btn_login.pack(pady=10, fill=tk.X)
        
        # Mensagem de erro
        self.lbl_erro = ttk.Label(frame_login, text="", foreground="red")
        self.lbl_erro.pack(pady=5)
        
        # Versão
        versao = ttk.Label(frame_login, text="v1.0.0", font=('Helvetica', 8))
        versao.pack(pady=5)
        
        # Configurar evento de tecla Enter
        self.entry_email.bind("<Return>", lambda e: self.entry_senha.focus())
        self.entry_senha.bind("<Return>", lambda e: self.fazer_login())

    # Adicionar também as configurações adicionais para os widgets Text:

    # Este código deve ser adicionado em todas as funções que criam widgets Text
    # Como exemplo, adicione isto antes de cada criação de widgets Text:

    def configurar_widget_text(self, text_widget):
        """Configura o estilo de um widget Text."""
        text_widget.config(bg="black",         # Fundo branco
                        fg="black",         # Texto preto
                        insertbackground="black",  # Cursor preto
                        selectbackground=self.cores['primaria'],  # Cor de seleção mantida
                        selectforeground="black")  # Texto na seleção em branco

    def aplicar_cores_widgets(self, parent):
        """Aplica as cores em todos os widgets filhos."""
        for child in parent.winfo_children():
            # Configura entry widgets
            if isinstance(child, ttk.Entry):
                child.configure(foreground='black')
            
            # Configura widgets Text
            elif isinstance(child, tk.Text):
                child.configure(foreground='black', insertbackground='black')
            
            # Processa widgets filhos recursivamente
            if child.winfo_children():
                self.aplicar_cores_widgets(child)


    # Adicione esta chamada antes de inserir o conteúdo em cada widget Text
    # Exemplo de uso:

    # self.text_mensagem = tk.Text(frame_individual, width=80, height=15)
    # self.configurar_widget_text(self.text_mensagem)
    # self.text_mensagem.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW, pady=(0, 10))

    
    def alterar_prefeitura(self, event=None):
        """Altera a prefeitura selecionada."""
        prefeitura = self.combo_prefeitura.get()
        if prefeitura == "São José":
            self.prefeitura_atual = 'sj'
        else:
            self.prefeitura_atual = 'floripa'
        
        # Atualiza as cores
        self.cores = CORES[self.prefeitura_atual]
        
        # Atualiza a interface
        self.criar_tela_login()

        # Aplica as cores pretas aos widgets de texto
        self.aplicar_cores_widgets(self.frame_principal)
    
    def fazer_login(self):
        """Valida o login e acessa o sistema."""
        email = self.entry_email.get().strip()
        senha = self.entry_senha.get()
        
        if not email or not senha:
            self.lbl_erro.config(text="Preencha todos os campos")
            return
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Verifica as credenciais
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            cursor.execute('''
            SELECT id, nome, nivel_acesso, prefeitura FROM usuarios 
            WHERE email = ? AND senha = ?
            ''', (email, senha_hash))
            
            usuario = cursor.fetchone()
            
            if usuario:
                user_id, nome, nivel_acesso, pref_usuario = usuario
                
                # Atualiza o último acesso
                cursor.execute('''
                UPDATE usuarios SET ultimo_acesso = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (user_id,))
                
                # Registra o login
                cursor.execute('''
                INSERT INTO logs (usuario_id, acao, descricao)
                VALUES (?, ?, ?)
                ''', (user_id, "LOGIN", f"Login realizado com sucesso"))
                
                conn.commit()
                
                # Armazena informações do usuário
                self.usuario_atual = {
                    'id': user_id,
                    'nome': nome,
                    'email': email,
                    'nivel_acesso': nivel_acesso,
                    'prefeitura': pref_usuario
                }
                
                # Ajusta a prefeitura se necessário
                if pref_usuario != self.prefeitura_atual:
                    self.prefeitura_atual = pref_usuario
                    self.cores = CORES[self.prefeitura_atual]
                
                # Vai para a tela principal
                self.criar_tela_principal()
            else:
                self.lbl_erro.config(text="E-mail ou senha incorretos")
                
                # Registra tentativa de login
                cursor.execute('''
                INSERT INTO logs (acao, descricao)
                VALUES (?, ?)
                ''', ("TENTATIVA_LOGIN", f"Tentativa falha para e-mail: {email}"))
                conn.commit()
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            self.lbl_erro.config(text="Erro ao conectar ao banco de dados")
    
    def criar_tela_principal(self):
        """Cria a tela principal do sistema."""
        # Limpa a tela
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        
        # Configura estilo
        style = ttk.Style()
        style.configure('TFrame', background=self.cores['fundo'])
        style.configure('TLabel', background=self.cores['fundo'], foreground=self.cores['texto'])
        style.configure('TButton', background=self.cores['primaria'], foreground='black')
        style.configure('TNotebook', background=self.cores['fundo'])
        style.configure('TNotebook.Tab', background=self.cores['secundaria'], 
                        foreground=self.cores['texto'], padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', self.cores['primaria'])],
                    foreground=[('selected', 'black')])
        
        # Cria o menu superior
        self.criar_menu_superior()
        
        # Cria o notebook (sistema de abas)
        self.notebook = ttk.Notebook(self.frame_principal)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cria as abas
        self.criar_aba_email_individual()
        self.criar_aba_email_massa()
        self.criar_aba_agendamento()
        self.criar_aba_templates()
        self.criar_aba_funcionarios()
        
        # Adiciona abas administrativas se o usuário tiver permissão
        if self.usuario_atual['nivel_acesso'] >= 2:
            self.criar_aba_usuarios()
        
        if self.usuario_atual['nivel_acesso'] >= 3:
            self.criar_aba_configuracoes()
            self.criar_aba_logs()
    
    def criar_menu_superior(self):
        """Cria o menu superior."""
        frame_menu = ttk.Frame(self.frame_principal, style='Menu.TFrame')
        frame_menu.pack(fill=tk.X, padx=0, pady=0)
        
        # Configura estilo
        style = ttk.Style()
        style.configure('Menu.TFrame', background=self.cores['primaria'])
        style.configure('Menu.TLabel', background=self.cores['primaria'], foreground='black')
        style.configure('Menu.TButton', background=self.cores['destaque'], foreground='black')
        
        # Logo
        try:
            if self.prefeitura_atual == 'sj':
                logo_path = os.path.join(RESOURCES_DIR, 'logo_sj_small.png')
            else:
                logo_path = os.path.join(RESOURCES_DIR, 'logo_floripa_small.png')
                
            # Se o arquivo não existir, cria um placeholder
            if not os.path.exists(logo_path):
                # Cria um diretório se não existir
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                
                # Cria uma imagem placeholder
                img = Image.new('RGB', (100, 50), color=(255, 255, 255))
                img.save(logo_path)
            
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((100, 50), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ttk.Label(frame_menu, image=logo_photo, style='Menu.TLabel')
            logo_label.image = logo_photo  # Mantém uma referência
            logo_label.pack(side=tk.LEFT, padx=10, pady=5)
        except Exception as e:
            logger.error(f"Erro ao carregar logo do menu: {e}")
            # Cria um label de texto como fallback
            logo_label = ttk.Label(frame_menu, text="Sistema E-mail", 
                                   style='Menu.TLabel', font=('Helvetica', 12, 'bold'))
            logo_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Informações do usuário
        lbl_usuario = ttk.Label(frame_menu, 
                              text=f"Usuário: {self.usuario_atual['nome']} | Prefeitura: {'São José' if self.prefeitura_atual == 'sj' else 'Florianópolis'}",
                              style='Menu.TLabel')
        lbl_usuario.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Botão Sair
        btn_sair = ttk.Button(frame_menu, text="Sair", command=self.fazer_logout, style='Menu.TButton')
        btn_sair.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Botão Ajuda
        btn_ajuda = ttk.Button(frame_menu, text="Ajuda", command=self.abrir_ajuda, style='Menu.TButton')
        btn_ajuda.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def criar_aba_email_individual(self):
        """Cria a aba para envio de e-mail individual."""
        frame_individual = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_individual, text="E-mail Individual")
        
        # Formulário de envio
        ttk.Label(frame_individual, text="Destinatário:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_destinatario = ttk.Frame(frame_individual)
        frame_destinatario.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        self.entry_destinatario = ttk.Entry(frame_destinatario, width=50)
        self.entry_destinatario.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_selecionar = ttk.Button(frame_destinatario, text="Selecionar", command=self.abrir_selecao_funcionarios)
        btn_selecionar.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Label(frame_individual, text="Assunto:", font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_assunto = ttk.Entry(frame_individual, width=80)
        self.entry_assunto.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        ttk.Label(frame_individual, text="Mensagem:", font=('Helvetica', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_botoes_editor = ttk.Frame(frame_individual)
        frame_botoes_editor.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
        
        btn_negrito = ttk.Button(frame_botoes_editor, text="N", width=3, command=lambda: self.formatar_texto("negrito"))
        btn_negrito.pack(side=tk.LEFT, padx=2)
        
        btn_italico = ttk.Button(frame_botoes_editor, text="I", width=3, command=lambda: self.formatar_texto("italico"))
        btn_italico.pack(side=tk.LEFT, padx=2)
        
        btn_sublinhado = ttk.Button(frame_botoes_editor, text="S", width=3, command=lambda: self.formatar_texto("sublinhado"))
        btn_sublinhado.pack(side=tk.LEFT, padx=2)
        
        btn_lista = ttk.Button(frame_botoes_editor, text="• Lista", width=6, command=lambda: self.formatar_texto("lista"))
        btn_lista.pack(side=tk.LEFT, padx=2)
        
        btn_link = ttk.Button(frame_botoes_editor, text="Link", width=6, command=lambda: self.formatar_texto("link"))
        btn_link.pack(side=tk.LEFT, padx=2)
        
        btn_imagem = ttk.Button(frame_botoes_editor, text="Imagem", width=8, command=lambda: self.formatar_texto("imagem"))
        btn_imagem.pack(side=tk.LEFT, padx=2)
        
        btn_template = ttk.Button(frame_botoes_editor, text="Usar Template", width=12, command=self.abrir_selecao_template)
        btn_template.pack(side=tk.LEFT, padx=2)
        
        self.text_mensagem = tk.Text(frame_individual, width=80, height=15)
        self.text_mensagem.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW, pady=(0, 10))
        
        # Adiciona barra de rolagem
        scrollbar = ttk.Scrollbar(frame_individual, orient=tk.VERTICAL, command=self.text_mensagem.yview)
        scrollbar.grid(row=6, column=2, sticky=tk.NS)
        self.text_mensagem.config(yscrollcommand=scrollbar.set)
        
        # Assinatura
        ttk.Label(frame_individual, text="Assinatura:", font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        self.assinatura_var = tk.BooleanVar(value=True)
        check_assinatura = ttk.Checkbutton(frame_individual, text="Incluir assinatura", variable=self.assinatura_var)
        check_assinatura.grid(row=7, column=1, sticky=tk.E, pady=(5, 0))
        
        # Anexos
        ttk.Label(frame_individual, text="Anexos:", font=('Helvetica', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_anexos = ttk.Frame(frame_individual)
        frame_anexos.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        self.lista_anexos = ttk.Treeview(frame_anexos, columns=('nome', 'tamanho'), show='headings', height=3)
        self.lista_anexos.heading('nome', text='Nome do arquivo')
        self.lista_anexos.heading('tamanho', text='Tamanho')
        self.lista_anexos.column('nome', width=300)
        self.lista_anexos.column('tamanho', width=100)
        self.lista_anexos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_anexos = ttk.Scrollbar(frame_anexos, orient=tk.VERTICAL, command=self.lista_anexos.yview)
        scrollbar_anexos.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_anexos.config(yscrollcommand=scrollbar_anexos.set)
        
        frame_botoes_anexos = ttk.Frame(frame_individual)
        frame_botoes_anexos.grid(row=10, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        self.anexos = []  # Lista para armazenar os caminhos dos arquivos anexados
        
        btn_adicionar_anexo = ttk.Button(frame_botoes_anexos, text="Adicionar Anexo", command=self.adicionar_anexo)
        btn_adicionar_anexo.pack(side=tk.LEFT, padx=2)
        
        btn_remover_anexo = ttk.Button(frame_botoes_anexos, text="Remover Anexo", command=self.remover_anexo)
        btn_remover_anexo.pack(side=tk.LEFT, padx=2)
        
        # Botões de ação
        frame_acoes = ttk.Frame(frame_individual)
        frame_acoes.grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        btn_enviar = ttk.Button(frame_acoes, text="Enviar E-mail", command=self.enviar_email_individual)
        btn_enviar.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar = ttk.Button(frame_acoes, text="Limpar Campos", command=self.limpar_campos_email)
        btn_limpar.pack(side=tk.RIGHT, padx=5)
        
        btn_previsualizar = ttk.Button(frame_acoes, text="Pré-visualizar", command=self.previsualizar_email)
        btn_previsualizar.pack(side=tk.RIGHT, padx=5)

        # Configurar a expansão da grid
        frame_individual.columnconfigure(0, weight=1)
        frame_individual.rowconfigure(6, weight=1)
    
    def criar_aba_email_massa(self):
        """Cria a aba para envio de e-mail em massa."""
        frame_massa = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_massa, text="E-mail em Massa")
        
        # Destinatários
        ttk.Label(frame_massa, text="Destinatários:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_destinatarios = ttk.Frame(frame_massa)
        frame_destinatarios.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Opções de seleção de destinatários
        self.opcao_destinatarios = tk.StringVar(value="grupo")
        
        rb_grupo = ttk.Radiobutton(frame_destinatarios, text="Grupo", variable=self.opcao_destinatarios, value="grupo", command=self.atualizar_opcao_destinatarios)
        rb_grupo.pack(side=tk.LEFT, padx=5)
        
        rb_departamento = ttk.Radiobutton(frame_destinatarios, text="Departamento", variable=self.opcao_destinatarios, value="departamento", command=self.atualizar_opcao_destinatarios)
        rb_departamento.pack(side=tk.LEFT, padx=5)
        
        rb_importar = ttk.Radiobutton(frame_destinatarios, text="Importar Lista", variable=self.opcao_destinatarios, value="importar", command=self.atualizar_opcao_destinatarios)
        rb_importar.pack(side=tk.LEFT, padx=5)
        
        rb_manual = ttk.Radiobutton(frame_destinatarios, text="Lista Manual", variable=self.opcao_destinatarios, value="manual", command=self.atualizar_opcao_destinatarios)
        rb_manual.pack(side=tk.LEFT, padx=5)
        
        # Frame para opções específicas de destinatários
        self.frame_opcao_destinatarios = ttk.Frame(frame_massa)
        self.frame_opcao_destinatarios.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Inicializa a exibição de opções de destinatários
        self.atualizar_opcao_destinatarios()
        
        # Preview de destinatários
        ttk.Label(frame_massa, text="Preview de destinatários:", font=('Helvetica', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_preview = ttk.Frame(frame_massa)
        frame_preview.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_preview = ttk.Treeview(frame_preview, columns=('email', 'nome', 'departamento'), show='headings', height=5)
        self.lista_preview.heading('email', text='E-mail')
        self.lista_preview.heading('nome', text='Nome')
        self.lista_preview.heading('departamento', text='Departamento')
        self.lista_preview.column('email', width=250)
        self.lista_preview.column('nome', width=200)
        self.lista_preview.column('departamento', width=200)
        self.lista_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_preview = ttk.Scrollbar(frame_preview, orient=tk.VERTICAL, command=self.lista_preview.yview)
        scrollbar_preview.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_preview.config(yscrollcommand=scrollbar_preview.set)
        
        # Contador de destinatários
        self.lbl_contador = ttk.Label(frame_massa, text="Total de destinatários: 0")
        self.lbl_contador.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # Opções de uso de template
        ttk.Label(frame_massa, text="Template de E-mail:", font=('Helvetica', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        
        frame_template = ttk.Frame(frame_massa)
        frame_template.grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.usar_template = tk.BooleanVar(value=False)
        check_template = ttk.Checkbutton(frame_template, text="Usar template", variable=self.usar_template, command=self.atualizar_template)
        check_template.pack(side=tk.LEFT)
        
        self.combo_template = ttk.Combobox(frame_template, width=50, state="readonly")
        self.combo_template.pack(side=tk.LEFT, padx=5)
        self.combo_template.bind("<<ComboboxSelected>>", self.selecionar_template)
        
        btn_visualizar_template = ttk.Button(frame_template, text="Visualizar", command=self.visualizar_template)
        btn_visualizar_template.pack(side=tk.LEFT, padx=5)
        
        # Carrega os templates disponíveis
        self.carregar_templates_combo()
        
        # Formulário de e-mail
        ttk.Label(frame_massa, text="Assunto:", font=('Helvetica', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_assunto_massa = ttk.Entry(frame_massa, width=80)
        self.entry_assunto_massa.grid(row=9, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        ttk.Label(frame_massa, text="Mensagem:", font=('Helvetica', 10, 'bold')).grid(row=10, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_botoes_editor_massa = ttk.Frame(frame_massa)
        frame_botoes_editor_massa.grid(row=11, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))
        
        btn_negrito = ttk.Button(frame_botoes_editor_massa, text="N", width=3, command=lambda: self.formatar_texto_massa("negrito"))
        btn_negrito.pack(side=tk.LEFT, padx=2)
        
        btn_italico = ttk.Button(frame_botoes_editor_massa, text="I", width=3, command=lambda: self.formatar_texto_massa("italico"))
        btn_italico.pack(side=tk.LEFT, padx=2)
        
        btn_sublinhado = ttk.Button(frame_botoes_editor_massa, text="S", width=3, command=lambda: self.formatar_texto_massa("sublinhado"))
        btn_sublinhado.pack(side=tk.LEFT, padx=2)
        
        btn_lista = ttk.Button(frame_botoes_editor_massa, text="• Lista", width=6, command=lambda: self.formatar_texto_massa("lista"))
        btn_lista.pack(side=tk.LEFT, padx=2)
        
        btn_link = ttk.Button(frame_botoes_editor_massa, text="Link", width=6, command=lambda: self.formatar_texto_massa("link"))
        btn_link.pack(side=tk.LEFT, padx=2)
        
        btn_imagem = ttk.Button(frame_botoes_editor_massa, text="Imagem", width=8, command=lambda: self.formatar_texto_massa("imagem"))
        btn_imagem.pack(side=tk.LEFT, padx=2)
        
        btn_variaveis = ttk.Button(frame_botoes_editor_massa, text="Variáveis", width=8, command=self.inserir_variaveis)
        btn_variaveis.pack(side=tk.LEFT, padx=2)
        
        self.text_mensagem_massa = tk.Text(frame_massa, width=80, height=15)
        self.text_mensagem_massa.grid(row=12, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        # Adiciona barra de rolagem
        scrollbar_massa = ttk.Scrollbar(frame_massa, orient=tk.VERTICAL, command=self.text_mensagem_massa.yview)
        scrollbar_massa.grid(row=12, column=3, sticky=tk.NS)
        self.text_mensagem_massa.config(yscrollcommand=scrollbar_massa.set)
        
        # Assinatura
        ttk.Label(frame_massa, text="Assinatura:", font=('Helvetica', 10, 'bold')).grid(row=13, column=0, sticky=tk.W, pady=(5, 0))
        self.assinatura_massa_var = tk.BooleanVar(value=True)
        check_assinatura_massa = ttk.Checkbutton(frame_massa, text="Incluir assinatura", variable=self.assinatura_massa_var)
        check_assinatura_massa.grid(row=13, column=1, sticky=tk.W, pady=(5, 0))
        
        # Anexos
        ttk.Label(frame_massa, text="Anexos:", font=('Helvetica', 10, 'bold')).grid(row=14, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_anexos_massa = ttk.Frame(frame_massa)
        frame_anexos_massa.grid(row=15, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.lista_anexos_massa = ttk.Treeview(frame_anexos_massa, columns=('nome', 'tamanho'), show='headings', height=3)
        self.lista_anexos_massa.heading('nome', text='Nome do arquivo')
        self.lista_anexos_massa.heading('tamanho', text='Tamanho')
        self.lista_anexos_massa.column('nome', width=300)
        self.lista_anexos_massa.column('tamanho', width=100)
        self.lista_anexos_massa.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_anexos_massa = ttk.Scrollbar(frame_anexos_massa, orient=tk.VERTICAL, command=self.lista_anexos_massa.yview)
        scrollbar_anexos_massa.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_anexos_massa.config(yscrollcommand=scrollbar_anexos_massa.set)
        
        frame_botoes_anexos_massa = ttk.Frame(frame_massa)
        frame_botoes_anexos_massa.grid(row=16, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.anexos_massa = []  # Lista para armazenar os caminhos dos arquivos anexados
        
        btn_adicionar_anexo_massa = ttk.Button(frame_botoes_anexos_massa, text="Adicionar Anexo", command=self.adicionar_anexo_massa)
        btn_adicionar_anexo_massa.pack(side=tk.LEFT, padx=2)
        
        btn_remover_anexo_massa = ttk.Button(frame_botoes_anexos_massa, text="Remover Anexo", command=self.remover_anexo_massa)
        btn_remover_anexo_massa.pack(side=tk.LEFT, padx=2)
        
        # Opções de envio
        frame_opcoes_envio = ttk.LabelFrame(frame_massa, text="Opções de Envio", padding=10)
        frame_opcoes_envio.grid(row=17, column=0, columnspan=3, sticky=tk.EW, pady=(10, 10))
        
        # Limite de e-mails por hora
        ttk.Label(frame_opcoes_envio, text="Limite de e-mails por hora:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.limite_emails_var = tk.StringVar(value="500")
        self.entry_limite = ttk.Entry(frame_opcoes_envio, width=10, textvariable=self.limite_emails_var)
        self.entry_limite.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Intervalo entre e-mails
        ttk.Label(frame_opcoes_envio, text="Intervalo entre e-mails (segundos):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.intervalo_emails_var = tk.StringVar(value="5")
        self.entry_intervalo = ttk.Entry(frame_opcoes_envio, width=10, textvariable=self.intervalo_emails_var)
        self.entry_intervalo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Botões de ação
        frame_acoes_massa = ttk.Frame(frame_massa)
        frame_acoes_massa.grid(row=18, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_enviar_massa = ttk.Button(frame_acoes_massa, text="Enviar E-mails", command=self.enviar_emails_massa)
        btn_enviar_massa.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_massa = ttk.Button(frame_acoes_massa, text="Limpar Campos", command=self.limpar_campos_massa)
        btn_limpar_massa.pack(side=tk.RIGHT, padx=5)
        
        btn_previsualizar_massa = ttk.Button(frame_acoes_massa, text="Pré-visualizar", command=self.previsualizar_email_massa)
        btn_previsualizar_massa.pack(side=tk.RIGHT, padx=5)
        
        # Configurar a expansão da grid
        frame_massa.columnconfigure(0, weight=1)
        frame_massa.rowconfigure(12, weight=1)
    
    def criar_aba_agendamento(self):
        """Cria a aba para agendamento de e-mails."""
        frame_agendamento = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_agendamento, text="Agendamento")
        
        # Painel de e-mails agendados
        ttk.Label(frame_agendamento, text="E-mails Agendados:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_lista_agendados = ttk.Frame(frame_agendamento)
        frame_lista_agendados.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_agendados = ttk.Treeview(frame_lista_agendados, 
                                          columns=('id', 'assunto', 'destinatarios', 'data', 'recorrencia', 'status'),
                                          show='headings', height=5)
        self.lista_agendados.heading('id', text='ID')
        self.lista_agendados.heading('assunto', text='Assunto')
        self.lista_agendados.heading('destinatarios', text='Destinatários')
        self.lista_agendados.heading('data', text='Data/Hora')
        self.lista_agendados.heading('recorrencia', text='Recorrência')
        self.lista_agendados.heading('status', text='Status')
        
        self.lista_agendados.column('id', width=50)
        self.lista_agendados.column('assunto', width=200)
        self.lista_agendados.column('destinatarios', width=150)
        self.lista_agendados.column('data', width=150)
        self.lista_agendados.column('recorrencia', width=100)
        self.lista_agendados.column('status', width=100)
        
        self.lista_agendados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_agendados = ttk.Scrollbar(frame_lista_agendados, orient=tk.VERTICAL, command=self.lista_agendados.yview)
        scrollbar_agendados.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_agendados.config(yscrollcommand=scrollbar_agendados.set)
        
        # Botões para gerenciar agendamentos
        frame_botoes_agendados = ttk.Frame(frame_agendamento)
        frame_botoes_agendados.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_visualizar = ttk.Button(frame_botoes_agendados, text="Visualizar Detalhes", command=self.visualizar_agendamento)
        btn_visualizar.pack(side=tk.LEFT, padx=2)
        
        btn_cancelar = ttk.Button(frame_botoes_agendados, text="Cancelar Agendamento", command=self.cancelar_agendamento)
        btn_cancelar.pack(side=tk.LEFT, padx=2)
        
        btn_editar = ttk.Button(frame_botoes_agendados, text="Editar Agendamento", command=self.editar_agendamento)
        btn_editar.pack(side=tk.LEFT, padx=2)
        
        btn_atualizar = ttk.Button(frame_botoes_agendados, text="Atualizar Lista", command=self.atualizar_lista_agendamentos)
        btn_atualizar.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(frame_agendamento, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Formulário de novo agendamento
        ttk.Label(frame_agendamento, text="Novo Agendamento:", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Destinatários
        ttk.Label(frame_agendamento, text="Destinatários:", font=('Helvetica', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_destinatarios_agendamento = ttk.Frame(frame_agendamento)
        frame_destinatarios_agendamento.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Opções de seleção de destinatários
        self.opcao_destinatarios_agendamento = tk.StringVar(value="grupo")
        
        rb_grupo_agendamento = ttk.Radiobutton(frame_destinatarios_agendamento, text="Grupo", 
                                            variable=self.opcao_destinatarios_agendamento, 
                                            value="grupo", 
                                            command=self.atualizar_opcao_destinatarios_agendamento)
        rb_grupo_agendamento.pack(side=tk.LEFT, padx=5)
        
        rb_departamento_agendamento = ttk.Radiobutton(frame_destinatarios_agendamento, text="Departamento", 
                                                  variable=self.opcao_destinatarios_agendamento, 
                                                  value="departamento", 
                                                  command=self.atualizar_opcao_destinatarios_agendamento)
        rb_departamento_agendamento.pack(side=tk.LEFT, padx=5)
        
        rb_importar_agendamento = ttk.Radiobutton(frame_destinatarios_agendamento, text="Importar Lista", 
                                             variable=self.opcao_destinatarios_agendamento, 
                                             value="importar", 
                                             command=self.atualizar_opcao_destinatarios_agendamento)
        rb_importar_agendamento.pack(side=tk.LEFT, padx=5)
        
        rb_manual_agendamento = ttk.Radiobutton(frame_destinatarios_agendamento, text="Lista Manual", 
                                           variable=self.opcao_destinatarios_agendamento, 
                                           value="manual", 
                                           command=self.atualizar_opcao_destinatarios_agendamento)
        rb_manual_agendamento.pack(side=tk.LEFT, padx=5)
        
        # Frame para opções específicas de destinatários
        self.frame_opcao_destinatarios_agendamento = ttk.Frame(frame_agendamento)
        self.frame_opcao_destinatarios_agendamento.grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Inicializa a exibição de opções de destinatários
        self.atualizar_opcao_destinatarios_agendamento()
        
        # Preview de destinatários
        ttk.Label(frame_agendamento, text="Preview de destinatários:", font=('Helvetica', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_preview_agendamento = ttk.Frame(frame_agendamento)
        frame_preview_agendamento.grid(row=9, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_preview_agendamento = ttk.Treeview(frame_preview_agendamento, 
                                                   columns=('email', 'nome', 'departamento'), 
                                                   show='headings', height=3)
        self.lista_preview_agendamento.heading('email', text='E-mail')
        self.lista_preview_agendamento.heading('nome', text='Nome')
        self.lista_preview_agendamento.heading('departamento', text='Departamento')
        self.lista_preview_agendamento.column('email', width=250)
        self.lista_preview_agendamento.column('nome', width=200)
        self.lista_preview_agendamento.column('departamento', width=200)
        self.lista_preview_agendamento.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_preview_agendamento = ttk.Scrollbar(frame_preview_agendamento, orient=tk.VERTICAL, 
                                                 command=self.lista_preview_agendamento.yview)
        scrollbar_preview_agendamento.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_preview_agendamento.config(yscrollcommand=scrollbar_preview_agendamento.set)
        
        # Contador de destinatários
        self.lbl_contador_agendamento = ttk.Label(frame_agendamento, text="Total de destinatários: 0")
        self.lbl_contador_agendamento.grid(row=10, column=0, sticky=tk.W, pady=5)
        
        # Opções de agendamento
        frame_opcoes_agendamento = ttk.LabelFrame(frame_agendamento, text="Opções de Agendamento", padding=10)
        frame_opcoes_agendamento.grid(row=11, column=0, columnspan=3, sticky=tk.EW, pady=(10, 10))
        
        # Data e hora
        ttk.Label(frame_opcoes_agendamento, text="Data:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.data_agendamento = DateEntry(frame_opcoes_agendamento, width=12, background=self.cores['primaria'],
                                      foreground='black', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.data_agendamento.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_opcoes_agendamento, text="Hora:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        frame_hora = ttk.Frame(frame_opcoes_agendamento)
        frame_hora.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        self.hora_var = tk.StringVar(value="08")
        self.minuto_var = tk.StringVar(value="00")
        
        self.spin_hora = ttk.Spinbox(frame_hora, from_=0, to=23, width=3, format="%02.0f", textvariable=self.hora_var)
        self.spin_hora.pack(side=tk.LEFT)
        
        ttk.Label(frame_hora, text=":").pack(side=tk.LEFT)
        
        self.spin_minuto = ttk.Spinbox(frame_hora, from_=0, to=59, width=3, format="%02.0f", textvariable=self.minuto_var)
        self.spin_minuto.pack(side=tk.LEFT)
        
        # Recorrência
        ttk.Label(frame_opcoes_agendamento, text="Recorrência:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.recorrencia_var = tk.StringVar(value="nenhuma")
        combo_recorrencia = ttk.Combobox(frame_opcoes_agendamento, textvariable=self.recorrencia_var, 
                                       values=["Nenhuma", "Diária", "Semanal", "Mensal"], 
                                       state="readonly", width=15)
        combo_recorrencia.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        combo_recorrencia.bind("<<ComboboxSelected>>", self.atualizar_recorrencia)
        
        # Opções específicas de recorrência (dia da semana, dia do mês)
        self.frame_recorrencia = ttk.Frame(frame_opcoes_agendamento)
        self.frame_recorrencia.grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Template
        ttk.Label(frame_agendamento, text="Template de E-mail:", font=('Helvetica', 10, 'bold')).grid(row=12, column=0, sticky=tk.W, pady=(10, 0))
        
        frame_template_agendamento = ttk.Frame(frame_agendamento)
        frame_template_agendamento.grid(row=13, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.usar_template_agendamento = tk.BooleanVar(value=False)
        check_template_agendamento = ttk.Checkbutton(frame_template_agendamento, text="Usar template", variable=self.usar_template_agendamento, command=self.atualizar_template_agendamento)
        check_template_agendamento.pack(side=tk.LEFT)
        
        self.combo_template_agendamento = ttk.Combobox(frame_template_agendamento, width=50, state="readonly")
        self.combo_template_agendamento.pack(side=tk.LEFT, padx=5)
        self.combo_template_agendamento.bind("<<ComboboxSelected>>", self.selecionar_template_agendamento)
        
        btn_visualizar_template_agendamento = ttk.Button(frame_template_agendamento, text="Visualizar", 
                                                      command=self.visualizar_template_agendamento)
        btn_visualizar_template_agendamento.pack(side=tk.LEFT, padx=5)
        
        # Carrega os templates disponíveis
        self.carregar_templates_combo_agendamento()
        
        # Formulário de e-mail
        ttk.Label(frame_agendamento, text="Assunto:", font=('Helvetica', 10, 'bold')).grid(row=14, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_assunto_agendamento = ttk.Entry(frame_agendamento, width=80)
        self.entry_assunto_agendamento.grid(row=15, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        ttk.Label(frame_agendamento, text="Mensagem:", font=('Helvetica', 10, 'bold')).grid(row=16, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_botoes_editor_agendamento = ttk.Frame(frame_agendamento)
        frame_botoes_editor_agendamento.grid(row=17, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))
        
        btn_negrito = ttk.Button(frame_botoes_editor_agendamento, text="N", width=3, 
                              command=lambda: self.formatar_texto_agendamento("negrito"))
        btn_negrito.pack(side=tk.LEFT, padx=2)
        
        btn_italico = ttk.Button(frame_botoes_editor_agendamento, text="I", width=3, 
                              command=lambda: self.formatar_texto_agendamento("italico"))
        btn_italico.pack(side=tk.LEFT, padx=2)
        
        btn_sublinhado = ttk.Button(frame_botoes_editor_agendamento, text="S", width=3, 
                                 command=lambda: self.formatar_texto_agendamento("sublinhado"))
        btn_sublinhado.pack(side=tk.LEFT, padx=2)
        
        btn_lista = ttk.Button(frame_botoes_editor_agendamento, text="• Lista", width=6, 
                            command=lambda: self.formatar_texto_agendamento("lista"))
        btn_lista.pack(side=tk.LEFT, padx=2)
        
        btn_link = ttk.Button(frame_botoes_editor_agendamento, text="Link", width=6, 
                           command=lambda: self.formatar_texto_agendamento("link"))
        btn_link.pack(side=tk.LEFT, padx=2)
        
        btn_imagem = ttk.Button(frame_botoes_editor_agendamento, text="Imagem", width=8, 
                             command=lambda: self.formatar_texto_agendamento("imagem"))
        btn_imagem.pack(side=tk.LEFT, padx=2)
        
        btn_variaveis = ttk.Button(frame_botoes_editor_agendamento, text="Variáveis", width=8, 
                                command=self.inserir_variaveis_agendamento)
        btn_variaveis.pack(side=tk.LEFT, padx=2)
        
        self.text_mensagem_agendamento = tk.Text(frame_agendamento, width=80, height=10)
        self.text_mensagem_agendamento.grid(row=18, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        # Adiciona barra de rolagem
        scrollbar_agendamento = ttk.Scrollbar(frame_agendamento, orient=tk.VERTICAL, 
                                          command=self.text_mensagem_agendamento.yview)
        scrollbar_agendamento.grid(row=18, column=3, sticky=tk.NS)
        self.text_mensagem_agendamento.config(yscrollcommand=scrollbar_agendamento.set)
        
        # Assinatura
        ttk.Label(frame_agendamento, text="Assinatura:", font=('Helvetica', 10, 'bold')).grid(row=19, column=0, sticky=tk.W, pady=(5, 0))
        self.assinatura_agendamento_var = tk.BooleanVar(value=True)
        check_assinatura_agendamento = ttk.Checkbutton(frame_agendamento, text="Incluir assinatura", 
                                                    variable=self.assinatura_agendamento_var)
        check_assinatura_agendamento.grid(row=19, column=1, sticky=tk.W, pady=(5, 0))
        
        # Anexos
        ttk.Label(frame_agendamento, text="Anexos:", font=('Helvetica', 10, 'bold')).grid(row=20, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_anexos_agendamento = ttk.Frame(frame_agendamento)
        frame_anexos_agendamento.grid(row=21, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.lista_anexos_agendamento = ttk.Treeview(frame_anexos_agendamento, 
                                                 columns=('nome', 'tamanho'), 
                                                 show='headings', height=3)
        self.lista_anexos_agendamento.heading('nome', text='Nome do arquivo')
        self.lista_anexos_agendamento.heading('tamanho', text='Tamanho')
        self.lista_anexos_agendamento.column('nome', width=300)
        self.lista_anexos_agendamento.column('tamanho', width=100)
        self.lista_anexos_agendamento.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_anexos_agendamento = ttk.Scrollbar(frame_anexos_agendamento, orient=tk.VERTICAL, 
                                                 command=self.lista_anexos_agendamento.yview)
        scrollbar_anexos_agendamento.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_anexos_agendamento.config(yscrollcommand=scrollbar_anexos_agendamento.set)
        
        frame_botoes_anexos_agendamento = ttk.Frame(frame_agendamento)
        frame_botoes_anexos_agendamento.grid(row=22, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        self.anexos_agendamento = []  # Lista para armazenar os caminhos dos arquivos anexados
        
        btn_adicionar_anexo_agendamento = ttk.Button(frame_botoes_anexos_agendamento, 
                                                 text="Adicionar Anexo", 
                                                 command=self.adicionar_anexo_agendamento)
        btn_adicionar_anexo_agendamento.pack(side=tk.LEFT, padx=2)
        
        btn_remover_anexo_agendamento = ttk.Button(frame_botoes_anexos_agendamento, 
                                              text="Remover Anexo", 
                                              command=self.remover_anexo_agendamento)
        btn_remover_anexo_agendamento.pack(side=tk.LEFT, padx=2)
        
        # Botões de ação
        frame_acoes_agendamento = ttk.Frame(frame_agendamento)
        frame_acoes_agendamento.grid(row=23, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_agendar = ttk.Button(frame_acoes_agendamento, text="Agendar E-mail", command=self.agendar_email)
        btn_agendar.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_agendamento = ttk.Button(frame_acoes_agendamento, text="Limpar Campos", 
                                        command=self.limpar_campos_agendamento)
        btn_limpar_agendamento.pack(side=tk.RIGHT, padx=5)
        
        btn_previsualizar_agendamento = ttk.Button(frame_acoes_agendamento, text="Pré-visualizar", 
                                               command=self.previsualizar_email_agendamento)
        btn_previsualizar_agendamento.pack(side=tk.RIGHT, padx=5)
        
        # Atualiza a lista de e-mails agendados
        self.atualizar_lista_agendamentos()
        
        # Configurar a expansão da grid
        frame_agendamento.columnconfigure(0, weight=1)
        frame_agendamento.rowconfigure(18, weight=1)
    
    def criar_aba_templates(self):
        """Cria a aba para gerenciamento de templates de e-mail."""
        frame_templates = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_templates, text="Templates")
        
        # Lista de templates
        ttk.Label(frame_templates, text="Templates Disponíveis:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_lista_templates = ttk.Frame(frame_templates)
        frame_lista_templates.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_templates = ttk.Treeview(frame_lista_templates, 
                                         columns=('id', 'nome', 'assunto', 'departamento', 'data'),
                                         show='headings', height=5)
        self.lista_templates.heading('id', text='ID')
        self.lista_templates.heading('nome', text='Nome')
        self.lista_templates.heading('assunto', text='Assunto')
        self.lista_templates.heading('departamento', text='Departamento')
        self.lista_templates.heading('data', text='Última Atualização')
        
        self.lista_templates.column('id', width=50)
        self.lista_templates.column('nome', width=200)
        self.lista_templates.column('assunto', width=200)
        self.lista_templates.column('departamento', width=150)
        self.lista_templates.column('data', width=150)
        
        self.lista_templates.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_templates = ttk.Scrollbar(frame_lista_templates, orient=tk.VERTICAL, command=self.lista_templates.yview)
        scrollbar_templates.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_templates.config(yscrollcommand=scrollbar_templates.set)
        
        # Botões para gerenciar templates
        frame_botoes_templates = ttk.Frame(frame_templates)
        frame_botoes_templates.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_visualizar_template = ttk.Button(frame_botoes_templates, text="Visualizar Template", 
                                       command=self.visualizar_template_selecionado)
        btn_visualizar_template.pack(side=tk.LEFT, padx=2)
        
        btn_excluir_template = ttk.Button(frame_botoes_templates, text="Excluir Template", 
                                    command=self.excluir_template)
        btn_excluir_template.pack(side=tk.LEFT, padx=2)
        
        btn_editar_template = ttk.Button(frame_botoes_templates, text="Editar Template", 
                                   command=self.editar_template)
        btn_editar_template.pack(side=tk.LEFT, padx=2)
        
        btn_duplicar_template = ttk.Button(frame_botoes_templates, text="Duplicar Template", 
                                     command=self.duplicar_template)
        btn_duplicar_template.pack(side=tk.LEFT, padx=2)
        
        btn_atualizar_templates = ttk.Button(frame_botoes_templates, text="Atualizar Lista", 
                                        command=self.atualizar_lista_templates)
        btn_atualizar_templates.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(frame_templates, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Formulário de novo template
        ttk.Label(frame_templates, text="Novo Template:", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Nome do template
        ttk.Label(frame_templates, text="Nome do Template:", font=('Helvetica', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_nome_template = ttk.Entry(frame_templates, width=80)
        self.entry_nome_template.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Departamento
        ttk.Label(frame_templates, text="Departamento:", font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_departamento_template = ttk.Combobox(frame_templates, width=50)
        self.combo_departamento_template.grid(row=8, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Carregar departamentos
        self.carregar_departamentos()
        
        # Assunto
        ttk.Label(frame_templates, text="Assunto:", font=('Helvetica', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_assunto_template = ttk.Entry(frame_templates, width=80)
        self.entry_assunto_template.grid(row=10, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        # Conteúdo
        ttk.Label(frame_templates, text="Conteúdo:", font=('Helvetica', 10, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_botoes_editor_template = ttk.Frame(frame_templates)
        frame_botoes_editor_template.grid(row=12, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))
        
        btn_negrito = ttk.Button(frame_botoes_editor_template, text="N", width=3, 
                              command=lambda: self.formatar_texto_template("negrito"))
        btn_negrito.pack(side=tk.LEFT, padx=2)
        
        btn_italico = ttk.Button(frame_botoes_editor_template, text="I", width=3, 
                              command=lambda: self.formatar_texto_template("italico"))
        btn_italico.pack(side=tk.LEFT, padx=2)
        
        btn_sublinhado = ttk.Button(frame_botoes_editor_template, text="S", width=3, 
                                 command=lambda: self.formatar_texto_template("sublinhado"))
        btn_sublinhado.pack(side=tk.LEFT, padx=2)
        
        btn_lista = ttk.Button(frame_botoes_editor_template, text="• Lista", width=6, 
                            command=lambda: self.formatar_texto_template("lista"))
        btn_lista.pack(side=tk.LEFT, padx=2)
        
        btn_link = ttk.Button(frame_botoes_editor_template, text="Link", width=6, 
                           command=lambda: self.formatar_texto_template("link"))
        btn_link.pack(side=tk.LEFT, padx=2)
        
        btn_imagem = ttk.Button(frame_botoes_editor_template, text="Imagem", width=8, 
                             command=lambda: self.formatar_texto_template("imagem"))
        btn_imagem.pack(side=tk.LEFT, padx=2)
        
        btn_variaveis = ttk.Button(frame_botoes_editor_template, text="Variáveis", width=8, 
                                command=self.inserir_variaveis_template)
        btn_variaveis.pack(side=tk.LEFT, padx=2)
        
        self.text_conteudo_template = tk.Text(frame_templates, width=80, height=15)
        self.text_conteudo_template.grid(row=13, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        # Adiciona barra de rolagem
        scrollbar_template = ttk.Scrollbar(frame_templates, orient=tk.VERTICAL, 
                                       command=self.text_conteudo_template.yview)
        scrollbar_template.grid(row=13, column=3, sticky=tk.NS)
        self.text_conteudo_template.config(yscrollcommand=scrollbar_template.set)
        
        # Botões de ação
        frame_acoes_template = ttk.Frame(frame_templates)
        frame_acoes_template.grid(row=14, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_salvar_template = ttk.Button(frame_acoes_template, text="Salvar Template", 
                                     command=self.salvar_template)
        btn_salvar_template.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_template = ttk.Button(frame_acoes_template, text="Limpar Campos", 
                                     command=self.limpar_campos_template)
        btn_limpar_template.pack(side=tk.RIGHT, padx=5)
        
        btn_previsualizar_template = ttk.Button(frame_acoes_template, text="Pré-visualizar", 
                                           command=self.previsualizar_template)
        btn_previsualizar_template.pack(side=tk.RIGHT, padx=5)
        
        # Atualiza a lista de templates
        self.atualizar_lista_templates()
        
        # Configurar a expansão da grid
        frame_templates.columnconfigure(0, weight=1)
        frame_templates.rowconfigure(13, weight=1)
    
    def criar_aba_funcionarios(self):
        """Cria a aba para gerenciamento de funcionários."""
        frame_funcionarios = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_funcionarios, text="Funcionários")
        
        # Lista de funcionários
        ttk.Label(frame_funcionarios, text="Funcionários Cadastrados:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        # Barra de busca
        frame_busca = ttk.Frame(frame_funcionarios)
        frame_busca.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))
        
        ttk.Label(frame_busca, text="Buscar:").pack(side=tk.LEFT, padx=5)
        self.entry_busca_funcionario = ttk.Entry(frame_busca, width=30)
        self.entry_busca_funcionario.pack(side=tk.LEFT, padx=5)
        self.entry_busca_funcionario.bind("<KeyRelease>", self.buscar_funcionario)
        
        self.filtro_funcionario = tk.StringVar(value="nome")
        combo_filtro = ttk.Combobox(frame_busca, textvariable=self.filtro_funcionario, 
                                  values=["Nome", "E-mail", "Cargo", "Departamento"], 
                                  state="readonly", width=15)
        combo_filtro.pack(side=tk.LEFT, padx=5)
        combo_filtro.current(0)
        
        btn_buscar = ttk.Button(frame_busca, text="Buscar", command=self.buscar_funcionario)
        btn_buscar.pack(side=tk.LEFT, padx=5)
        
        # Lista de funcionários
        frame_lista_funcionarios = ttk.Frame(frame_funcionarios)
        frame_lista_funcionarios.grid(row=2, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_funcionarios = ttk.Treeview(frame_lista_funcionarios, 
                                           columns=('id', 'nome', 'email', 'cargo', 'departamento', 'prefeitura', 'status'),
                                           show='headings', height=8)
        self.lista_funcionarios.heading('id', text='ID')
        self.lista_funcionarios.heading('nome', text='Nome')
        self.lista_funcionarios.heading('email', text='E-mail')
        self.lista_funcionarios.heading('cargo', text='Cargo')
        self.lista_funcionarios.heading('departamento', text='Departamento')
        self.lista_funcionarios.heading('prefeitura', text='Prefeitura')
        self.lista_funcionarios.heading('status', text='Status')
        
        self.lista_funcionarios.column('id', width=50)
        self.lista_funcionarios.column('nome', width=200)
        self.lista_funcionarios.column('email', width=200)
        self.lista_funcionarios.column('cargo', width=150)
        self.lista_funcionarios.column('departamento', width=150)
        self.lista_funcionarios.column('prefeitura', width=100)
        self.lista_funcionarios.column('status', width=100)
        
        self.lista_funcionarios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_funcionarios = ttk.Scrollbar(frame_lista_funcionarios, orient=tk.VERTICAL, 
                                          command=self.lista_funcionarios.yview)
        scrollbar_funcionarios.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_funcionarios.config(yscrollcommand=scrollbar_funcionarios.set)
        
        # Botões para gerenciar funcionários
        frame_botoes_funcionarios = ttk.Frame(frame_funcionarios)
        frame_botoes_funcionarios.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_adicionar_grupo = ttk.Button(frame_botoes_funcionarios, text="Adicionar a Grupo", 
                                     command=self.adicionar_funcionario_grupo)
        btn_adicionar_grupo.pack(side=tk.LEFT, padx=2)
        
        btn_excluir_funcionario = ttk.Button(frame_botoes_funcionarios, text="Excluir Funcionário", 
                                        command=self.excluir_funcionario)
        btn_excluir_funcionario.pack(side=tk.LEFT, padx=2)
        
        btn_editar_funcionario = ttk.Button(frame_botoes_funcionarios, text="Editar Funcionário", 
                                       command=self.editar_funcionario)
        btn_editar_funcionario.pack(side=tk.LEFT, padx=2)
        
        btn_ativar_funcionario = ttk.Button(frame_botoes_funcionarios, text="Ativar/Desativar", 
                                       command=self.alternar_status_funcionario)
        btn_ativar_funcionario.pack(side=tk.LEFT, padx=2)
        
        btn_atualizar_funcionarios = ttk.Button(frame_botoes_funcionarios, text="Atualizar Lista", 
                                           command=self.atualizar_lista_funcionarios)
        btn_atualizar_funcionarios.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(frame_funcionarios, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Painel de importação/exportação
        frame_importacao = ttk.LabelFrame(frame_funcionarios, text="Importar/Exportar Funcionários", padding=10)
        frame_importacao.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_importar_csv = ttk.Button(frame_importacao, text="Importar CSV/Excel", 
                                   command=self.importar_funcionarios)
        btn_importar_csv.grid(row=0, column=0, padx=5, pady=5)
        
        btn_exportar_csv = ttk.Button(frame_importacao, text="Exportar para CSV", 
                                   command=self.exportar_funcionarios_csv)
        btn_exportar_csv.grid(row=0, column=1, padx=5, pady=5)
        
        btn_exportar_excel = ttk.Button(frame_importacao, text="Exportar para Excel", 
                                     command=self.exportar_funcionarios_excel)
        btn_exportar_excel.grid(row=0, column=2, padx=5, pady=5)
        
        # Formulário de novo funcionário
        ttk.Label(frame_funcionarios, text="Novo Funcionário:", font=('Helvetica', 12, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        
        # Nome
        ttk.Label(frame_funcionarios, text="Nome:", font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_nome_funcionario = ttk.Entry(frame_funcionarios, width=50)
        self.entry_nome_funcionario.grid(row=7, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Email
        ttk.Label(frame_funcionarios, text="E-mail:", font=('Helvetica', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_email_funcionario = ttk.Entry(frame_funcionarios, width=50)
        self.entry_email_funcionario.grid(row=8, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Cargo
        ttk.Label(frame_funcionarios, text="Cargo:", font=('Helvetica', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_cargo_funcionario = ttk.Entry(frame_funcionarios, width=50)
        self.entry_cargo_funcionario.grid(row=9, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Departamento
        ttk.Label(frame_funcionarios, text="Departamento:", font=('Helvetica', 10, 'bold')).grid(row=10, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_departamento_funcionario = ttk.Combobox(frame_funcionarios, width=50)
        self.combo_departamento_funcionario.grid(row=10, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Telefone
        ttk.Label(frame_funcionarios, text="Telefone:", font=('Helvetica', 10, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_telefone_funcionario = ttk.Entry(frame_funcionarios, width=50)
        self.entry_telefone_funcionario.grid(row=11, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Prefeitura
        ttk.Label(frame_funcionarios, text="Prefeitura:", font=('Helvetica', 10, 'bold')).grid(row=12, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_prefeitura_funcionario = ttk.Combobox(frame_funcionarios, 
                                                     values=["São José", "Florianópolis"],
                                                     state="readonly", width=50)
        self.combo_prefeitura_funcionario.grid(row=12, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        self.combo_prefeitura_funcionario.current(0 if self.prefeitura_atual == 'sj' else 1)
        
        # Botões de ação
        frame_acoes_funcionario = ttk.Frame(frame_funcionarios)
        frame_acoes_funcionario.grid(row=13, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_salvar_funcionario = ttk.Button(frame_acoes_funcionario, text="Salvar Funcionário", 
                                       command=self.salvar_funcionario)
        btn_salvar_funcionario.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_funcionario = ttk.Button(frame_acoes_funcionario, text="Limpar Campos", 
                                       command=self.limpar_campos_funcionario)
        btn_limpar_funcionario.pack(side=tk.RIGHT, padx=5)
        
        # Carregar departamentos
        self.carregar_departamentos()
        
        # Atualiza a lista de funcionários
        self.atualizar_lista_funcionarios()
        
        # Configurar a expansão da grid
        frame_funcionarios.columnconfigure(1, weight=1)
        frame_funcionarios.rowconfigure(2, weight=1)
    
    def criar_aba_usuarios(self):
        """Cria a aba para gerenciamento de usuários do sistema."""
        frame_usuarios = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_usuarios, text="Usuários")
        
        # Lista de usuários
        ttk.Label(frame_usuarios, text="Usuários do Sistema:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_lista_usuarios = ttk.Frame(frame_usuarios)
        frame_lista_usuarios.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_usuarios = ttk.Treeview(frame_lista_usuarios, 
                                       columns=('id', 'nome', 'email', 'prefeitura', 'nivel', 'ultimo_acesso'),
                                       show='headings', height=8)
        self.lista_usuarios.heading('id', text='ID')
        self.lista_usuarios.heading('nome', text='Nome')
        self.lista_usuarios.heading('email', text='E-mail')
        self.lista_usuarios.heading('prefeitura', text='Prefeitura')
        self.lista_usuarios.heading('nivel', text='Nível de Acesso')
        self.lista_usuarios.heading('ultimo_acesso', text='Último Acesso')
        
        self.lista_usuarios.column('id', width=50)
        self.lista_usuarios.column('nome', width=200)
        self.lista_usuarios.column('email', width=200)
        self.lista_usuarios.column('prefeitura', width=100)
        self.lista_usuarios.column('nivel', width=100)
        self.lista_usuarios.column('ultimo_acesso', width=150)
        
        self.lista_usuarios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_usuarios = ttk.Scrollbar(frame_lista_usuarios, orient=tk.VERTICAL, command=self.lista_usuarios.yview)
        scrollbar_usuarios.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_usuarios.config(yscrollcommand=scrollbar_usuarios.set)
        
        # Botões para gerenciar usuários
        frame_botoes_usuarios = ttk.Frame(frame_usuarios)
        frame_botoes_usuarios.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_resetar_senha = ttk.Button(frame_botoes_usuarios, text="Resetar Senha", command=self.resetar_senha_usuario)
        btn_resetar_senha.pack(side=tk.LEFT, padx=2)
        
        btn_excluir_usuario = ttk.Button(frame_botoes_usuarios, text="Excluir Usuário", command=self.excluir_usuario)
        btn_excluir_usuario.pack(side=tk.LEFT, padx=2)
        
        btn_editar_usuario = ttk.Button(frame_botoes_usuarios, text="Editar Usuário", command=self.editar_usuario)
        btn_editar_usuario.pack(side=tk.LEFT, padx=2)
        
        btn_atualizar_usuarios = ttk.Button(frame_botoes_usuarios, text="Atualizar Lista", command=self.atualizar_lista_usuarios)
        btn_atualizar_usuarios.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(frame_usuarios, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Formulário de novo usuário
        ttk.Label(frame_usuarios, text="Novo Usuário:", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Nome
        ttk.Label(frame_usuarios, text="Nome:", font=('Helvetica', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_nome_usuario = ttk.Entry(frame_usuarios, width=50)
        self.entry_nome_usuario.grid(row=5, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Email
        ttk.Label(frame_usuarios, text="E-mail:", font=('Helvetica', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_email_usuario = ttk.Entry(frame_usuarios, width=50)
        self.entry_email_usuario.grid(row=6, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Senha
        ttk.Label(frame_usuarios, text="Senha:", font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_senha_usuario = ttk.Entry(frame_usuarios, width=50, show="*")
        self.entry_senha_usuario.grid(row=7, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Confirmar Senha
        ttk.Label(frame_usuarios, text="Confirmar Senha:", font=('Helvetica', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_confirmar_senha = ttk.Entry(frame_usuarios, width=50, show="*")
        self.entry_confirmar_senha.grid(row=8, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Cargo
        ttk.Label(frame_usuarios, text="Cargo:", font=('Helvetica', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_cargo_usuario = ttk.Entry(frame_usuarios, width=50)
        self.entry_cargo_usuario.grid(row=9, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Departamento
        ttk.Label(frame_usuarios, text="Departamento:", font=('Helvetica', 10, 'bold')).grid(row=10, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_departamento_usuario = ttk.Combobox(frame_usuarios, width=50)
        self.combo_departamento_usuario.grid(row=10, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Telefone
        ttk.Label(frame_usuarios, text="Telefone:", font=('Helvetica', 10, 'bold')).grid(row=11, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_telefone_usuario = ttk.Entry(frame_usuarios, width=50)
        self.entry_telefone_usuario.grid(row=11, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Prefeitura
        ttk.Label(frame_usuarios, text="Prefeitura:", font=('Helvetica', 10, 'bold')).grid(row=12, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_prefeitura_usuario = ttk.Combobox(frame_usuarios, 
                                                 values=["São José", "Florianópolis"],
                                                 state="readonly", width=50)
        self.combo_prefeitura_usuario.grid(row=12, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        self.combo_prefeitura_usuario.current(0 if self.prefeitura_atual == 'sj' else 1)
        
        # Nível de Acesso
        ttk.Label(frame_usuarios, text="Nível de Acesso:", font=('Helvetica', 10, 'bold')).grid(row=13, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_nivel_acesso = ttk.Combobox(frame_usuarios, 
                                          values=["Usuário", "Supervisor", "Administrador"],
                                          state="readonly", width=50)
        self.combo_nivel_acesso.grid(row=13, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        self.combo_nivel_acesso.current(0)
        
        # Botões de ação
        frame_acoes_usuario = ttk.Frame(frame_usuarios)
        frame_acoes_usuario.grid(row=14, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_salvar_usuario = ttk.Button(frame_acoes_usuario, text="Salvar Usuário", command=self.salvar_usuario)
        btn_salvar_usuario.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_usuario = ttk.Button(frame_acoes_usuario, text="Limpar Campos", command=self.limpar_campos_usuario)
        btn_limpar_usuario.pack(side=tk.RIGHT, padx=5)
        
        # Carregar departamentos
        self.carregar_departamentos()
        
        # Atualiza a lista de usuários
        self.atualizar_lista_usuarios()
        
        # Configurar a expansão da grid
        frame_usuarios.columnconfigure(1, weight=1)
        frame_usuarios.rowconfigure(1, weight=1)
    
    def criar_aba_configuracoes(self):
        """Cria a aba para configurações do sistema."""
        frame_configuracoes = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_configuracoes, text="Configurações")
        
        # Notebook para configurações específicas
        config_notebook = ttk.Notebook(frame_configuracoes)
        config_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de configurações gerais
        frame_config_geral = ttk.Frame(config_notebook, padding=10)
        config_notebook.add(frame_config_geral, text="Geral")
        
        # Prefeitura padrão
        frame_prefeitura = ttk.LabelFrame(frame_config_geral, text="Prefeitura Padrão", padding=10)
        frame_prefeitura.pack(fill=tk.X, padx=5, pady=5)
        
        self.prefeitura_padrao_var = tk.StringVar(value="São José" if self.config.get('prefeitura_padrao') == 'sj' else "Florianópolis")
        
        rb_sj = ttk.Radiobutton(frame_prefeitura, text="São José", variable=self.prefeitura_padrao_var, value="São José")
        rb_sj.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        rb_floripa = ttk.Radiobutton(frame_prefeitura, text="Florianópolis", variable=self.prefeitura_padrao_var, value="Florianópolis")
        rb_floripa.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Backup automático
        frame_backup = ttk.LabelFrame(frame_config_geral, text="Backup Automático", padding=10)
        frame_backup.pack(fill=tk.X, padx=5, pady=5)
        
        self.backup_automatico_var = tk.BooleanVar(value=self.config.get('backup', {}).get('automatico', True))
        check_backup = ttk.Checkbutton(frame_backup, text="Ativar backup automático", variable=self.backup_automatico_var)
        check_backup.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(frame_backup, text="Intervalo:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.intervalo_backup_var = tk.StringVar(value=self.config.get('backup', {}).get('intervalo', 'diario').capitalize())
        combo_intervalo = ttk.Combobox(frame_backup, textvariable=self.intervalo_backup_var,
                                     values=["Diário", "Semanal", "Mensal"],
                                     state="readonly", width=15)
        combo_intervalo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        combo_intervalo.current(0 if self.intervalo_backup_var.get() == "Diário" else
                               1 if self.intervalo_backup_var.get() == "Semanal" else 2)
        
        ttk.Label(frame_backup, text="Hora:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        hora_backup = self.config.get('backup', {}).get('hora', '23:00')
        horas, minutos = hora_backup.split(':')
        
        frame_hora_backup = ttk.Frame(frame_backup)
        frame_hora_backup.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.hora_backup_var = tk.StringVar(value=horas)
        self.minuto_backup_var = tk.StringVar(value=minutos)
        
        self.spin_hora_backup = ttk.Spinbox(frame_hora_backup, from_=0, to=23, width=3, format="%02.0f", 
                                         textvariable=self.hora_backup_var)
        self.spin_hora_backup.pack(side=tk.LEFT)
        
        ttk.Label(frame_hora_backup, text=":").pack(side=tk.LEFT)
        
        self.spin_minuto_backup = ttk.Spinbox(frame_hora_backup, from_=0, to=59, width=3, format="%02.0f", 
                                           textvariable=self.minuto_backup_var)
        self.spin_minuto_backup.pack(side=tk.LEFT)
        
        # Diretório de backup
        ttk.Label(frame_backup, text="Diretório de Backup:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        frame_dir_backup = ttk.Frame(frame_backup)
        frame_dir_backup.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)
        
        self.entry_dir_backup = ttk.Entry(frame_dir_backup, width=30)
        self.entry_dir_backup.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_dir_backup.insert(0, BACKUP_DIR)
        
        btn_escolher_dir = ttk.Button(frame_dir_backup, text="...", width=3, command=self.escolher_diretorio_backup)
        btn_escolher_dir.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Aba de configurações SMTP
        frame_config_smtp = ttk.Frame(config_notebook, padding=10)
        config_notebook.add(frame_config_smtp, text="SMTP")
        
        # Notebook para cada prefeitura
        smtp_notebook = ttk.Notebook(frame_config_smtp)
        smtp_notebook.pack(fill=tk.BOTH, expand=True)
        
        # SMTP São José
        frame_smtp_sj = ttk.Frame(smtp_notebook, padding=10)
        smtp_notebook.add(frame_smtp_sj, text="São José")
        
        # Formulário SMTP São José
        self.criar_form_smtp(frame_smtp_sj, 'sj')
        
        # SMTP Florianópolis
        frame_smtp_floripa = ttk.Frame(smtp_notebook, padding=10)
        smtp_notebook.add(frame_smtp_floripa, text="Florianópolis")
        
        # Formulário SMTP Florianópolis
        self.criar_form_smtp(frame_smtp_floripa, 'floripa')
        
        # Aba de assinaturas
        frame_config_assinaturas = ttk.Frame(config_notebook, padding=10)
        config_notebook.add(frame_config_assinaturas, text="Assinaturas")
        
        # Notebook para cada prefeitura (assinaturas)
        assinaturas_notebook = ttk.Notebook(frame_config_assinaturas)
        assinaturas_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Assinaturas São José
        frame_assinaturas_sj = ttk.Frame(assinaturas_notebook, padding=10)
        assinaturas_notebook.add(frame_assinaturas_sj, text="São José")
        
        # Assinatura padrão São José
        ttk.Label(frame_assinaturas_sj, text="Assinatura Padrão:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.text_assinatura_sj = tk.Text(frame_assinaturas_sj, width=80, height=10)
        self.text_assinatura_sj.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        scrollbar_assinatura_sj = ttk.Scrollbar(frame_assinaturas_sj, orient=tk.VERTICAL, 
                                             command=self.text_assinatura_sj.yview)
        scrollbar_assinatura_sj.grid(row=1, column=2, sticky=tk.NS, pady=5)
        self.text_assinatura_sj.config(yscrollcommand=scrollbar_assinatura_sj.set)
        
        # Carrega a assinatura atual
        self.text_assinatura_sj.insert(tk.END, self.config.get('assinaturas', {}).get('sj', {}).get('padrao', ''))
        
        # Assinaturas Florianópolis
        frame_assinaturas_floripa = ttk.Frame(assinaturas_notebook, padding=10)
        assinaturas_notebook.add(frame_assinaturas_floripa, text="Florianópolis")
        
        # Assinatura padrão Florianópolis
        ttk.Label(frame_assinaturas_floripa, text="Assinatura Padrão:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.text_assinatura_floripa = tk.Text(frame_assinaturas_floripa, width=80, height=10)
        self.text_assinatura_floripa.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        scrollbar_assinatura_floripa = ttk.Scrollbar(frame_assinaturas_floripa, orient=tk.VERTICAL, 
                                                 command=self.text_assinatura_floripa.yview)
        scrollbar_assinatura_floripa.grid(row=1, column=2, sticky=tk.NS, pady=5)
        self.text_assinatura_floripa.config(yscrollcommand=scrollbar_assinatura_floripa.set)
        
        # Carrega a assinatura atual
        self.text_assinatura_floripa.insert(tk.END, self.config.get('assinaturas', {}).get('floripa', {}).get('padrao', ''))
        
        # Aba de Grupos
        frame_config_grupos = ttk.Frame(config_notebook, padding=10)
        config_notebook.add(frame_config_grupos, text="Grupos")
        
        # Lista de grupos
        ttk.Label(frame_config_grupos, text="Grupos Disponíveis:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(5, 0))
        
        frame_lista_grupos = ttk.Frame(frame_config_grupos)
        frame_lista_grupos.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(0, 10))
        
        self.lista_grupos = ttk.Treeview(frame_lista_grupos, 
                                     columns=('id', 'nome', 'descricao', 'prefeitura', 'membros'),
                                     show='headings', height=5)
        self.lista_grupos.heading('id', text='ID')
        self.lista_grupos.heading('nome', text='Nome')
        self.lista_grupos.heading('descricao', text='Descrição')
        self.lista_grupos.heading('prefeitura', text='Prefeitura')
        self.lista_grupos.heading('membros', text='Membros')
        
        self.lista_grupos.column('id', width=50)
        self.lista_grupos.column('nome', width=150)
        self.lista_grupos.column('descricao', width=200)
        self.lista_grupos.column('prefeitura', width=100)
        self.lista_grupos.column('membros', width=100)
        
        self.lista_grupos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_grupos = ttk.Scrollbar(frame_lista_grupos, orient=tk.VERTICAL, command=self.lista_grupos.yview)
        scrollbar_grupos.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_grupos.config(yscrollcommand=scrollbar_grupos.set)
        
        # Botões para gerenciar grupos
        frame_botoes_grupos = ttk.Frame(frame_config_grupos)
        frame_botoes_grupos.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))
        
        btn_gerenciar_membros = ttk.Button(frame_botoes_grupos, text="Gerenciar Membros", 
                                      command=self.gerenciar_membros_grupo)
        btn_gerenciar_membros.pack(side=tk.LEFT, padx=2)
        
        btn_excluir_grupo = ttk.Button(frame_botoes_grupos, text="Excluir Grupo", command=self.excluir_grupo)
        btn_excluir_grupo.pack(side=tk.LEFT, padx=2)
        
        btn_editar_grupo = ttk.Button(frame_botoes_grupos, text="Editar Grupo", command=self.editar_grupo)
        btn_editar_grupo.pack(side=tk.LEFT, padx=2)
        
        btn_atualizar_grupos = ttk.Button(frame_botoes_grupos, text="Atualizar Lista", command=self.atualizar_lista_grupos)
        btn_atualizar_grupos.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(frame_config_grupos, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Formulário de novo grupo
        ttk.Label(frame_config_grupos, text="Novo Grupo:", font=('Helvetica', 12, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Nome
        ttk.Label(frame_config_grupos, text="Nome:", font=('Helvetica', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_nome_grupo = ttk.Entry(frame_config_grupos, width=50)
        self.entry_nome_grupo.grid(row=5, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Descrição
        ttk.Label(frame_config_grupos, text="Descrição:", font=('Helvetica', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        self.entry_descricao_grupo = ttk.Entry(frame_config_grupos, width=50)
        self.entry_descricao_grupo.grid(row=6, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        
        # Prefeitura
        ttk.Label(frame_config_grupos, text="Prefeitura:", font=('Helvetica', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        self.combo_prefeitura_grupo = ttk.Combobox(frame_config_grupos, 
                                              values=["São José", "Florianópolis"],
                                              state="readonly", width=50)
        self.combo_prefeitura_grupo.grid(row=7, column=1, columnspan=2, sticky=tk.EW, pady=(5, 0))
        self.combo_prefeitura_grupo.current(0 if self.prefeitura_atual == 'sj' else 1)
        
        # Botões de ação
        frame_acoes_grupo = ttk.Frame(frame_config_grupos)
        frame_acoes_grupo.grid(row=8, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        btn_salvar_grupo = ttk.Button(frame_acoes_grupo, text="Salvar Grupo", command=self.salvar_grupo)
        btn_salvar_grupo.pack(side=tk.RIGHT, padx=5)
        
        btn_limpar_grupo = ttk.Button(frame_acoes_grupo, text="Limpar Campos", command=self.limpar_campos_grupo)
        btn_limpar_grupo.pack(side=tk.RIGHT, padx=5)
        
        # Atualiza a lista de grupos
        self.atualizar_lista_grupos()
        
        # Botões de ação para configurações
        frame_acoes_config = ttk.Frame(frame_configuracoes)
        frame_acoes_config.pack(fill=tk.X, padx=10, pady=10)
        
        btn_salvar_config = ttk.Button(frame_acoes_config, text="Salvar Configurações", command=self.salvar_configuracoes_sistema)
        btn_salvar_config.pack(side=tk.RIGHT, padx=5)
        
        btn_restaurar_config = ttk.Button(frame_acoes_config, text="Restaurar Padrões", command=self.restaurar_configuracoes_padrao)
        btn_restaurar_config.pack(side=tk.RIGHT, padx=5)
        
        btn_testar_smtp = ttk.Button(frame_acoes_config, text="Testar Conexão SMTP", command=self.testar_conexao_smtp)
        btn_testar_smtp.pack(side=tk.RIGHT, padx=5)
        
        btn_fazer_backup = ttk.Button(frame_acoes_config, text="Fazer Backup Agora", command=self.fazer_backup_manual)
        btn_fazer_backup.pack(side=tk.RIGHT, padx=5)
        
        # Configurar a expansão das grids
        frame_config_geral.columnconfigure(0, weight=1)
        frame_assinaturas_sj.columnconfigure(0, weight=1)
        frame_assinaturas_sj.rowconfigure(1, weight=1)
        frame_assinaturas_floripa.columnconfigure(0, weight=1)
        frame_assinaturas_floripa.rowconfigure(1, weight=1)
        frame_config_grupos.columnconfigure(1, weight=1)
        frame_config_grupos.rowconfigure(1, weight=1)
    
    def criar_form_smtp(self, frame, prefeitura):
        """Cria o formulário de configuração SMTP para a prefeitura especificada."""
        # Servidor
        ttk.Label(frame, text="Servidor SMTP:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.entry_servidor_smtp = {}
        self.entry_servidor_smtp[prefeitura] = ttk.Entry(frame, width=30)
        self.entry_servidor_smtp[prefeitura].grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.entry_servidor_smtp[prefeitura].insert(0, self.config.get('smtp', {}).get(prefeitura, {}).get('servidor', ''))
        
        # Porta
        ttk.Label(frame, text="Porta:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.entry_porta_smtp = {}
        self.entry_porta_smtp[prefeitura] = ttk.Entry(frame, width=10)
        self.entry_porta_smtp[prefeitura].grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.entry_porta_smtp[prefeitura].insert(0, str(self.config.get('smtp', {}).get(prefeitura, {}).get('porta', 587)))
        
        # Usuário
        ttk.Label(frame, text="Usuário:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.entry_usuario_smtp = {}
        self.entry_usuario_smtp[prefeitura] = ttk.Entry(frame, width=30)
        self.entry_usuario_smtp[prefeitura].grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.entry_usuario_smtp[prefeitura].insert(0, self.config.get('smtp', {}).get(prefeitura, {}).get('usuario', ''))
        
        # Senha
        ttk.Label(frame, text="Senha:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.entry_senha_smtp = {}
        self.entry_senha_smtp[prefeitura] = ttk.Entry(frame, width=30, show="*")
        self.entry_senha_smtp[prefeitura].grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        self.entry_senha_smtp[prefeitura].insert(0, self.config.get('smtp', {}).get(prefeitura, {}).get('senha', ''))
        
        # Segurança
        ttk.Label(frame, text="Segurança:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        
        frame_seguranca = ttk.Frame(frame)
        frame_seguranca.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        self.tls_var = {}
        self.ssl_var = {}
        
        self.tls_var[prefeitura] = tk.BooleanVar(value=self.config.get('smtp', {}).get(prefeitura, {}).get('tls', True))
        check_tls = ttk.Checkbutton(frame_seguranca, text="Usar TLS", variable=self.tls_var[prefeitura])
        check_tls.pack(side=tk.LEFT, padx=5)
        
        self.ssl_var[prefeitura] = tk.BooleanVar(value=self.config.get('smtp', {}).get(prefeitura, {}).get('ssl', False))
        check_ssl = ttk.Checkbutton(frame_seguranca, text="Usar SSL", variable=self.ssl_var[prefeitura])
        check_ssl.pack(side=tk.LEFT, padx=5)
    
    def criar_aba_logs(self):
        """Cria a aba para visualização de logs do sistema."""
        frame_logs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_logs, text="Logs")
        
        # Filtros
        frame_filtros = ttk.LabelFrame(frame_logs, text="Filtros", padding=10)
        frame_filtros.pack(fill=tk.X, padx=5, pady=5)
        
        # Tipo de ação
        ttk.Label(frame_filtros, text="Tipo de Ação:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.combo_acao_log = ttk.Combobox(frame_filtros, width=20, state="readonly")
        self.combo_acao_log.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Data inicial
        ttk.Label(frame_filtros, text="Data Inicial:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        self.data_inicial_log = DateEntry(frame_filtros, width=12, background=self.cores['primaria'],
                                       foreground='black', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.data_inicial_log.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Data final
        ttk.Label(frame_filtros, text="Data Final:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        
        self.data_final_log = DateEntry(frame_filtros, width=12, background=self.cores['primaria'],
                                     foreground='black', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.data_final_log.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Usuário
        ttk.Label(frame_filtros, text="Usuário:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.combo_usuario_log = ttk.Combobox(frame_filtros, width=30, state="readonly")
        self.combo_usuario_log.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Botões de ação para filtros
        btn_filtrar = ttk.Button(frame_filtros, text="Filtrar", command=self.filtrar_logs)
        btn_filtrar.grid(row=1, column=4, padx=5, pady=5)
        
        btn_limpar_filtros = ttk.Button(frame_filtros, text="Limpar Filtros", command=self.limpar_filtros_log)
        btn_limpar_filtros.grid(row=1, column=5, padx=5, pady=5)
        
        # Lista de logs
        ttk.Label(frame_logs, text="Registros:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=(10, 0))
        
        frame_lista_logs = ttk.Frame(frame_logs)
        frame_lista_logs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.lista_logs = ttk.Treeview(frame_lista_logs, 
                                     columns=('id', 'data', 'usuario', 'acao', 'descricao'),
                                     show='headings', height=15)
        self.lista_logs.heading('id', text='ID')
        self.lista_logs.heading('data', text='Data/Hora')
        self.lista_logs.heading('usuario', text='Usuário')
        self.lista_logs.heading('acao', text='Ação')
        self.lista_logs.heading('descricao', text='Descrição')
        
        self.lista_logs.column('id', width=50)
        self.lista_logs.column('data', width=150)
        self.lista_logs.column('usuario', width=150)
        self.lista_logs.column('acao', width=150)
        self.lista_logs.column('descricao', width=400)
        
        self.lista_logs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_logs = ttk.Scrollbar(frame_lista_logs, orient=tk.VERTICAL, command=self.lista_logs.yview)
        scrollbar_logs.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_logs.config(yscrollcommand=scrollbar_logs.set)
        
        # Botões de ação para logs
        frame_acoes_logs = ttk.Frame(frame_logs)
        frame_acoes_logs.pack(fill=tk.X, padx=5, pady=5)
        
        btn_atualizar_logs = ttk.Button(frame_acoes_logs, text="Atualizar Logs", command=self.atualizar_lista_logs)
        btn_atualizar_logs.pack(side=tk.LEFT, padx=5)
        
        btn_exportar_logs = ttk.Button(frame_acoes_logs, text="Exportar Logs", command=self.exportar_logs)
        btn_exportar_logs.pack(side=tk.LEFT, padx=5)
        
        btn_limpar_logs = ttk.Button(frame_acoes_logs, text="Limpar Logs Antigos", command=self.limpar_logs_antigos)
        btn_limpar_logs.pack(side=tk.LEFT, padx=5)
        
        # Carregar dados para os filtros
        self.carregar_dados_filtros_log()
        
        # Atualiza a lista de logs
        self.atualizar_lista_logs()
    
    def fazer_logout(self):
        """Realiza logout do sistema e volta para a tela de login."""
        try:
            if hasattr(self, 'usuario_atual'):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                # Registra o logout
                cursor.execute('''
                INSERT INTO logs (usuario_id, acao, descricao)
                VALUES (?, ?, ?)
                ''', (self.usuario_atual['id'], "LOGOUT", f"Logout realizado com sucesso"))
                
                conn.commit()
                conn.close()
            
            # Limpa as informações do usuário
            self.usuario_atual = None
            
            # Volta para a tela de login
            self.criar_tela_login()
        except Exception as e:
            logger.error(f"Erro ao realizar logout: {e}")
            messagebox.showerror("Erro", f"Não foi possível realizar o logout: {e}")
    
    def abrir_ajuda(self):
        """Abre a tela de ajuda do sistema."""
        # Criando uma nova janela
        self.janela_ajuda = tk.Toplevel(self.root)
        self.janela_ajuda.title("Ajuda do Sistema")
        self.janela_ajuda.geometry("800x600")
        self.janela_ajuda.minsize(600, 400)
        
        # Configurando estilo
        style = ttk.Style()
        style.configure('Ajuda.TFrame', background=self.cores['fundo'])
        style.configure('Ajuda.TLabel', background=self.cores['fundo'], foreground=self.cores['texto'])
        
        # Criando o notebook para as diferentes seções de ajuda
        notebook_ajuda = ttk.Notebook(self.janela_ajuda)
        notebook_ajuda.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de Visão Geral
        frame_visao_geral = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_visao_geral, text="Visão Geral")
        
        texto_visao_geral = tk.Text(frame_visao_geral, wrap=tk.WORD, font=('Helvetica', 11))
        texto_visao_geral.pack(fill=tk.BOTH, expand=True)
        
        texto_visao_geral.insert(tk.END, """
        Sistema de Envio de E-mails para Prefeituras
        ===========================================
        
        Este sistema foi desenvolvido para gerenciar e enviar e-mails institucionais das prefeituras 
        de São José e Florianópolis. Ele oferece uma variedade de funcionalidades para facilitar a 
        comunicação institucional.
        
        Principais Características:
        - Envio de e-mails individuais e em massa
        - Agendamento de e-mails automáticos
        - Gerenciamento de funcionários e grupos
        - Modelos de e-mail personalizáveis
        - Sistema de backup automático
        - Registro completo de atividades
        
        Para começar a usar o sistema, faça login com as credenciais fornecidas pelo administrador.
        
        Caso tenha dúvidas específicas, consulte as outras abas desta janela de ajuda para informações 
        detalhadas sobre cada funcionalidade.
        """)
        texto_visao_geral.config(state=tk.DISABLED)
        
        # Aba de E-mail Individual
        frame_email_individual = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_email_individual, text="E-mail Individual")
        
        texto_email_individual = tk.Text(frame_email_individual, wrap=tk.WORD, font=('Helvetica', 11))
        texto_email_individual.pack(fill=tk.BOTH, expand=True)
        
        texto_email_individual.insert(tk.END, """
        Envio de E-mail Individual
        ========================
        
        A aba de E-mail Individual permite enviar mensagens para um destinatário específico. 
        
        Para enviar um e-mail individual:
        
        1. Informe o e-mail do destinatário ou clique em "Selecionar" para escolher um funcionário da lista.
        2. Digite o assunto do e-mail.
        3. Escreva o conteúdo da mensagem no editor. Você pode usar os botões de formatação para melhorar a aparência do texto.
        4. Opcionalmente, você pode:
           - Adicionar anexos clicando em "Adicionar Anexo"
           - Usar um template existente clicando em "Usar Template"
           - Incluir ou não a sua assinatura marcando a opção correspondente
        5. Clique em "Pré-visualizar" para ver como o e-mail ficará antes de enviar.
        6. Clique em "Enviar E-mail" para enviar a mensagem.
        
        O sistema armazenará automaticamente um registro do e-mail enviado com informações sobre o status de entrega.
        """)
        texto_email_individual.config(state=tk.DISABLED)
        
        # Aba de E-mail em Massa
        frame_email_massa = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_email_massa, text="E-mail em Massa")
        
        texto_email_massa = tk.Text(frame_email_massa, wrap=tk.WORD, font=('Helvetica', 11))
        texto_email_massa.pack(fill=tk.BOTH, expand=True)
        
        texto_email_massa.insert(tk.END, """
        Envio de E-mail em Massa
        =======================
        
        A aba de E-mail em Massa permite enviar a mesma mensagem para múltiplos destinatários simultaneamente.
        
        Para enviar e-mails em massa:
        
        1. Selecione o método de definição dos destinatários:
           - Grupo: Selecione um grupo predefinido de funcionários
           - Departamento: Envie para todos os funcionários de um departamento específico
           - Importar Lista: Importe uma lista de e-mails a partir de um arquivo CSV ou Excel
           - Lista Manual: Digite manualmente os e-mails separados por vírgula ou quebra de linha
        
        2. Verifique a lista de preview para confirmar os destinatários selecionados.
        
        3. Opcionalmente, selecione um template existente marcando "Usar template" e escolhendo-o na lista.
        
        4. Preencha o assunto e o conteúdo da mensagem. Você pode usar variáveis como {nome}, {cargo}, etc., 
           que serão substituídas pelos dados de cada destinatário.
        
        5. Configure as opções de envio:
           - Limite de e-mails por hora: Para evitar bloqueios do servidor SMTP
           - Intervalo entre e-mails: Para distribuir o envio ao longo do tempo
        
        6. Clique em "Enviar E-mails" para iniciar o processo de envio.
        
        O sistema mostrará o progresso do envio e registrará o status de cada mensagem.
        """)
        texto_email_massa.config(state=tk.DISABLED)
        
        # Aba de Agendamento
        frame_agendamento = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_agendamento, text="Agendamento")
        
        texto_agendamento = tk.Text(frame_agendamento, wrap=tk.WORD, font=('Helvetica', 11))
        texto_agendamento.pack(fill=tk.BOTH, expand=True)
        
        texto_agendamento.insert(tk.END, """
        Agendamento de E-mails
        =====================
        
        A funcionalidade de Agendamento permite programar e-mails para serem enviados automaticamente 
        em datas e horários específicos, com opção de recorrência.
        
        Para agendar um e-mail:
        
        1. Na parte superior da aba, você pode visualizar e gerenciar todos os e-mails já agendados.
        
        2. Para criar um novo agendamento, defina os destinatários da mesma forma que no envio em massa.
        
        3. Configure as opções de agendamento:
           - Data: Selecione a data para o envio
           - Hora: Defina o horário exato
           - Recorrência: Escolha entre Nenhuma, Diária, Semanal ou Mensal
           - Para agendamentos recorrentes, configure as opções específicas que aparecem
        
        4. Preencha o assunto e conteúdo da mensagem, podendo usar templates e variáveis.
        
        5. Clique em "Agendar E-mail" para confirmar o agendamento.
        
        Os e-mails agendados serão enviados automaticamente nos horários programados, mesmo que o 
        sistema esteja fechado, desde que o serviço de agendamento esteja em execução no servidor.
        
        Você pode editar ou cancelar agendamentos existentes a qualquer momento.
        """)
        texto_agendamento.config(state=tk.DISABLED)
        
        # Aba de Templates
        frame_templates = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_templates, text="Templates")
        
        texto_templates = tk.Text(frame_templates, wrap=tk.WORD, font=('Helvetica', 11))
        texto_templates.pack(fill=tk.BOTH, expand=True)
        
        texto_templates.insert(tk.END, """
        Gerenciamento de Templates
        ========================
        
        O sistema permite criar, editar e gerenciar modelos de e-mail (templates) para agilizar o envio 
        de mensagens padronizadas.
        
        Para criar um novo template:
        
        1. Na parte inferior da aba, preencha os campos do formulário:
           - Nome do Template: Um nome descritivo para facilitar a identificação
           - Departamento: Associe o template a um departamento específico (opcional)
           - Assunto: O assunto padrão para e-mails que usarem este template
           - Conteúdo: O texto do e-mail, onde você pode incluir formatação e variáveis
        
        2. Você pode usar variáveis como {nome}, {cargo}, {departamento}, etc., que serão substituídas 
           pelos dados reais ao usar o template.
        
        3. Clique em "Salvar Template" para armazenar o modelo.
        
        Para usar um template:
        
        1. Ao criar um novo e-mail (individual, em massa ou agendado), clique em "Usar Template"
        2. Selecione o template desejado na lista
        3. O assunto e conteúdo serão preenchidos automaticamente com os dados do template
        4. Você pode editar o conteúdo antes de enviar, sem alterar o template original
        
        Você também pode editar, duplicar ou excluir templates existentes usando os botões na parte 
        superior da aba.
        """)
        texto_templates.config(state=tk.DISABLED)
        
        # Aba de Funcionários
        frame_funcionarios = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_funcionarios, text="Funcionários")
        
        texto_funcionarios = tk.Text(frame_funcionarios, wrap=tk.WORD, font=('Helvetica', 11))
        texto_funcionarios.pack(fill=tk.BOTH, expand=True)
        
        texto_funcionarios.insert(tk.END, """
        Gerenciamento de Funcionários
        ===========================
        
        A aba de Funcionários permite gerenciar o cadastro de todos os funcionários das prefeituras 
        que podem receber e-mails.
        
        Principais funcionalidades:
        
        1. Cadastro de funcionários:
           - Preencha os dados do formulário na parte inferior da aba
           - Informe nome, e-mail, cargo, departamento, telefone e prefeitura
           - Clique em "Salvar Funcionário" para confirmar o cadastro
        
        2. Busca de funcionários:
           - Use o campo de busca para encontrar funcionários por nome, e-mail, cargo ou departamento
           - Selecione o filtro desejado no menu suspenso ao lado
        
        3. Gerenciamento de cadastros:
           - Edite informações de funcionários existentes usando o botão "Editar Funcionário"
           - Ative ou desative cadastros com o botão "Ativar/Desativar"
           - Adicione funcionários a grupos específicos usando "Adicionar a Grupo"
        
        4. Importação e exportação:
           - Importe dados de funcionários a partir de arquivos CSV ou Excel
           - Exporte a lista de funcionários para CSV ou Excel
           - Use o modelo fornecido pelo sistema para preparar arquivos de importação
        
        Os funcionários cadastrados estarão disponíveis para seleção ao enviar e-mails 
        individuais ou em massa.
        """)
        texto_funcionarios.config(state=tk.DISABLED)
        
        # Aba de Configurações
        frame_configuracoes = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_configuracoes, text="Configurações")
        
        texto_configuracoes = tk.Text(frame_configuracoes, wrap=tk.WORD, font=('Helvetica', 11))
        texto_configuracoes.pack(fill=tk.BOTH, expand=True)
        
        texto_configuracoes.insert(tk.END, """
        Configurações do Sistema
        ======================
        
        A aba de Configurações (disponível apenas para administradores) permite personalizar 
        diversos aspectos do funcionamento do sistema.
        
        Principais seções:
        
        1. Configurações Gerais:
           - Prefeitura padrão: Define qual prefeitura será selecionada ao iniciar o sistema
           - Backup automático: Ativa/desativa e configura o backup automático dos dados
        
        2. Configurações SMTP:
           - Servidor SMTP: Endereço do servidor de e-mail de cada prefeitura
           - Porta: Porta de conexão (geralmente 587 para TLS ou 465 para SSL)
           - Usuário/Senha: Credenciais de acesso ao servidor
           - Segurança: Opções de TLS e SSL para conexão segura
        
        3. Assinaturas:
           - Configure assinaturas padrão para cada prefeitura
           - Use variáveis como {nome}, {cargo}, etc. que serão preenchidas automaticamente
        
        4. Grupos:
           - Crie e gerencie grupos de destinatários
           - Adicione ou remova funcionários dos grupos
           - Use para facilitar o envio de e-mails a equipes específicas
        
        5. Usuários (administrador):
           - Gerencie as contas de usuários do sistema
           - Defina níveis de acesso e permissões
        
        6. Logs (administrador):
           - Visualize e exporte registros de atividades
           - Monitore ações realizadas no sistema
        
        Após fazer alterações nas configurações, clique em "Salvar Configurações" para aplicá-las.
        """)
        texto_configuracoes.config(state=tk.DISABLED)
        
        # Aba de FAQ
        frame_faq = ttk.Frame(notebook_ajuda, padding=10, style='Ajuda.TFrame')
        notebook_ajuda.add(frame_faq, text="FAQ")
        
        texto_faq = tk.Text(frame_faq, wrap=tk.WORD, font=('Helvetica', 11))
        texto_faq.pack(fill=tk.BOTH, expand=True)
        
        texto_faq.insert(tk.END, """
        Perguntas Frequentes (FAQ)
        =========================
        
        P: Como faço para enviar um e-mail para todos os funcionários de um departamento?
        R: Na aba "E-mail em Massa", selecione a opção "Departamento" e escolha o departamento desejado na lista suspensa.
        
        P: O que são variáveis nos templates e como usá-las?
        R: Variáveis são marcadores como {nome}, {cargo}, etc. que serão substituídos pelos dados reais de cada destinatário. Para usá-las, insira-as no texto do template ou da mensagem.
        
        P: Como faço para criar um e-mail recorrente que será enviado todo mês?
        R: Na aba "Agendamento", configure os destinatários e a mensagem, escolha a data da primeira ocorrência e selecione "Mensal" na opção de recorrência.
        
        P: O sistema continuará enviando e-mails agendados mesmo se o computador for desligado?
        R: Sim, desde que o serviço de agendamento esteja em execução no servidor. Os e-mails agendados são armazenados no banco de dados e processados no horário programado.
        
        P: Como importar uma lista grande de funcionários para o sistema?
        R: Na aba "Funcionários", clique em "Importar CSV/Excel", selecione o arquivo preparado no formato correto e siga as instruções do assistente de importação.
        
        P: Como verificar se um e-mail em massa foi entregue corretamente a todos os destinatários?
        R: Na aba "Logs", filtre por "ENVIO_EMAIL" na opção "Tipo de Ação" e procure pelo assunto ou data específica do envio.
        
        P: Esqueci minha senha. Como recuperá-la?
        R: Contate o administrador do sistema, que poderá resetar sua senha na aba "Usuários".
        
        P: O que fazer se o servidor SMTP não estiver respondendo?
        R: Verifique as configurações SMTP na aba "Configurações", teste a conexão usando o botão "Testar Conexão SMTP" e consulte o administrador de rede se o problema persistir.
        
        P: Como personalizar a assinatura dos meus e-mails?
        R: Os administradores podem configurar assinaturas padrão na aba "Configurações > Assinaturas". Se precisar de uma assinatura personalizada, solicite ao administrador.
        
        P: É possível cancelar um e-mail agendado?
        R: Sim. Na aba "Agendamento", selecione o e-mail na lista e clique em "Cancelar Agendamento".
        """)
        texto_faq.config(state=tk.DISABLED)
        
        # Botão para fechar
        btn_fechar = ttk.Button(self.janela_ajuda, text="Fechar", command=self.janela_ajuda.destroy)
        btn_fechar.pack(pady=10)
    
    def atualizar_opcao_destinatarios(self):
        """Atualiza a exibição das opções de destinatários para e-mail em massa."""
        # Limpa o frame atual
        for widget in self.frame_opcao_destinatarios.winfo_children():
            widget.destroy()
        
        opcao = self.opcao_destinatarios.get()
        
        if opcao == "grupo":
            # Opção de seleção de grupo
            ttk.Label(self.frame_opcao_destinatarios, text="Selecione o grupo:").pack(side=tk.LEFT, padx=5)
            
            self.combo_grupo = ttk.Combobox(self.frame_opcao_destinatarios, width=40, state="readonly")
            self.combo_grupo.pack(side=tk.LEFT, padx=5)
            self.combo_grupo.bind("<<ComboboxSelected>>", self.atualizar_preview_destinatarios)
            
            # Carrega os grupos disponíveis
            self.carregar_grupos_combo()
            
        elif opcao == "departamento":
            # Opção de seleção de departamento
            ttk.Label(self.frame_opcao_destinatarios, text="Selecione o departamento:").pack(side=tk.LEFT, padx=5)
            
            self.combo_departamento = ttk.Combobox(self.frame_opcao_destinatarios, width=40)
            self.combo_departamento.pack(side=tk.LEFT, padx=5)
            self.combo_departamento.bind("<<ComboboxSelected>>", self.atualizar_preview_destinatarios)
            
            # Carrega os departamentos disponíveis
            self.carregar_departamentos_combo()
            
        elif opcao == "importar":
            # Opção de importação de lista
            ttk.Label(self.frame_opcao_destinatarios, text="Arquivo:").pack(side=tk.LEFT, padx=5)
            
            self.entry_arquivo_importacao = ttk.Entry(self.frame_opcao_destinatarios, width=40)
            self.entry_arquivo_importacao.pack(side=tk.LEFT, padx=5)
            
            btn_selecionar_arquivo = ttk.Button(self.frame_opcao_destinatarios, text="Selecionar", 
                                              command=self.selecionar_arquivo_destinatarios)
            btn_selecionar_arquivo.pack(side=tk.LEFT, padx=5)
            
        elif opcao == "manual":
            # Opção de lista manual
            ttk.Label(self.frame_opcao_destinatarios, text="Digite os e-mails (um por linha ou separados por vírgula):").pack(anchor=tk.W, padx=5, pady=5)
            
            self.text_emails_manual = tk.Text(self.frame_opcao_destinatarios, width=60, height=5)
            self.text_emails_manual.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            btn_validar_emails = ttk.Button(self.frame_opcao_destinatarios, text="Validar E-mails", 
                                         command=self.validar_emails_manual)
            btn_validar_emails.pack(anchor=tk.E, padx=5, pady=5)
    
    def atualizar_opcao_destinatarios_agendamento(self):
        """Atualiza a exibição das opções de destinatários para agendamento."""
        # Limpa o frame atual
        for widget in self.frame_opcao_destinatarios_agendamento.winfo_children():
            widget.destroy()
        
        opcao = self.opcao_destinatarios_agendamento.get()
        
        if opcao == "grupo":
            # Opção de seleção de grupo
            ttk.Label(self.frame_opcao_destinatarios_agendamento, text="Selecione o grupo:").pack(side=tk.LEFT, padx=5)
            
            self.combo_grupo_agendamento = ttk.Combobox(self.frame_opcao_destinatarios_agendamento, 
                                                   width=40, state="readonly")
            self.combo_grupo_agendamento.pack(side=tk.LEFT, padx=5)
            self.combo_grupo_agendamento.bind("<<ComboboxSelected>>", self.atualizar_preview_destinatarios_agendamento)
            
            # Carrega os grupos disponíveis
            self.carregar_grupos_combo_agendamento()
            
        elif opcao == "departamento":
            # Opção de seleção de departamento
            ttk.Label(self.frame_opcao_destinatarios_agendamento, text="Selecione o departamento:").pack(side=tk.LEFT, padx=5)
            
            self.combo_departamento_agendamento = ttk.Combobox(self.frame_opcao_destinatarios_agendamento, width=40)
            self.combo_departamento_agendamento.pack(side=tk.LEFT, padx=5)
            self.combo_departamento_agendamento.bind("<<ComboboxSelected>>", 
                                              self.atualizar_preview_destinatarios_agendamento)
            
            # Carrega os departamentos disponíveis
            self.carregar_departamentos_combo_agendamento()
            
        elif opcao == "importar":
            # Opção de importação de lista
            ttk.Label(self.frame_opcao_destinatarios_agendamento, text="Arquivo:").pack(side=tk.LEFT, padx=5)
            
            self.entry_arquivo_importacao_agendamento = ttk.Entry(self.frame_opcao_destinatarios_agendamento, width=40)
            self.entry_arquivo_importacao_agendamento.pack(side=tk.LEFT, padx=5)
            
            btn_selecionar_arquivo = ttk.Button(self.frame_opcao_destinatarios_agendamento, 
                                              text="Selecionar", 
                                              command=self.selecionar_arquivo_destinatarios_agendamento)
            btn_selecionar_arquivo.pack(side=tk.LEFT, padx=5)
            
        elif opcao == "manual":
            # Opção de lista manual
            ttk.Label(self.frame_opcao_destinatarios_agendamento, 
                   text="Digite os e-mails (um por linha ou separados por vírgula):").pack(anchor=tk.W, padx=5, pady=5)
            
            self.text_emails_manual_agendamento = tk.Text(self.frame_opcao_destinatarios_agendamento, width=60, height=5)
            self.text_emails_manual_agendamento.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            btn_validar_emails = ttk.Button(self.frame_opcao_destinatarios_agendamento, 
                                         text="Validar E-mails", 
                                         command=self.validar_emails_manual_agendamento)
            btn_validar_emails.pack(anchor=tk.E, padx=5, pady=5)
    
    def atualizar_recorrencia(self, event=None):
        """Atualiza as opções específicas de recorrência."""
        # Limpa o frame atual
        for widget in self.frame_recorrencia.winfo_children():
            widget.destroy()
        
        recorrencia = self.recorrencia_var.get().lower()
        
        if recorrencia == "semanal":
            # Opções de dia da semana
            ttk.Label(self.frame_recorrencia, text="Dia da semana:").pack(side=tk.LEFT, padx=5)
            
            dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            self.combo_dia_semana = ttk.Combobox(self.frame_recorrencia, values=dias_semana, state="readonly", width=15)
            self.combo_dia_semana.pack(side=tk.LEFT, padx=5)
            self.combo_dia_semana.current(0)  # Segunda-feira por padrão
            
        elif recorrencia == "mensal":
            # Opções de dia do mês
            ttk.Label(self.frame_recorrencia, text="Dia do mês:").pack(side=tk.LEFT, padx=5)
            
            dias_mes = list(range(1, 32))
            self.combo_dia_mes = ttk.Combobox(self.frame_recorrencia, values=dias_mes, state="readonly", width=5)
            self.combo_dia_mes.pack(side=tk.LEFT, padx=5)
            self.combo_dia_mes.current(0)  # Primeiro dia por padrão
    
    def atualizar_template(self):
        """Atualiza o estado do combobox de templates baseado na opção selecionada."""
        if self.usar_template.get():
            self.combo_template.config(state="readonly")
        else:
            self.combo_template.config(state="disabled")
    
    def atualizar_template_agendamento(self):
        """Atualiza o estado do combobox de templates baseado na opção selecionada para agendamento."""
        if self.usar_template_agendamento.get():
            self.combo_template_agendamento.config(state="readonly")
        else:
            self.combo_template_agendamento.config(state="disabled")
    
    def carregar_templates_combo(self):
        """Carrega os templates disponíveis no combobox."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca templates da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome FROM templates 
            WHERE prefeitura = ? 
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            templates = cursor.fetchall()
            
            # Preenche o combobox
            self.combo_template.config(values=[f"{id} - {nome}" for id, nome in templates])
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar templates: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os templates: {e}")
    
    def carregar_templates_combo_agendamento(self):
        """Carrega os templates disponíveis no combobox para agendamento."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca templates da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome FROM templates 
            WHERE prefeitura = ? 
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            templates = cursor.fetchall()
            
            # Preenche o combobox
            self.combo_template_agendamento.config(values=[f"{id} - {nome}" for id, nome in templates])
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar templates para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os templates: {e}")
    
    def carregar_grupos_combo(self):
        """Carrega os grupos disponíveis no combobox."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca grupos da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome FROM grupos 
            WHERE prefeitura = ? 
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            grupos = cursor.fetchall()
            
            # Preenche o combobox
            self.combo_grupo.config(values=[f"{id} - {nome}" for id, nome in grupos])
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar grupos: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os grupos: {e}")
    
    def carregar_grupos_combo_agendamento(self):
        """Carrega os grupos disponíveis no combobox para agendamento."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca grupos da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome FROM grupos 
            WHERE prefeitura = ? 
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            grupos = cursor.fetchall()
            
            # Preenche o combobox
            self.combo_grupo_agendamento.config(values=[f"{id} - {nome}" for id, nome in grupos])
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar grupos para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os grupos: {e}")
    
    def carregar_departamentos(self):
        """Carrega os departamentos disponíveis."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca departamentos únicos dos funcionários da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT DISTINCT departamento FROM funcionarios 
            WHERE prefeitura = ? AND departamento IS NOT NULL AND departamento != ''
            ORDER BY departamento
            ''', (prefeitura_codigo,))
            
            departamentos = [dep[0] for dep in cursor.fetchall()]
            
            # Atualiza os comboboxes que usam departamentos
            if hasattr(self, 'combo_departamento_template'):
                self.combo_departamento_template.config(values=departamentos)
            
            if hasattr(self, 'combo_departamento_funcionario'):
                self.combo_departamento_funcionario.config(values=departamentos)
            
            if hasattr(self, 'combo_departamento_usuario'):
                self.combo_departamento_usuario.config(values=departamentos)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar departamentos: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os departamentos: {e}")
    
    def carregar_departamentos_combo(self):
        """Carrega os departamentos disponíveis no combobox para e-mail em massa."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca departamentos únicos dos funcionários da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT DISTINCT departamento FROM funcionarios 
            WHERE prefeitura = ? AND departamento IS NOT NULL AND departamento != ''
            ORDER BY departamento
            ''', (prefeitura_codigo,))
            
            departamentos = [dep[0] for dep in cursor.fetchall()]
            
            # Preenche o combobox
            self.combo_departamento.config(values=departamentos)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar departamentos para e-mail em massa: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os departamentos: {e}")
    
    def carregar_departamentos_combo_agendamento(self):
        """Carrega os departamentos disponíveis no combobox para agendamento."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca departamentos únicos dos funcionários da prefeitura atual
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT DISTINCT departamento FROM funcionarios 
            WHERE prefeitura = ? AND departamento IS NOT NULL AND departamento != ''
            ORDER BY departamento
            ''', (prefeitura_codigo,))
            
            departamentos = [dep[0] for dep in cursor.fetchall()]
            
            # Preenche o combobox
            self.combo_departamento_agendamento.config(values=departamentos)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar departamentos para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar os departamentos: {e}")
    
    def selecionar_arquivo_destinatarios(self):
        """Abre o diálogo para selecionar arquivo de importação de destinatários."""
        filetypes = [
            ('Arquivos CSV', '*.csv'),
            ('Arquivos Excel', '*.xlsx *.xls'),
            ('Todos os arquivos', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo de destinatários",
            filetypes=filetypes
        )
        
        if filename:
            self.entry_arquivo_importacao.delete(0, tk.END)
            self.entry_arquivo_importacao.insert(0, filename)
            self.importar_destinatarios()
    
    def selecionar_arquivo_destinatarios_agendamento(self):
        """Abre o diálogo para selecionar arquivo de importação de destinatários para agendamento."""
        filetypes = [
            ('Arquivos CSV', '*.csv'),
            ('Arquivos Excel', '*.xlsx *.xls'),
            ('Todos os arquivos', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo de destinatários",
            filetypes=filetypes
        )
        
        if filename:
            self.entry_arquivo_importacao_agendamento.delete(0, tk.END)
            self.entry_arquivo_importacao_agendamento.insert(0, filename)
            self.importar_destinatarios_agendamento()
    
    def atualizar_preview_destinatarios(self, event=None):
        """Atualiza a preview de destinatários com base na seleção."""
        try:
            # Limpa a lista atual
            for item in self.lista_preview.get_children():
                self.lista_preview.delete(item)
            
            opcao = self.opcao_destinatarios.get()
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            if opcao == "grupo":
                # Obtém os destinatários do grupo selecionado
                if not hasattr(self, 'combo_grupo') or not self.combo_grupo.get():
                    return
                
                grupo_id = self.combo_grupo.get().split(" - ")[0]
                
                cursor.execute('''
                SELECT f.email, f.nome, f.departamento FROM funcionarios f
                JOIN grupo_funcionario gf ON f.id = gf.funcionario_id
                WHERE gf.grupo_id = ? AND f.ativo = 1
                ORDER BY f.nome
                ''', (grupo_id,))
                
            elif opcao == "departamento":
                # Obtém os funcionários do departamento selecionado
                if not hasattr(self, 'combo_departamento') or not self.combo_departamento.get():
                    return
                
                departamento = self.combo_departamento.get()
                prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
                
                cursor.execute('''
                SELECT email, nome, departamento FROM funcionarios 
                WHERE departamento = ? AND prefeitura = ? AND ativo = 1
                ORDER BY nome
                ''', (departamento, prefeitura_codigo))
            
            else:
                # Para outras opções, a preview é preenchida por métodos específicos
                return
            
            # Preenche a lista de preview
            funcionarios = cursor.fetchall()
            contador = 0
            
            for email, nome, departamento in funcionarios:
                self.lista_preview.insert("", tk.END, values=(email, nome, departamento))
                contador += 1
            
            # Atualiza o contador
            self.lbl_contador.config(text=f"Total de destinatários: {contador}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar preview de destinatários: {e}")
            messagebox.showerror("Erro", f"Não foi possível atualizar a lista de destinatários: {e}")
    
    def atualizar_preview_destinatarios_agendamento(self, event=None):
        """Atualiza a preview de destinatários para agendamento."""
        try:
            # Limpa a lista atual
            for item in self.lista_preview_agendamento.get_children():
                self.lista_preview_agendamento.delete(item)
            
            opcao = self.opcao_destinatarios_agendamento.get()
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            if opcao == "grupo":
                # Obtém os destinatários do grupo selecionado
                if not hasattr(self, 'combo_grupo_agendamento') or not self.combo_grupo_agendamento.get():
                    return
                
                grupo_id = self.combo_grupo_agendamento.get().split(" - ")[0]
                
                cursor.execute('''
                SELECT f.email, f.nome, f.departamento FROM funcionarios f
                JOIN grupo_funcionario gf ON f.id = gf.funcionario_id
                WHERE gf.grupo_id = ? AND f.ativo = 1
                ORDER BY f.nome
                ''', (grupo_id,))
                
            elif opcao == "departamento":
                # Obtém os funcionários do departamento selecionado
                if not hasattr(self, 'combo_departamento_agendamento') or not self.combo_departamento_agendamento.get():
                    return
                
                departamento = self.combo_departamento_agendamento.get()
                prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
                
                cursor.execute('''
                SELECT email, nome, departamento FROM funcionarios 
                WHERE departamento = ? AND prefeitura = ? AND ativo = 1
                ORDER BY nome
                ''', (departamento, prefeitura_codigo))
            
            else:
                # Para outras opções, a preview é preenchida por métodos específicos
                return
            
            # Preenche a lista de preview
            funcionarios = cursor.fetchall()
            contador = 0
            
            for email, nome, departamento in funcionarios:
                self.lista_preview_agendamento.insert("", tk.END, values=(email, nome, departamento))
                contador += 1
            
            # Atualiza o contador
            self.lbl_contador_agendamento.config(text=f"Total de destinatários: {contador}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar preview de destinatários para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível atualizar a lista de destinatários: {e}")
    
    def importar_destinatarios(self):
        """Importa destinatários de arquivo CSV ou Excel."""
        try:
            arquivo = self.entry_arquivo_importacao.get()
            
            if not arquivo:
                messagebox.showwarning("Aviso", "Selecione um arquivo para importar.")
                return
                
            # Limpa a lista atual
            for item in self.lista_preview.get_children():
                self.lista_preview.delete(item)
            
            # Identifica o tipo de arquivo
            extensao = os.path.splitext(arquivo)[1].lower()
            
            if extensao == '.csv':
                # Importa do CSV
                with open(arquivo, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    cabecalho = next(reader)  # Pula o cabeçalho
                    
                    # Tenta identificar as colunas
                    email_idx = None
                    nome_idx = None
                    departamento_idx = None
                    
                    for i, col in enumerate(cabecalho):
                        col_lower = col.lower()
                        if 'email' in col_lower or 'e-mail' in col_lower:
                            email_idx = i
                        elif 'nome' in col_lower:
                            nome_idx = i
                        elif 'departamento' in col_lower or 'setor' in col_lower:
                            departamento_idx = i
                    
                    if email_idx is None:
                        messagebox.showerror("Erro", "Não foi possível identificar a coluna de e-mail no arquivo CSV.")
                        return
                    
                    # Preenche a lista
                    contador = 0
                    for row in reader:
                        if len(row) > email_idx:
                            email = row[email_idx]
                            nome = row[nome_idx] if nome_idx is not None and len(row) > nome_idx else ""
                            departamento = row[departamento_idx] if departamento_idx is not None and len(row) > departamento_idx else ""
                            
                            self.lista_preview.insert("", tk.END, values=(email, nome, departamento))
                            contador += 1
            
            elif extensao in ['.xlsx', '.xls']:
                # Importa do Excel
                df = pd.read_excel(arquivo)
                
                # Tenta identificar as colunas
                email_col = None
                nome_col = None
                departamento_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'email' in col_lower or 'e-mail' in col_lower:
                        email_col = col
                    elif 'nome' in col_lower:
                        nome_col = col
                    elif 'departamento' in col_lower or 'setor' in col_lower:
                        departamento_col = col
                
                if email_col is None:
                    messagebox.showerror("Erro", "Não foi possível identificar a coluna de e-mail no arquivo Excel.")
                    return
                
                # Preenche a lista
                contador = 0
                for _, row in df.iterrows():
                    email = str(row[email_col])
                    nome = str(row[nome_col]) if nome_col is not None else ""
                    departamento = str(row[departamento_col]) if departamento_col is not None else ""
                    
                    if email and email != "nan":
                        self.lista_preview.insert("", tk.END, values=(email, nome, departamento))
                        contador += 1
            
            else:
                messagebox.showerror("Erro", "Formato de arquivo não suportado. Use CSV ou Excel.")
                return
            
            # Atualiza o contador
            self.lbl_contador.config(text=f"Total de destinatários: {contador}")
            
        except Exception as e:
            logger.error(f"Erro ao importar destinatários: {e}")
            messagebox.showerror("Erro", f"Falha ao importar arquivo: {e}")
    
    def importar_destinatarios_agendamento(self):
        """Importa destinatários de arquivo CSV ou Excel para agendamento."""
        try:
            arquivo = self.entry_arquivo_importacao_agendamento.get()
            
            if not arquivo:
                messagebox.showwarning("Aviso", "Selecione um arquivo para importar.")
                return
                
            # Limpa a lista atual
            for item in self.lista_preview_agendamento.get_children():
                self.lista_preview_agendamento.delete(item)
            
            # Identifica o tipo de arquivo
            extensao = os.path.splitext(arquivo)[1].lower()
            
            if extensao == '.csv':
                # Importa do CSV
                with open(arquivo, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    cabecalho = next(reader)  # Pula o cabeçalho
                    
                    # Tenta identificar as colunas
                    email_idx = None
                    nome_idx = None
                    departamento_idx = None
                    
                    for i, col in enumerate(cabecalho):
                        col_lower = col.lower()
                        if 'email' in col_lower or 'e-mail' in col_lower:
                            email_idx = i
                        elif 'nome' in col_lower:
                            nome_idx = i
                        elif 'departamento' in col_lower or 'setor' in col_lower:
                            departamento_idx = i
                    
                    if email_idx is None:
                        messagebox.showerror("Erro", "Não foi possível identificar a coluna de e-mail no arquivo CSV.")
                        return
                    
                    # Preenche a lista
                    contador = 0
                    for row in reader:
                        if len(row) > email_idx:
                            email = row[email_idx]
                            nome = row[nome_idx] if nome_idx is not None and len(row) > nome_idx else ""
                            departamento = row[departamento_idx] if departamento_idx is not None and len(row) > departamento_idx else ""
                            
                            self.lista_preview_agendamento.insert("", tk.END, values=(email, nome, departamento))
                            contador += 1
            
            elif extensao in ['.xlsx', '.xls']:
                # Importa do Excel
                df = pd.read_excel(arquivo)
                
                # Tenta identificar as colunas
                email_col = None
                nome_col = None
                departamento_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'email' in col_lower or 'e-mail' in col_lower:
                        email_col = col
                    elif 'nome' in col_lower:
                        nome_col = col
                    elif 'departamento' in col_lower or 'setor' in col_lower:
                        departamento_col = col
                
                if email_col is None:
                    messagebox.showerror("Erro", "Não foi possível identificar a coluna de e-mail no arquivo Excel.")
                    return
                
                # Preenche a lista
                contador = 0
                for _, row in df.iterrows():
                    email = str(row[email_col])
                    nome = str(row[nome_col]) if nome_col is not None else ""
                    departamento = str(row[departamento_col]) if departamento_col is not None else ""
                    
                    if email and email != "nan":
                        self.lista_preview_agendamento.insert("", tk.END, values=(email, nome, departamento))
                        contador += 1
            
            else:
                messagebox.showerror("Erro", "Formato de arquivo não suportado. Use CSV ou Excel.")
                return
            
            # Atualiza o contador
            self.lbl_contador_agendamento.config(text=f"Total de destinatários: {contador}")
            
        except Exception as e:
            logger.error(f"Erro ao importar destinatários para agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao importar arquivo: {e}")
    
    def validar_emails_manual(self):
        """Valida os e-mails digitados manualmente e atualiza a preview."""
        try:
            texto = self.text_emails_manual.get(1.0, tk.END).strip()
            
            if not texto:
                messagebox.showwarning("Aviso", "Digite pelo menos um e-mail.")
                return
            
            # Separa os e-mails (por vírgula ou quebra de linha)
            emails_raw = texto.replace(',', '\n')
            emails_list = [e.strip() for e in emails_raw.split('\n') if e.strip()]
            
            # Limpa a lista atual
            for item in self.lista_preview.get_children():
                self.lista_preview.delete(item)
            
            # Valida e adiciona cada e-mail
            contador = 0
            emails_invalidos = []
            
            for email in emails_list:
                # Validação básica de e-mail
                import re
                padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                
                if re.match(padrao_email, email):
                    self.lista_preview.insert("", tk.END, values=(email, "", ""))
                    contador += 1
                else:
                    emails_invalidos.append(email)
            
            # Atualiza o contador
            self.lbl_contador.config(text=f"Total de destinatários: {contador}")
            
            # Avisa sobre e-mails inválidos
            if emails_invalidos:
                mensagem = "Os seguintes e-mails são inválidos e foram ignorados:\n\n"
                mensagem += "\n".join(emails_invalidos)
                messagebox.showwarning("E-mails Inválidos", mensagem)
                
        except Exception as e:
            logger.error(f"Erro ao validar e-mails: {e}")
            messagebox.showerror("Erro", f"Falha ao validar e-mails: {e}")
    
    def validar_emails_manual_agendamento(self):
        """Valida os e-mails digitados manualmente e atualiza a preview para agendamento."""
        try:
            texto = self.text_emails_manual_agendamento.get(1.0, tk.END).strip()
            
            if not texto:
                messagebox.showwarning("Aviso", "Digite pelo menos um e-mail.")
                return
            
            # Separa os e-mails (por vírgula ou quebra de linha)
            emails_raw = texto.replace(',', '\n')
            emails_list = [e.strip() for e in emails_raw.split('\n') if e.strip()]
            
            # Limpa a lista atual
            for item in self.lista_preview_agendamento.get_children():
                self.lista_preview_agendamento.delete(item)
            
            # Valida e adiciona cada e-mail
            contador = 0
            emails_invalidos = []
            
            for email in emails_list:
                # Validação básica de e-mail
                import re
                padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                
                if re.match(padrao_email, email):
                    self.lista_preview_agendamento.insert("", tk.END, values=(email, "", ""))
                    contador += 1
                else:
                    emails_invalidos.append(email)
            
            # Atualiza o contador
            self.lbl_contador_agendamento.config(text=f"Total de destinatários: {contador}")
            
            # Avisa sobre e-mails inválidos
            if emails_invalidos:
                mensagem = "Os seguintes e-mails são inválidos e foram ignorados:\n\n"
                mensagem += "\n".join(emails_invalidos)
                messagebox.showwarning("E-mails Inválidos", mensagem)
                
        except Exception as e:
            logger.error(f"Erro ao validar e-mails para agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao validar e-mails: {e}")
    
    def abrir_selecao_funcionarios(self):
        """Abre janela para selecionar funcionários."""
        # Criando uma nova janela
        self.janela_selecao = tk.Toplevel(self.root)
        self.janela_selecao.title("Selecionar Funcionário")
        self.janela_selecao.geometry("800x500")
        self.janela_selecao.minsize(600, 400)
        
        # Configurando estilo
        style = ttk.Style()
        style.configure('Selecao.TFrame', background=self.cores['fundo'])
        style.configure('Selecao.TLabel', background=self.cores['fundo'], foreground=self.cores['texto'])
        
        # Frame principal
        frame_selecao = ttk.Frame(self.janela_selecao, padding=10, style='Selecao.TFrame')
        frame_selecao.pack(fill=tk.BOTH, expand=True)
        
        # Barra de busca
        frame_busca = ttk.Frame(frame_selecao, style='Selecao.TFrame')
        frame_busca.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_busca, text="Buscar:", style='Selecao.TLabel').pack(side=tk.LEFT, padx=5)
        
        self.entry_busca_selecao = ttk.Entry(frame_busca, width=30)
        self.entry_busca_selecao.pack(side=tk.LEFT, padx=5)
        self.entry_busca_selecao.bind("<KeyRelease>", self.buscar_funcionario_selecao)
        
        self.filtro_selecao = tk.StringVar(value="nome")
        combo_filtro = ttk.Combobox(frame_busca, textvariable=self.filtro_selecao, 
                                 values=["Nome", "E-mail", "Cargo", "Departamento"], 
                                 state="readonly", width=15)
        combo_filtro.pack(side=tk.LEFT, padx=5)
        combo_filtro.current(0)
        
        btn_buscar = ttk.Button(frame_busca, text="Buscar", command=self.buscar_funcionario_selecao)
        btn_buscar.pack(side=tk.LEFT, padx=5)
        
        # Lista de funcionários
        frame_lista = ttk.Frame(frame_selecao, style='Selecao.TFrame')
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.lista_selecao = ttk.Treeview(frame_lista, 
                                        columns=('id', 'nome', 'email', 'cargo', 'departamento'),
                                        show='headings', height=15)
        self.lista_selecao.heading('id', text='ID')
        self.lista_selecao.heading('nome', text='Nome')
        self.lista_selecao.heading('email', text='E-mail')
        self.lista_selecao.heading('cargo', text='Cargo')
        self.lista_selecao.heading('departamento', text='Departamento')
        
        self.lista_selecao.column('id', width=50)
        self.lista_selecao.column('nome', width=200)
        self.lista_selecao.column('email', width=200)
        self.lista_selecao.column('cargo', width=150)
        self.lista_selecao.column('departamento', width=150)
        
        self.lista_selecao.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_selecao = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.lista_selecao.yview)
        scrollbar_selecao.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_selecao.config(yscrollcommand=scrollbar_selecao.set)
        
        # Botões de ação
        frame_botoes = ttk.Frame(self.janela_selecao, style='Selecao.TFrame')
        frame_botoes.pack(fill=tk.X, padx=10, pady=10)
        
        btn_selecionar = ttk.Button(frame_botoes, text="Selecionar", command=self.selecionar_funcionario)
        btn_selecionar.pack(side=tk.RIGHT, padx=5)
        
        btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=self.janela_selecao.destroy)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)
        
        # Carrega a lista de funcionários
        self.carregar_funcionarios_selecao()
        
        # Foco na busca
        self.entry_busca_selecao.focus_set()
    
    def carregar_funcionarios_selecao(self):
        """Carrega a lista de funcionários para seleção."""
        try:
            # Limpa a lista atual
            for item in self.lista_selecao.get_children():
                self.lista_selecao.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome, email, cargo, departamento FROM funcionarios 
            WHERE prefeitura = ? AND ativo = 1
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            funcionarios = cursor.fetchall()
            
            for func in funcionarios:
                self.lista_selecao.insert("", tk.END, values=func)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar funcionários para seleção: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar a lista de funcionários: {e}")
    
    def buscar_funcionario_selecao(self, event=None):
        """Busca funcionários na janela de seleção."""
        try:
            busca = self.entry_busca_selecao.get().strip()
            filtro = self.filtro_selecao.get().lower()
            
            # Limpa a lista atual
            for item in self.lista_selecao.get_children():
                self.lista_selecao.delete(item)
            
            if not busca:
                self.carregar_funcionarios_selecao()
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            campo_filtro = ''
            
            if filtro == 'nome':
                campo_filtro = 'nome'
            elif filtro == 'e-mail':
                campo_filtro = 'email'
            elif filtro == 'cargo':
                campo_filtro = 'cargo'
            elif filtro == 'departamento':
                campo_filtro = 'departamento'
            
            cursor.execute(f'''
            SELECT id, nome, email, cargo, departamento FROM funcionarios 
            WHERE prefeitura = ? AND ativo = 1 AND {campo_filtro} LIKE ?
            ORDER BY nome
            ''', (prefeitura_codigo, f'%{busca}%'))
            
            funcionarios = cursor.fetchall()
            
            for func in funcionarios:
                self.lista_selecao.insert("", tk.END, values=func)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {e}")
            messagebox.showerror("Erro", f"Falha na busca: {e}")
    
    def selecionar_funcionario(self):
        """Seleciona o funcionário e fecha a janela de seleção."""
        try:
            selecionado = self.lista_selecao.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário da lista.")
                return
            
            valores = self.lista_selecao.item(selecionado[0], 'values')
            
            # Coloca o e-mail do funcionário na entrada de destinatário
            self.entry_destinatario.delete(0, tk.END)
            self.entry_destinatario.insert(0, valores[2])  # Email
            
            # Fecha a janela
            self.janela_selecao.destroy()
        except Exception as e:
            logger.error(f"Erro ao selecionar funcionário: {e}")
            messagebox.showerror("Erro", f"Não foi possível selecionar o funcionário: {e}")
    
    def abrir_selecao_template(self):
        """Abre janela para selecionar template."""
        # Criando uma nova janela
        self.janela_template = tk.Toplevel(self.root)
        self.janela_template.title("Selecionar Template")
        self.janela_template.geometry("800x500")
        self.janela_template.minsize(600, 400)
        
        # Configurando estilo
        style = ttk.Style()
        style.configure('Template.TFrame', background=self.cores['fundo'])
        style.configure('Template.TLabel', background=self.cores['fundo'], foreground=self.cores['texto'])
        
        # Frame principal
        frame_template = ttk.Frame(self.janela_template, padding=10, style='Template.TFrame')
        frame_template.pack(fill=tk.BOTH, expand=True)
        
        # Lista de templates
        ttk.Label(frame_template, text="Templates Disponíveis:", style='Template.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        frame_lista = ttk.Frame(frame_template, style='Template.TFrame')
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.lista_selecao_template = ttk.Treeview(frame_lista, 
                                               columns=('id', 'nome', 'assunto', 'departamento'),
                                               show='headings', height=10)
        self.lista_selecao_template.heading('id', text='ID')
        self.lista_selecao_template.heading('nome', text='Nome')
        self.lista_selecao_template.heading('assunto', text='Assunto')
        self.lista_selecao_template.heading('departamento', text='Departamento')
        
        self.lista_selecao_template.column('id', width=50)
        self.lista_selecao_template.column('nome', width=200)
        self.lista_selecao_template.column('assunto', width=200)
        self.lista_selecao_template.column('departamento', width=150)
        
        self.lista_selecao_template.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_template = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.lista_selecao_template.yview)
        scrollbar_template.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_selecao_template.config(yscrollcommand=scrollbar_template.set)
        
        # Frame de visualização
        ttk.Label(frame_template, text="Prévia:", style='Template.TLabel').pack(anchor=tk.W, pady=(10, 5))
        
        frame_preview = ttk.Frame(frame_template, style='Template.TFrame')
        frame_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_preview_template = tk.Text(frame_preview, width=80, height=10, wrap=tk.WORD)
        self.text_preview_template.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_preview = ttk.Scrollbar(frame_preview, orient=tk.VERTICAL, command=self.text_preview_template.yview)
        scrollbar_preview.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_preview_template.config(yscrollcommand=scrollbar_preview.set)
        self.text_preview_template.config(state=tk.DISABLED)
        
        # Botões de ação
        frame_botoes = ttk.Frame(self.janela_template, style='Template.TFrame')
        frame_botoes.pack(fill=tk.X, padx=10, pady=10)
        
        btn_selecionar = ttk.Button(frame_botoes, text="Usar Template", command=self.usar_template_selecionado)
        btn_selecionar.pack(side=tk.RIGHT, padx=5)
        
        btn_visualizar = ttk.Button(frame_botoes, text="Visualizar", command=self.visualizar_template_na_selecao)
        btn_visualizar.pack(side=tk.RIGHT, padx=5)
        
        btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=self.janela_template.destroy)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)
        
        # Carrega a lista de templates
        self.carregar_templates_selecao()
        
        # Evento de seleção
        self.lista_selecao_template.bind("<<TreeviewSelect>>", self.visualizar_template_na_selecao)
    
    def carregar_templates_selecao(self):
        """Carrega a lista de templates para seleção."""
        try:
            # Limpa a lista atual
            for item in self.lista_selecao_template.get_children():
                self.lista_selecao_template.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome, assunto, departamento FROM templates 
            WHERE prefeitura = ?
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            templates = cursor.fetchall()
            
            for template in templates:
                self.lista_selecao_template.insert("", tk.END, values=template)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar templates para seleção: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar a lista de templates: {e}")
    
    def visualizar_template_na_selecao(self, event=None):
        """Visualiza o template selecionado na janela de seleção."""
        try:
            selecionado = self.lista_selecao_template.selection()
            
            if not selecionado:
                return
            
            valores = self.lista_selecao_template.item(selecionado[0], 'values')
            template_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT conteudo FROM templates WHERE id = ?', (template_id,))
            conteudo = cursor.fetchone()[0]
            
            # Atualiza a prévia
            self.text_preview_template.config(state=tk.NORMAL)
            self.text_preview_template.delete(1.0, tk.END)
            self.text_preview_template.insert(tk.END, conteudo)
            self.text_preview_template.config(state=tk.DISABLED)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao visualizar template: {e}")
            messagebox.showerror("Erro", f"Não foi possível visualizar o template: {e}")
    
    def usar_template_selecionado(self):
        """Usa o template selecionado no e-mail atual."""
        try:
            selecionado = self.lista_selecao_template.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um template da lista.")
                return
            
            valores = self.lista_selecao_template.item(selecionado[0], 'values')
            template_id = valores[0]
            assunto = valores[2]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT conteudo FROM templates WHERE id = ?', (template_id,))
            conteudo = cursor.fetchone()[0]
            
            # Preenche o assunto e conteúdo do e-mail
            self.entry_assunto.delete(0, tk.END)
            self.entry_assunto.insert(0, assunto)
            
            self.text_mensagem.delete(1.0, tk.END)
            self.text_mensagem.insert(tk.END, conteudo)
            
            conn.close()
            
            # Fecha a janela
            self.janela_template.destroy()
        except Exception as e:
            logger.error(f"Erro ao usar template: {e}")
            messagebox.showerror("Erro", f"Não foi possível aplicar o template: {e}")
    
    def selecionar_template(self, event=None):
        """Seleciona um template através do combobox e preenche os campos."""
        try:
            if not self.usar_template.get() or not self.combo_template.get():
                return
                
            template_id = self.combo_template.get().split(" - ")[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT assunto, conteudo FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                assunto, conteudo = resultado
                
                # Preenche o assunto e conteúdo do e-mail
                self.entry_assunto_massa.delete(0, tk.END)
                self.entry_assunto_massa.insert(0, assunto)
                
                self.text_mensagem_massa.delete(1.0, tk.END)
                self.text_mensagem_massa.insert(tk.END, conteudo)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao selecionar template: {e}")
            messagebox.showerror("Erro", f"Não foi possível selecionar o template: {e}")
    
    def selecionar_template_agendamento(self, event=None):
        """Seleciona um template através do combobox e preenche os campos para agendamento."""
        try:
            if not self.usar_template_agendamento.get() or not self.combo_template_agendamento.get():
                return
                
            template_id = self.combo_template_agendamento.get().split(" - ")[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT assunto, conteudo FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                assunto, conteudo = resultado
                
                # Preenche o assunto e conteúdo do e-mail
                self.entry_assunto_agendamento.delete(0, tk.END)
                self.entry_assunto_agendamento.insert(0, assunto)
                
                self.text_mensagem_agendamento.delete(1.0, tk.END)
                self.text_mensagem_agendamento.insert(tk.END, conteudo)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao selecionar template para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível selecionar o template: {e}")
    
    def visualizar_template(self):
        """Visualiza o template selecionado no combobox."""
        try:
            if not self.combo_template.get():
                messagebox.showwarning("Aviso", "Selecione um template da lista.")
                return
                
            template_id = self.combo_template.get().split(" - ")[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, assunto, conteudo FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, assunto, conteudo = resultado
                
                # Cria janela de visualização
                janela_visualizacao = tk.Toplevel(self.root)
                janela_visualizacao.title(f"Template: {nome}")
                janela_visualizacao.geometry("700x500")
                janela_visualizacao.minsize(600, 400)
                
                frame_visualizacao = ttk.Frame(janela_visualizacao, padding=10)
                frame_visualizacao.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(frame_visualizacao, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
                
                frame_conteudo = ttk.Frame(frame_visualizacao)
                frame_conteudo.pack(fill=tk.BOTH, expand=True)
                
                text_conteudo = tk.Text(frame_conteudo, wrap=tk.WORD)
                text_conteudo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                text_conteudo.insert(tk.END, conteudo)
                text_conteudo.config(state=tk.DISABLED)
                
                scrollbar = ttk.Scrollbar(frame_conteudo, orient=tk.VERTICAL, command=text_conteudo.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_conteudo.config(yscrollcommand=scrollbar.set)
                
                ttk.Button(janela_visualizacao, text="Fechar", command=janela_visualizacao.destroy).pack(pady=10)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao visualizar template: {e}")
            messagebox.showerror("Erro", f"Não foi possível visualizar o template: {e}")
    
    def visualizar_template_agendamento(self):
        """Visualiza o template selecionado no combobox para agendamento."""
        try:
            if not self.combo_template_agendamento.get():
                messagebox.showwarning("Aviso", "Selecione um template da lista.")
                return
                
            template_id = self.combo_template_agendamento.get().split(" - ")[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, assunto, conteudo FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, assunto, conteudo = resultado
                
                # Cria janela de visualização
                janela_visualizacao = tk.Toplevel(self.root)
                janela_visualizacao.title(f"Template: {nome}")
                janela_visualizacao.geometry("700x500")
                janela_visualizacao.minsize(600, 400)
                
                frame_visualizacao = ttk.Frame(janela_visualizacao, padding=10)
                frame_visualizacao.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(frame_visualizacao, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
                
                frame_conteudo = ttk.Frame(frame_visualizacao)
                frame_conteudo.pack(fill=tk.BOTH, expand=True)
                
                text_conteudo = tk.Text(frame_conteudo, wrap=tk.WORD)
                text_conteudo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                text_conteudo.insert(tk.END, conteudo)
                text_conteudo.config(state=tk.DISABLED)
                
                scrollbar = ttk.Scrollbar(frame_conteudo, orient=tk.VERTICAL, command=text_conteudo.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_conteudo.config(yscrollcommand=scrollbar.set)
                
                ttk.Button(janela_visualizacao, text="Fechar", command=janela_visualizacao.destroy).pack(pady=10)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao visualizar template para agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível visualizar o template: {e}")
    
    def formatar_texto(self, tipo):
        """Aplica formatação ao texto selecionado no editor."""
        try:
            # Obtém o texto selecionado
            if self.text_mensagem.tag_ranges("sel"):
                inicio, fim = self.text_mensagem.tag_ranges("sel")
                texto_selecionado = self.text_mensagem.get(inicio, fim)
                
                if tipo == "negrito":
                    texto_formatado = f"<b>{texto_selecionado}</b>"
                elif tipo == "italico":
                    texto_formatado = f"<i>{texto_selecionado}</i>"
                elif tipo == "sublinhado":
                    texto_formatado = f"<u>{texto_selecionado}</u>"
                elif tipo == "lista":
                    linhas = texto_selecionado.split("\n")
                    texto_formatado = "<ul>\n"
                    for linha in linhas:
                        if linha.strip():
                            texto_formatado += f"  <li>{linha.strip()}</li>\n"
                    texto_formatado += "</ul>"
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    if url:
                        texto_formatado = f'<a href="{url}">{texto_selecionado}</a>'
                    else:
                        return
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    if url:
                        alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                        alt = alt or texto_selecionado or "Imagem"
                        texto_formatado = f'<img src="{url}" alt="{alt}" style="max-width: 100%;">'
                    else:
                      return
                else:
                    return
                
                # Substitui o texto selecionado pelo texto formatado
                self.text_mensagem.delete(inicio, fim)
                self.text_mensagem.insert(inicio, texto_formatado)
            else:
                # Se não houver texto selecionado
                if tipo == "lista":
                    self.text_mensagem.insert(tk.INSERT, "<ul>\n  <li></li>\n</ul>")
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    texto = simpledialog.askstring("Texto do Link", "Digite o texto que será exibido:")
                    if url and texto:
                        self.text_mensagem.insert(tk.INSERT, f'<a href="{url}">{texto}</a>')
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                    if url:
                        alt = alt or "Imagem"
                        self.text_mensagem.insert(tk.INSERT, f'<img src="{url}" alt="{alt}" style="max-width: 100%;">')
        except Exception as e:
            logger.error(f"Erro ao formatar texto: {e}")
            messagebox.showerror("Erro", f"Falha ao aplicar formatação: {e}")
    
    def formatar_texto_massa(self, tipo):
        """Aplica formatação ao texto selecionado no editor de e-mail em massa."""
        try:
            # Obtém o texto selecionado
            if self.text_mensagem_massa.tag_ranges("sel"):
                inicio, fim = self.text_mensagem_massa.tag_ranges("sel")
                texto_selecionado = self.text_mensagem_massa.get(inicio, fim)
                
                if tipo == "negrito":
                    texto_formatado = f"<b>{texto_selecionado}</b>"
                elif tipo == "italico":
                    texto_formatado = f"<i>{texto_selecionado}</i>"
                elif tipo == "sublinhado":
                    texto_formatado = f"<u>{texto_selecionado}</u>"
                elif tipo == "lista":
                    linhas = texto_selecionado.split("\n")
                    texto_formatado = "<ul>\n"
                    for linha in linhas:
                        if linha.strip():
                            texto_formatado += f"  <li>{linha.strip()}</li>\n"
                    texto_formatado += "</ul>"
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    if url:
                        texto_formatado = f'<a href="{url}">{texto_selecionado}</a>'
                    else:
                        return
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    if url:
                        alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                        alt = alt or texto_selecionado or "Imagem"
                        texto_formatado = f'<img src="{url}" alt="{alt}" style="max-width: 100%;">'
                    else:
                        return
                
                # Substitui o texto selecionado pelo texto formatado
                self.text_mensagem_massa.delete(inicio, fim)
                self.text_mensagem_massa.insert(inicio, texto_formatado)
            else:
                # Se não houver texto selecionado
                if tipo == "lista":
                    self.text_mensagem_massa.insert(tk.INSERT, "<ul>\n  <li></li>\n</ul>")
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    texto = simpledialog.askstring("Texto do Link", "Digite o texto que será exibido:")
                    if url and texto:
                        self.text_mensagem_massa.insert(tk.INSERT, f'<a href="{url}">{texto}</a>')
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                    if url:
                        alt = alt or "Imagem"
                        self.text_mensagem_massa.insert(tk.INSERT, f'<img src="{url}" alt="{alt}" style="max-width: 100%;">')
        except Exception as e:
            logger.error(f"Erro ao formatar texto em massa: {e}")
            messagebox.showerror("Erro", f"Falha ao aplicar formatação: {e}")
    
    def formatar_texto_agendamento(self, tipo):
        """Aplica formatação ao texto selecionado no editor de agendamento."""
        try:
            # Obtém o texto selecionado
            if self.text_mensagem_agendamento.tag_ranges("sel"):
                inicio, fim = self.text_mensagem_agendamento.tag_ranges("sel")
                texto_selecionado = self.text_mensagem_agendamento.get(inicio, fim)
                
                if tipo == "negrito":
                    texto_formatado = f"<b>{texto_selecionado}</b>"
                elif tipo == "italico":
                    texto_formatado = f"<i>{texto_selecionado}</i>"
                elif tipo == "sublinhado":
                    texto_formatado = f"<u>{texto_selecionado}</u>"
                elif tipo == "lista":
                    linhas = texto_selecionado.split("\n")
                    texto_formatado = "<ul>\n"
                    for linha in linhas:
                        if linha.strip():
                            texto_formatado += f"  <li>{linha.strip()}</li>\n"
                    texto_formatado += "</ul>"
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    if url:
                        texto_formatado = f'<a href="{url}">{texto_selecionado}</a>'
                    else:
                        return
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    if url:
                        alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                        alt = alt or texto_selecionado or "Imagem"
                        texto_formatado = f'<img src="{url}" alt="{alt}" style="max-width: 100%;">'
                    else:
                        return
                
                # Substitui o texto selecionado pelo texto formatado
                self.text_mensagem_agendamento.delete(inicio, fim)
                self.text_mensagem_agendamento.insert(inicio, texto_formatado)
            else:
                # Se não houver texto selecionado
                if tipo == "lista":
                    self.text_mensagem_agendamento.insert(tk.INSERT, "<ul>\n  <li></li>\n</ul>")
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    texto = simpledialog.askstring("Texto do Link", "Digite o texto que será exibido:")
                    if url and texto:
                        self.text_mensagem_agendamento.insert(tk.INSERT, f'<a href="{url}">{texto}</a>')
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                    if url:
                        alt = alt or "Imagem"
                        self.text_mensagem_agendamento.insert(tk.INSERT, f'<img src="{url}" alt="{alt}" style="max-width: 100%;">')
        except Exception as e:
            logger.error(f"Erro ao formatar texto em agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao aplicar formatação: {e}")
    
    def formatar_texto_template(self, tipo):
        """Aplica formatação ao texto selecionado no editor de template."""
        try:
            # Obtém o texto selecionado
            if self.text_conteudo_template.tag_ranges("sel"):
                inicio, fim = self.text_conteudo_template.tag_ranges("sel")
                texto_selecionado = self.text_conteudo_template.get(inicio, fim)
                
                if tipo == "negrito":
                    texto_formatado = f"<b>{texto_selecionado}</b>"
                elif tipo == "italico":
                    texto_formatado = f"<i>{texto_selecionado}</i>"
                elif tipo == "sublinhado":
                    texto_formatado = f"<u>{texto_selecionado}</u>"
                elif tipo == "lista":
                    linhas = texto_selecionado.split("\n")
                    texto_formatado = "<ul>\n"
                    for linha in linhas:
                        if linha.strip():
                            texto_formatado += f"  <li>{linha.strip()}</li>\n"
                    texto_formatado += "</ul>"
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    if url:
                        texto_formatado = f'<a href="{url}">{texto_selecionado}</a>'
                    else:
                        return
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    if url:
                        alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                        alt = alt or texto_selecionado or "Imagem"
                        texto_formatado = f'<img src="{url}" alt="{alt}" style="max-width: 100%;">'
                    else:
                        return
                
                # Substitui o texto selecionado pelo texto formatado
                self.text_conteudo_template.delete(inicio, fim)
                self.text_conteudo_template.insert(inicio, texto_formatado)
            else:
                # Se não houver texto selecionado
                if tipo == "lista":
                    self.text_conteudo_template.insert(tk.INSERT, "<ul>\n  <li></li>\n</ul>")
                elif tipo == "link":
                    url = simpledialog.askstring("Inserir Link", "Digite a URL:")
                    texto = simpledialog.askstring("Texto do Link", "Digite o texto que será exibido:")
                    if url and texto:
                        self.text_conteudo_template.insert(tk.INSERT, f'<a href="{url}">{texto}</a>')
                elif tipo == "imagem":
                    url = simpledialog.askstring("Inserir Imagem", "Digite a URL da imagem:")
                    alt = simpledialog.askstring("Texto Alternativo", "Digite o texto alternativo:")
                    if url:
                        alt = alt or "Imagem"
                        self.text_conteudo_template.insert(tk.INSERT, f'<img src="{url}" alt="{alt}" style="max-width: 100%;">')
        except Exception as e:
            logger.error(f"Erro ao formatar texto em template: {e}")
            messagebox.showerror("Erro", f"Falha ao aplicar formatação: {e}")
    
    def inserir_variaveis(self):
        """Insere variáveis de template no texto."""
        try:
            # Lista de variáveis disponíveis
            variaveis = [
                "{nome}", "{email}", "{cargo}", "{departamento}", "{telefone}", 
                "{data}", "{hora}", "{prefeitura}"
            ]
            
            # Cria janela de seleção
            janela_variaveis = tk.Toplevel(self.root)
            janela_variaveis.title("Inserir Variável")
            janela_variaveis.geometry("300x300")
            janela_variaveis.minsize(300, 300)
            
            ttk.Label(janela_variaveis, text="Selecione a variável a inserir:").pack(pady=10)
            
            # Frame para lista
            frame_lista = ttk.Frame(janela_variaveis)
            frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Listbox com as variáveis
            listbox_variaveis = tk.Listbox(frame_lista, width=30, height=10)
            listbox_variaveis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for var in variaveis:
                listbox_variaveis.insert(tk.END, var)
            
            scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=listbox_variaveis.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox_variaveis.config(yscrollcommand=scrollbar.set)
            
            # Função para inserir a variável selecionada
            def inserir_variavel_selecionada():
                selecionado = listbox_variaveis.curselection()
                if selecionado:
                    variavel = listbox_variaveis.get(selecionado[0])
                    self.text_mensagem_massa.insert(tk.INSERT, variavel)
                    janela_variaveis.destroy()
            
            # Função para inserir ao dar duplo clique
            def inserir_variavel_duplo_clique(event):
                inserir_variavel_selecionada()
            
            listbox_variaveis.bind("<Double-1>", inserir_variavel_duplo_clique)
            
            # Botões
            frame_botoes = ttk.Frame(janela_variaveis)
            frame_botoes.pack(fill=tk.X, padx=10, pady=10)
            
            btn_inserir = ttk.Button(frame_botoes, text="Inserir", command=inserir_variavel_selecionada)
            btn_inserir.pack(side=tk.RIGHT, padx=5)
            
            btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_variaveis.destroy)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Configura para modal e focus
            janela_variaveis.transient(self.root)
            janela_variaveis.grab_set()
            janela_variaveis.focus_set()
            
        except Exception as e:
            logger.error(f"Erro ao inserir variáveis: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir seleção de variáveis: {e}")
    
    def inserir_variaveis_agendamento(self):
        """Insere variáveis de template no texto de agendamento."""
        try:
            # Lista de variáveis disponíveis
            variaveis = [
                "{nome}", "{email}", "{cargo}", "{departamento}", "{telefone}", 
                "{data}", "{hora}", "{prefeitura}"
            ]
            
            # Cria janela de seleção
            janela_variaveis = tk.Toplevel(self.root)
            janela_variaveis.title("Inserir Variável")
            janela_variaveis.geometry("300x300")
            janela_variaveis.minsize(300, 300)
            
            ttk.Label(janela_variaveis, text="Selecione a variável a inserir:").pack(pady=10)
            
            # Frame para lista
            frame_lista = ttk.Frame(janela_variaveis)
            frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Listbox com as variáveis
            listbox_variaveis = tk.Listbox(frame_lista, width=30, height=10)
            listbox_variaveis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for var in variaveis:
                listbox_variaveis.insert(tk.END, var)
            
            scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=listbox_variaveis.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox_variaveis.config(yscrollcommand=scrollbar.set)
            
            # Função para inserir a variável selecionada
            def inserir_variavel_selecionada():
                selecionado = listbox_variaveis.curselection()
                if selecionado:
                    variavel = listbox_variaveis.get(selecionado[0])
                    self.text_mensagem_agendamento.insert(tk.INSERT, variavel)
                    janela_variaveis.destroy()
            
            # Função para inserir ao dar duplo clique
            def inserir_variavel_duplo_clique(event):
                inserir_variavel_selecionada()
            
            listbox_variaveis.bind("<Double-1>", inserir_variavel_duplo_clique)
            
            # Botões
            frame_botoes = ttk.Frame(janela_variaveis)
            frame_botoes.pack(fill=tk.X, padx=10, pady=10)
            
            btn_inserir = ttk.Button(frame_botoes, text="Inserir", command=inserir_variavel_selecionada)
            btn_inserir.pack(side=tk.RIGHT, padx=5)
            
            btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_variaveis.destroy)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Configura para modal e focus
            janela_variaveis.transient(self.root)
            janela_variaveis.grab_set()
            janela_variaveis.focus_set()
            
        except Exception as e:
            logger.error(f"Erro ao inserir variáveis em agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir seleção de variáveis: {e}")
    
    def inserir_variaveis_template(self):
        """Insere variáveis de template no editor de template."""
        try:
            # Lista de variáveis disponíveis
            variaveis = [
                "{nome}", "{email}", "{cargo}", "{departamento}", "{telefone}", 
                "{data}", "{hora}", "{prefeitura}"
            ]
            
            # Cria janela de seleção
            janela_variaveis = tk.Toplevel(self.root)
            janela_variaveis.title("Inserir Variável")
            janela_variaveis.geometry("300x300")
            janela_variaveis.minsize(300, 300)
            
            ttk.Label(janela_variaveis, text="Selecione a variável a inserir:").pack(pady=10)
            
            # Frame para lista
            frame_lista = ttk.Frame(janela_variaveis)
            frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Listbox com as variáveis
            listbox_variaveis = tk.Listbox(frame_lista, width=30, height=10)
            listbox_variaveis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for var in variaveis:
                listbox_variaveis.insert(tk.END, var)
            
            scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=listbox_variaveis.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox_variaveis.config(yscrollcommand=scrollbar.set)
            
            # Função para inserir a variável selecionada
            def inserir_variavel_selecionada():
                selecionado = listbox_variaveis.curselection()
                if selecionado:
                    variavel = listbox_variaveis.get(selecionado[0])
                    self.text_conteudo_template.insert(tk.INSERT, variavel)
                    janela_variaveis.destroy()
            
            # Função para inserir ao dar duplo clique
            def inserir_variavel_duplo_clique(event):
                inserir_variavel_selecionada()
            
            listbox_variaveis.bind("<Double-1>", inserir_variavel_duplo_clique)
            
            # Botões
            frame_botoes = ttk.Frame(janela_variaveis)
            frame_botoes.pack(fill=tk.X, padx=10, pady=10)
            
            btn_inserir = ttk.Button(frame_botoes, text="Inserir", command=inserir_variavel_selecionada)
            btn_inserir.pack(side=tk.RIGHT, padx=5)
            
            btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_variaveis.destroy)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Configura para modal e focus
            janela_variaveis.transient(self.root)
            janela_variaveis.grab_set()
            janela_variaveis.focus_set()
            
        except Exception as e:
            logger.error(f"Erro ao inserir variáveis em template: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir seleção de variáveis: {e}")
    
    def adicionar_anexo(self):
        """Adiciona um anexo ao e-mail individual."""
        try:
            filetypes = [
                ('Todos os arquivos', '*.*'),
                ('Documentos', '*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt'),
                ('Imagens', '*.jpg *.jpeg *.png *.gif *.bmp'),
                ('Arquivos ZIP', '*.zip *.rar')
            ]
            
            filename = filedialog.askopenfilename(
                title="Selecionar Anexo",
                filetypes=filetypes
            )
            
            if filename:
                # Verifica o tamanho do arquivo
                tamanho = os.path.getsize(filename)
                
                # Limite de 10MB
                if tamanho > 10 * 1024 * 1024:
                    messagebox.showwarning(
                        "Arquivo Grande", 
                        "O arquivo selecionado é maior que 10MB. Isso pode causar problemas no envio do e-mail."
                    )
                
                # Adiciona à lista de anexos
                self.anexos.append(filename)
                
                # Exibe na tabela
                nome_arquivo = os.path.basename(filename)
                tamanho_formatado = self.formatar_tamanho(tamanho)
                
                self.lista_anexos.insert("", tk.END, values=(nome_arquivo, tamanho_formatado))
                
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo: {e}")
            messagebox.showerror("Erro", f"Não foi possível adicionar o anexo: {e}")
    
    def adicionar_anexo_massa(self):
        """Adiciona um anexo ao e-mail em massa."""
        try:
            filetypes = [
                ('Todos os arquivos', '*.*'),
                ('Documentos', '*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt'),
                ('Imagens', '*.jpg *.jpeg *.png *.gif *.bmp'),
                ('Arquivos ZIP', '*.zip *.rar')
            ]
            
            filename = filedialog.askopenfilename(
                title="Selecionar Anexo",
                filetypes=filetypes
            )
            
            if filename:
                # Verifica o tamanho do arquivo
                tamanho = os.path.getsize(filename)
                
                # Limite de 10MB
                if tamanho > 10 * 1024 * 1024:
                    messagebox.showwarning(
                        "Arquivo Grande", 
                        "O arquivo selecionado é maior que 10MB. Isso pode causar problemas no envio do e-mail."
                    )
                
                # Adiciona à lista de anexos
                self.anexos_massa.append(filename)
                
                # Exibe na tabela
                nome_arquivo = os.path.basename(filename)
                tamanho_formatado = self.formatar_tamanho(tamanho)
                
                self.lista_anexos_massa.insert("", tk.END, values=(nome_arquivo, tamanho_formatado))
                
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo em massa: {e}")
            messagebox.showerror("Erro", f"Não foi possível adicionar o anexo: {e}")
    
    def adicionar_anexo_agendamento(self):
        """Adiciona um anexo ao e-mail agendado."""
        try:
            filetypes = [
                ('Todos os arquivos', '*.*'),
                ('Documentos', '*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt'),
                ('Imagens', '*.jpg *.jpeg *.png *.gif *.bmp'),
                ('Arquivos ZIP', '*.zip *.rar')
            ]
            
            filename = filedialog.askopenfilename(
                title="Selecionar Anexo",
                filetypes=filetypes
            )
            
            if filename:
                # Verifica o tamanho do arquivo
                tamanho = os.path.getsize(filename)
                
                # Limite de 10MB
                if tamanho > 10 * 1024 * 1024:
                    messagebox.showwarning(
                        "Arquivo Grande", 
                        "O arquivo selecionado é maior que 10MB. Isso pode causar problemas no envio do e-mail."
                    )
                
                # Adiciona à lista de anexos
                self.anexos_agendamento.append(filename)
                
                # Exibe na tabela
                nome_arquivo = os.path.basename(filename)
                tamanho_formatado = self.formatar_tamanho(tamanho)
                
                self.lista_anexos_agendamento.insert("", tk.END, values=(nome_arquivo, tamanho_formatado))
                
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo em agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível adicionar o anexo: {e}")
    
    def remover_anexo(self):
        """Remove um anexo da lista de anexos do e-mail individual."""
        try:
            selecionado = self.lista_anexos.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um anexo para remover.")
                return
            
            # Obtém o índice do item selecionado
            indice = self.lista_anexos.index(selecionado[0])
            
            # Remove da lista de anexos
            if 0 <= indice < len(self.anexos):
                del self.anexos[indice]
            
            # Remove da tabela
            self.lista_anexos.delete(selecionado[0])
            
        except Exception as e:
            logger.error(f"Erro ao remover anexo: {e}")
            messagebox.showerror("Erro", f"Não foi possível remover o anexo: {e}")
    
    def remover_anexo_massa(self):
        """Remove um anexo da lista de anexos do e-mail em massa."""
        try:
            selecionado = self.lista_anexos_massa.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um anexo para remover.")
                return
            
            # Obtém o índice do item selecionado
            indice = self.lista_anexos_massa.index(selecionado[0])
            
            # Remove da lista de anexos
            if 0 <= indice < len(self.anexos_massa):
                del self.anexos_massa[indice]
            
            # Remove da tabela
            self.lista_anexos_massa.delete(selecionado[0])
            
        except Exception as e:
            logger.error(f"Erro ao remover anexo em massa: {e}")
            messagebox.showerror("Erro", f"Não foi possível remover o anexo: {e}")
    
    def remover_anexo_agendamento(self):
        """Remove um anexo da lista de anexos do e-mail agendado."""
        try:
            selecionado = self.lista_anexos_agendamento.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um anexo para remover.")
                return
            
            # Obtém o índice do item selecionado
            indice = self.lista_anexos_agendamento.index(selecionado[0])
            
            # Remove da lista de anexos
            if 0 <= indice < len(self.anexos_agendamento):
                del self.anexos_agendamento[indice]
            
            # Remove da tabela
            self.lista_anexos_agendamento.delete(selecionado[0])
            
        except Exception as e:
            logger.error(f"Erro ao remover anexo em agendamento: {e}")
            messagebox.showerror("Erro", f"Não foi possível remover o anexo: {e}")
    
    def formatar_tamanho(self, tamanho):
      # """Formata o tamanho do arquivo em uma string legível."""
      for unidade in ['B', 'KB', 'MB', 'GB']:
          if tamanho < 1024:
              return f"{tamanho} {unidade}"
          tamanho /= 1024
          if tamanho < 1024:
              return f"{tamanho:.2f} {unidade}"
      return f"{tamanho:.2f} GB"
    
    def previsualizar_email(self):
        """Exibe uma prévia do e-mail individual."""
        try:
            destinatario = self.entry_destinatario.get().strip()
            assunto = self.entry_assunto.get().strip()
            conteudo = self.text_mensagem.get(1.0, tk.END).strip()
            
            if not destinatario or not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios.")
                return
            
            # Prepara o conteúdo com a assinatura
            conteudo_completo = conteudo
            
            if self.assinatura_var.get():
                conteudo_completo += self.obter_assinatura()
            
            # Cria janela de prévia
            janela_preview = tk.Toplevel(self.root)
            janela_preview.title("Pré-visualização do E-mail")
            janela_preview.geometry("800x600")
            janela_preview.minsize(600, 400)
            
            frame_preview = ttk.Frame(janela_preview, padding=10)
            frame_preview.pack(fill=tk.BOTH, expand=True)
            
            # Informações do e-mail
            ttk.Label(frame_preview, text=f"Para: {destinatario}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(frame_preview, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para o conteúdo HTML
            frame_html = ttk.Frame(frame_preview)
            frame_html.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Usar um Text widget com configuração de HTML
            html_view = tk.Text(frame_html, wrap=tk.WORD, font=('Helvetica', 10))
            html_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_html = ttk.Scrollbar(frame_html, orient=tk.VERTICAL, command=html_view.yview)
            scrollbar_html.pack(side=tk.RIGHT, fill=tk.Y)
            html_view.config(yscrollcommand=scrollbar_html.set)
            
            # Insere o conteúdo
            html_view.insert(tk.END, conteudo_completo)
            
            # Configura tags para formatação básica de HTML
            html_view.tag_configure("bold", font=('Helvetica', 10, 'bold'))
            html_view.tag_configure("italic", font=('Helvetica', 10, 'italic'))
            html_view.tag_configure("underline", underline=True)
            
            # Aplica formatação básica (simplificada)
            self.aplicar_formatacao_html(html_view)
            
            html_view.config(state=tk.DISABLED)
            
            # Anexos
            if self.anexos:
                ttk.Label(frame_preview, text="Anexos:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                for i, anexo in enumerate(self.anexos):
                    nome_arquivo = os.path.basename(anexo)
                    tamanho = os.path.getsize(anexo)
                    tamanho_formatado = self.formatar_tamanho(tamanho)
                    
                    ttk.Label(frame_preview, text=f"{i+1}. {nome_arquivo} ({tamanho_formatado})").pack(anchor=tk.W)
            
            # Botão para fechar
            ttk.Button(janela_preview, text="Fechar", command=janela_preview.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erro ao pré-visualizar e-mail: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar pré-visualização: {e}")
    
    def previsualizar_email_massa(self):
        """Exibe uma prévia do e-mail em massa."""
        try:
            assunto = self.entry_assunto_massa.get().strip()
            conteudo = self.text_mensagem_massa.get(1.0, tk.END).strip()
            
            if not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha o assunto e o conteúdo do e-mail.")
                return
            
            # Verifica se há destinatários selecionados
            if self.lista_preview.get_children():
                # Pega o primeiro destinatário para exemplo
                valores = self.lista_preview.item(self.lista_preview.get_children()[0], 'values')
                destinatario_exemplo = valores[0]
                nome_exemplo = valores[1] if valores[1] else "Nome do Destinatário"
                cargo_exemplo = "Cargo do Destinatário"
                departamento_exemplo = valores[2] if valores[2] else "Departamento"
                telefone_exemplo = "Telefone do Destinatário"
            else:
                destinatario_exemplo = "exemplo@email.com"
                nome_exemplo = "Nome do Destinatário"
                cargo_exemplo = "Cargo do Destinatário"
                departamento_exemplo = "Departamento"
                telefone_exemplo = "Telefone do Destinatário"
            
            # Substitui variáveis no conteúdo
            conteudo_exemplo = conteudo.replace("{nome}", nome_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{email}", destinatario_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{cargo}", cargo_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{departamento}", departamento_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{telefone}", telefone_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{data}", datetime.datetime.now().strftime("%d/%m/%Y"))
            conteudo_exemplo = conteudo_exemplo.replace("{hora}", datetime.datetime.now().strftime("%H:%M"))
            conteudo_exemplo = conteudo_exemplo.replace("{prefeitura}", "São José" if self.prefeitura_atual == 'sj' else "Florianópolis")
            
            # Adiciona assinatura se selecionado
            if self.assinatura_massa_var.get():
                conteudo_exemplo += self.obter_assinatura(nome_exemplo, cargo_exemplo, departamento_exemplo, telefone_exemplo)
            
            # Cria janela de prévia
            janela_preview = tk.Toplevel(self.root)
            janela_preview.title("Pré-visualização do E-mail em Massa")
            janela_preview.geometry("800x600")
            janela_preview.minsize(600, 400)
            
            frame_preview = ttk.Frame(janela_preview, padding=10)
            frame_preview.pack(fill=tk.BOTH, expand=True)
            
            # Informações do e-mail
            ttk.Label(frame_preview, text=f"Exemplo para: {destinatario_exemplo}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(frame_preview, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para o conteúdo HTML
            frame_html = ttk.Frame(frame_preview)
            frame_html.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Usar um Text widget com configuração de HTML
            html_view = tk.Text(frame_html, wrap=tk.WORD, font=('Helvetica', 10))
            html_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_html = ttk.Scrollbar(frame_html, orient=tk.VERTICAL, command=html_view.yview)
            scrollbar_html.pack(side=tk.RIGHT, fill=tk.Y)
            html_view.config(yscrollcommand=scrollbar_html.set)
            
            # Insere o conteúdo
            html_view.insert(tk.END, conteudo_exemplo)
            
            # Configura tags para formatação básica de HTML
            html_view.tag_configure("bold", font=('Helvetica', 10, 'bold'))
            html_view.tag_configure("italic", font=('Helvetica', 10, 'italic'))
            html_view.tag_configure("underline", underline=True)
            
            # Aplica formatação básica (simplificada)
            self.aplicar_formatacao_html(html_view)
            
            html_view.config(state=tk.DISABLED)
            
            # Anexos
            if self.anexos_massa:
                ttk.Label(frame_preview, text="Anexos:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                for i, anexo in enumerate(self.anexos_massa):
                    nome_arquivo = os.path.basename(anexo)
                    tamanho = os.path.getsize(anexo)
                    tamanho_formatado = self.formatar_tamanho(tamanho)
                    
                    ttk.Label(frame_preview, text=f"{i+1}. {nome_arquivo} ({tamanho_formatado})").pack(anchor=tk.W)
            
            # Informações do envio em massa
            ttk.Separator(frame_preview, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            total_destinatarios = len(self.lista_preview.get_children())
            ttk.Label(frame_preview, text=f"Total de destinatários: {total_destinatarios}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
            
            limite = self.limite_emails_var.get()
            intervalo = self.intervalo_emails_var.get()
            ttk.Label(frame_preview, text=f"Configuração de envio: Limite de {limite} e-mails por hora, com intervalo de {intervalo} segundos").pack(anchor=tk.W)
            
            # Botão para fechar
            ttk.Button(janela_preview, text="Fechar", command=janela_preview.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erro ao pré-visualizar e-mail em massa: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar pré-visualização: {e}")
    
    def previsualizar_email_agendamento(self):
        """Exibe uma prévia do e-mail agendado."""
        try:
            assunto = self.entry_assunto_agendamento.get().strip()
            conteudo = self.text_mensagem_agendamento.get(1.0, tk.END).strip()
            
            if not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha o assunto e o conteúdo do e-mail.")
                return
            
            # Verifica se há destinatários selecionados
            if self.lista_preview_agendamento.get_children():
                # Pega o primeiro destinatário para exemplo
                valores = self.lista_preview_agendamento.item(self.lista_preview_agendamento.get_children()[0], 'values')
                destinatario_exemplo = valores[0]
                nome_exemplo = valores[1] if valores[1] else "Nome do Destinatário"
                cargo_exemplo = "Cargo do Destinatário"
                departamento_exemplo = valores[2] if valores[2] else "Departamento"
                telefone_exemplo = "Telefone do Destinatário"
            else:
                destinatario_exemplo = "exemplo@email.com"
                nome_exemplo = "Nome do Destinatário"
                cargo_exemplo = "Cargo do Destinatário"
                departamento_exemplo = "Departamento"
                telefone_exemplo = "Telefone do Destinatário"
            
            # Substitui variáveis no conteúdo
            conteudo_exemplo = conteudo.replace("{nome}", nome_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{email}", destinatario_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{cargo}", cargo_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{departamento}", departamento_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{telefone}", telefone_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{data}", datetime.datetime.now().strftime("%d/%m/%Y"))
            conteudo_exemplo = conteudo_exemplo.replace("{hora}", datetime.datetime.now().strftime("%H:%M"))
            conteudo_exemplo = conteudo_exemplo.replace("{prefeitura}", "São José" if self.prefeitura_atual == 'sj' else "Florianópolis")
            
            # Adiciona assinatura se selecionado
            if self.assinatura_agendamento_var.get():
                conteudo_exemplo += self.obter_assinatura(nome_exemplo, cargo_exemplo, departamento_exemplo, telefone_exemplo)
            
            # Cria janela de prévia
            janela_preview = tk.Toplevel(self.root)
            janela_preview.title("Pré-visualização do E-mail Agendado")
            janela_preview.geometry("800x600")
            janela_preview.minsize(600, 400)
            
            frame_preview = ttk.Frame(janela_preview, padding=10)
            frame_preview.pack(fill=tk.BOTH, expand=True)
            
            # Informações do e-mail
            ttk.Label(frame_preview, text=f"Exemplo para: {destinatario_exemplo}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(frame_preview, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para o conteúdo HTML
            frame_html = ttk.Frame(frame_preview)
            frame_html.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Usar um Text widget com configuração de HTML
            html_view = tk.Text(frame_html, wrap=tk.WORD, font=('Helvetica', 10))
            html_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_html = ttk.Scrollbar(frame_html, orient=tk.VERTICAL, command=html_view.yview)
            scrollbar_html.pack(side=tk.RIGHT, fill=tk.Y)
            html_view.config(yscrollcommand=scrollbar_html.set)
            
            # Insere o conteúdo
            html_view.insert(tk.END, conteudo_exemplo)
            
            # Configura tags para formatação básica de HTML
            html_view.tag_configure("bold", font=('Helvetica', 10, 'bold'))
            html_view.tag_configure("italic", font=('Helvetica', 10, 'italic'))
            html_view.tag_configure("underline", underline=True)
            
            # Aplica formatação básica (simplificada)
            self.aplicar_formatacao_html(html_view)
            
            html_view.config(state=tk.DISABLED)
            
            # Anexos
            if self.anexos_agendamento:
                ttk.Label(frame_preview, text="Anexos:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                for i, anexo in enumerate(self.anexos_agendamento):
                    nome_arquivo = os.path.basename(anexo)
                    tamanho = os.path.getsize(anexo)
                    tamanho_formatado = self.formatar_tamanho(tamanho)
                    
                    ttk.Label(frame_preview, text=f"{i+1}. {nome_arquivo} ({tamanho_formatado})").pack(anchor=tk.W)
            
            # Informações de agendamento
            ttk.Separator(frame_preview, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
            
            data_agendada = self.data_agendamento.get_date().strftime("%d/%m/%Y")
            hora_agendada = f"{self.hora_var.get()}:{self.minuto_var.get()}"
            recorrencia = self.recorrencia_var.get().capitalize()
            
            ttk.Label(frame_preview, text=f"Agendamento: {data_agendada} às {hora_agendada}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(frame_preview, text=f"Recorrência: {recorrencia}").pack(anchor=tk.W)
            
            # Botão para fechar
            ttk.Button(janela_preview, text="Fechar", command=janela_preview.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erro ao pré-visualizar e-mail agendado: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar pré-visualização: {e}")
    
    def previsualizar_template(self):
        """Exibe uma prévia do template."""
        try:
            nome = self.entry_nome_template.get().strip()
            assunto = self.entry_assunto_template.get().strip()
            conteudo = self.text_conteudo_template.get(1.0, tk.END).strip()
            
            if not nome or not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios.")
                return
            
            # Substitui variáveis com valores de exemplo
            nome_exemplo = "Nome do Destinatário"
            email_exemplo = "exemplo@email.com"
            cargo_exemplo = "Cargo do Destinatário"
            departamento_exemplo = self.combo_departamento_template.get() or "Departamento"
            telefone_exemplo = "Telefone do Destinatário"
            
            conteudo_exemplo = conteudo.replace("{nome}", nome_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{email}", email_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{cargo}", cargo_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{departamento}", departamento_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{telefone}", telefone_exemplo)
            conteudo_exemplo = conteudo_exemplo.replace("{data}", datetime.datetime.now().strftime("%d/%m/%Y"))
            conteudo_exemplo = conteudo_exemplo.replace("{hora}", datetime.datetime.now().strftime("%H:%M"))
            conteudo_exemplo = conteudo_exemplo.replace("{prefeitura}", "São José" if self.prefeitura_atual == 'sj' else "Florianópolis")
            
            # Cria janela de prévia
            janela_preview = tk.Toplevel(self.root)
            janela_preview.title(f"Pré-visualização do Template: {nome}")
            janela_preview.geometry("800x600")
            janela_preview.minsize(600, 400)
            
            frame_preview = ttk.Frame(janela_preview, padding=10)
            frame_preview.pack(fill=tk.BOTH, expand=True)
            
            # Informações do template
            ttk.Label(frame_preview, text=f"Nome: {nome}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(frame_preview, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            ttk.Label(frame_preview, text=f"Departamento: {departamento_exemplo}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para o conteúdo HTML
            frame_html = ttk.Frame(frame_preview)
            frame_html.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Usar um Text widget com configuração de HTML
            html_view = tk.Text(frame_html, wrap=tk.WORD, font=('Helvetica', 10))
            html_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_html = ttk.Scrollbar(frame_html, orient=tk.VERTICAL, command=html_view.yview)
            scrollbar_html.pack(side=tk.RIGHT, fill=tk.Y)
            html_view.config(yscrollcommand=scrollbar_html.set)
            
            # Insere o conteúdo
            html_view.insert(tk.END, conteudo_exemplo)
            
            # Configura tags para formatação básica de HTML
            html_view.tag_configure("bold", font=('Helvetica', 10, 'bold'))
            html_view.tag_configure("italic", font=('Helvetica', 10, 'italic'))
            html_view.tag_configure("underline", underline=True)
            
            # Aplica formatação básica (simplificada)
            self.aplicar_formatacao_html(html_view)
            
            html_view.config(state=tk.DISABLED)
            
            # Botão para fechar
            ttk.Button(janela_preview, text="Fechar", command=janela_preview.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erro ao pré-visualizar template: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar pré-visualização: {e}")
    
    def aplicar_formatacao_html(self, text_widget):
        """Aplica formatação básica de HTML no widget de texto (simplificada)."""
        try:
            conteudo = text_widget.get(1.0, tk.END)
            
            # Aplicar tags de formatação básica (simplificada)
            # Negrito
            pos = 1.0
            while True:
                pos = text_widget.search("<b>", pos, tk.END)
                if not pos:
                    break
                
                inicio_tag = pos
                fim_tag = text_widget.search("</b>", pos, tk.END)
                
                if not fim_tag:
                    break
                
                # Calcula posições ajustadas
                inicio_texto = text_widget.index(f"{inicio_tag}+3c")
                fim_texto = fim_tag
                
                # Aplica tag
                text_widget.tag_add("bold", inicio_texto, fim_texto)
                
                # Avança para a próxima ocorrência
                pos = text_widget.index(f"{fim_tag}+4c")
            
            # Itálico
            pos = 1.0
            while True:
                pos = text_widget.search("<i>", pos, tk.END)
                if not pos:
                    break
                
                inicio_tag = pos
                fim_tag = text_widget.search("</i>", pos, tk.END)
                
                if not fim_tag:
                    break
                
                # Calcula posições ajustadas
                inicio_texto = text_widget.index(f"{inicio_tag}+3c")
                fim_texto = fim_tag
                
                # Aplica tag
                text_widget.tag_add("italic", inicio_texto, fim_texto)
                
                # Avança para a próxima ocorrência
                pos = text_widget.index(f"{fim_tag}+4c")
            
            # Sublinhado
            pos = 1.0
            while True:
                pos = text_widget.search("<u>", pos, tk.END)
                if not pos:
                    break
                
                inicio_tag = pos
                fim_tag = text_widget.search("</u>", pos, tk.END)
                
                if not fim_tag:
                    break
                
                # Calcula posições ajustadas
                inicio_texto = text_widget.index(f"{inicio_tag}+3c")
                fim_texto = fim_tag
                
                # Aplica tag
                text_widget.tag_add("underline", inicio_texto, fim_texto)
                
                # Avança para a próxima ocorrência
                pos = text_widget.index(f"{fim_tag}+4c")
        
        except Exception as e:
            logger.error(f"Erro ao aplicar formatação HTML: {e}")
    
    def obter_assinatura(self, nome=None, cargo=None, departamento=None, telefone=None):
        """Obtém a assinatura formatada com os dados do usuário."""
        try:
            # Obtém o template de assinatura da prefeitura atual
            assinatura_template = self.config.get('assinaturas', {}).get(
                self.prefeitura_atual, {}).get('padrao', '')
            
            if not assinatura_template:
                return ""
            
            # Dados para substituição
            nome = nome or self.usuario_atual.get('nome', '')
            cargo = cargo or ''
            departamento = departamento or ''
            telefone = telefone or ''
            
            # Substitui as variáveis
            assinatura = assinatura_template.replace("{nome}", nome)
            assinatura = assinatura.replace("{cargo}", cargo)
            assinatura = assinatura.replace("{departamento}", departamento)
            assinatura = assinatura.replace("{telefone}", telefone)
            
            return f"\n\n{assinatura}"
        except Exception as e:
            logger.error(f"Erro ao obter assinatura: {e}")
            return ""
    
    def enviar_email_individual(self):
        """Envia um e-mail individual."""
        try:
            destinatario = self.entry_destinatario.get().strip()
            assunto = self.entry_assunto.get().strip()
            conteudo = self.text_mensagem.get(1.0, tk.END).strip()
            
            if not destinatario or not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios.")
                return
            
            # Validação básica de e-mail
            import re
            padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(padrao_email, destinatario):
                messagebox.showwarning("Aviso", "O e-mail do destinatário parece ser inválido.")
                return
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja enviar este e-mail para {destinatario}?"):
                return
            
            # Prepara o conteúdo com a assinatura
            conteudo_completo = conteudo
            
            if self.assinatura_var.get():
                conteudo_completo += self.obter_assinatura()
            
            # Envia o e-mail
            status = self.enviar_email(
                destinatarios=[destinatario],
                assunto=assunto,
                conteudo=conteudo_completo,
                anexos=self.anexos
            )
            
            if status:
                messagebox.showinfo("Sucesso", "E-mail enviado com sucesso!")
                self.limpar_campos_email()
            else:
                messagebox.showerror("Erro", "Não foi possível enviar o e-mail. Verifique as configurações SMTP.")
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail individual: {e}")
            messagebox.showerror("Erro", f"Falha ao enviar e-mail: {e}")
    
    def enviar_emails_massa(self):
        """Envia e-mails em massa para os destinatários selecionados."""
        try:
            assunto = self.entry_assunto_massa.get().strip()
            conteudo = self.text_mensagem_massa.get(1.0, tk.END).strip()
            
            if not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha o assunto e o conteúdo do e-mail.")
                return
            
            # Obtém a lista de destinatários
            destinatarios = []
            info_destinatarios = []
            
            for item in self.lista_preview.get_children():
                valores = self.lista_preview.item(item, 'values')
                email = valores[0]
                nome = valores[1] if valores[1] else ""
                departamento = valores[2] if valores[2] else ""
                
                destinatarios.append(email)
                info_destinatarios.append({
                    'email': email,
                    'nome': nome,
                    'departamento': departamento,
                    'cargo': '',
                    'telefone': ''
                })
            
            if not destinatarios:
                messagebox.showwarning("Aviso", "Selecione pelo menos um destinatário.")
                return
            
            # Confirmação
            if not messagebox.askyesno(
                "Confirmação", 
                f"Deseja enviar este e-mail para {len(destinatarios)} destinatários?\n\n"
                f"Esta operação pode levar algum tempo, dependendo da quantidade de destinatários."
            ):
                return
            
            # Obtém as configurações de envio
            try:
                limite_emails = int(self.limite_emails_var.get())
                intervalo_segundos = float(self.intervalo_emails_var.get())
            except ValueError:
                messagebox.showwarning("Aviso", "Os valores de limite e intervalo devem ser numéricos.")
                return
            
            # Cria janela de progresso
            janela_progresso = tk.Toplevel(self.root)
            janela_progresso.title("Enviando E-mails em Massa")
            janela_progresso.geometry("500x300")
            janela_progresso.minsize(500, 300)
            janela_progresso.transient(self.root)
            janela_progresso.grab_set()
            
            frame_progresso = ttk.Frame(janela_progresso, padding=20)
            frame_progresso.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame_progresso, text="Enviando e-mails...", font=('Helvetica', 12, 'bold')).pack(pady=(0, 10))
            
            # Barra de progresso
            progresso_var = tk.DoubleVar()
            barra_progresso = ttk.Progressbar(frame_progresso, variable=progresso_var, maximum=len(destinatarios))
            barra_progresso.pack(fill=tk.X, pady=10)
            
            # Informações de progresso
            lbl_info = ttk.Label(frame_progresso, text="Preparando...")
            lbl_info.pack(pady=5)
            
            lbl_atual = ttk.Label(frame_progresso, text="")
            lbl_atual.pack(pady=5)
            
            lbl_contador = ttk.Label(frame_progresso, text="0 de 0 enviados")
            lbl_contador.pack(pady=5)
            
            # Frame para log
            frame_log = ttk.LabelFrame(frame_progresso, text="Log de Envio")
            frame_log.pack(fill=tk.BOTH, expand=True, pady=10)
            
            text_log = tk.Text(frame_log, height=8, width=50)
            text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_log = ttk.Scrollbar(frame_log, orient=tk.VERTICAL, command=text_log.yview)
            scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)
            text_log.config(yscrollcommand=scrollbar_log.set)
            
            # Botão para cancelar
            cancelar_var = tk.BooleanVar(value=False)
            
            def cancelar_envio():
                if messagebox.askyesno("Cancelar", "Deseja realmente cancelar o envio?"):
                    cancelar_var.set(True)
                    btn_cancelar.config(text="Cancelando...", state=tk.DISABLED)
            
            btn_cancelar = ttk.Button(janela_progresso, text="Cancelar", command=cancelar_envio)
            btn_cancelar.pack(pady=10)
            
            # Atualiza a interface
            janela_progresso.update()
            
            # Função que será executada em uma thread separada
            def enviar_emails_thread():
                try:
                    # Prepara a assinatura
                    assinatura_padrao = self.obter_assinatura() if self.assinatura_massa_var.get() else ""
                    
                    enviados = 0
                    falhas = 0
                    
                    for i, (destinatario, info) in enumerate(zip(destinatarios, info_destinatarios)):
                        if cancelar_var.get():
                            text_log.insert(tk.END, "Envio cancelado pelo usuário.\n")
                            break
                        
                        # Atualiza a interface
                        progresso_var.set(i)
                        lbl_info.config(text=f"Enviando e-mail {i+1} de {len(destinatarios)}...")
                        lbl_atual.config(text=f"Destinatário: {destinatario}")
                        lbl_contador.config(text=f"{enviados} enviados, {falhas} falhas")
                        text_log.insert(tk.END, f"Enviando para {destinatario}... ")
                        text_log.see(tk.END)
                        janela_progresso.update()
                        
                        # Personaliza o conteúdo
                        conteudo_personalizado = conteudo
                        
                        # Substitui variáveis
                        conteudo_personalizado = conteudo_personalizado.replace("{nome}", info['nome'])
                        conteudo_personalizado = conteudo_personalizado.replace("{email}", info['email'])
                        conteudo_personalizado = conteudo_personalizado.replace("{cargo}", info['cargo'])
                        conteudo_personalizado = conteudo_personalizado.replace("{departamento}", info['departamento'])
                        conteudo_personalizado = conteudo_personalizado.replace("{telefone}", info['telefone'])
                        conteudo_personalizado = conteudo_personalizado.replace("{data}", datetime.datetime.now().strftime("%d/%m/%Y"))
                        conteudo_personalizado = conteudo_personalizado.replace("{hora}", datetime.datetime.now().strftime("%H:%M"))
                        prefeitura_nome = "São José" if self.prefeitura_atual == 'sj' else "Florianópolis"
                        conteudo_personalizado = conteudo_personalizado.replace("{prefeitura}", prefeitura_nome)
                        
                        # Adiciona assinatura
                        if self.assinatura_massa_var.get():
                            # Personaliza a assinatura para este destinatário
                            assinatura = self.obter_assinatura(
                                info['nome'], info['cargo'], info['departamento'], info['telefone'])
                            conteudo_personalizado += assinatura
                        
                        # Envia o e-mail
                        status = self.enviar_email(
                            destinatarios=[destinatario],
                            assunto=assunto,
                            conteudo=conteudo_personalizado,
                            anexos=self.anexos_massa
                        )
                        
                        if status:
                            enviados += 1
                            text_log.insert(tk.END, "OK\n")
                        else:
                            falhas += 1
                            text_log.insert(tk.END, "FALHA\n")
                        
                        text_log.see(tk.END)
                        
                        # Respeita o limite e intervalo
                        if (i + 1) % limite_emails == 0 and i < len(destinatarios) - 1:
                            # Aguarda uma hora após enviar o limite
                            for segundo in range(int(3600)):
                                if cancelar_var.get():
                                    break
                                
                                # Atualiza a mensagem a cada 5 segundos
                                if segundo % 5 == 0:
                                    tempo_restante = 3600 - segundo
                                    minutos = tempo_restante // 60
                                    segundos = tempo_restante % 60
                                    
                                    lbl_info.config(text=f"Limite de {limite_emails} atingido. Aguardando {minutos:02d}:{segundos:02d} para continuar...")
                                    janela_progresso.update()
                                
                                time.sleep(1)
                        elif i < len(destinatarios) - 1:
                            # Aguarda o intervalo entre e-mails
                            time.sleep(intervalo_segundos)
                    
                    # Atualiza a interface uma última vez
                    progresso_var.set(len(destinatarios))
                    lbl_info.config(text="Concluído!")
                    lbl_atual.config(text="")
                    lbl_contador.config(text=f"{enviados} enviados, {falhas} falhas")
                    text_log.insert(tk.END, f"\nEnvio concluído: {enviados} enviados, {falhas} falhas.\n")
                    text_log.see(tk.END)
                    
                    btn_cancelar.config(text="Fechar", command=janela_progresso.destroy)
                    
                    # Registra no banco de dados
                    self.registrar_envio_massa(destinatarios, assunto, conteudo, enviados, falhas)
                    
                    # Exibe mensagem de conclusão
                    if not cancelar_var.get():
                        messagebox.showinfo("Concluído", f"Envio de e-mails concluído!\n\n{enviados} enviados\n{falhas} falhas")
                
                except Exception as e:
                    logger.error(f"Erro na thread de envio em massa: {e}")
                    text_log.insert(tk.END, f"\nErro: {e}\n")
                    btn_cancelar.config(text="Fechar", command=janela_progresso.destroy)
            
            # Inicia a thread de envio
            threading.Thread(target=enviar_emails_thread, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar envio em massa: {e}")
            messagebox.showerror("Erro", f"Falha ao iniciar o envio: {e}")
    
    def agendar_email(self):
        """Agenda um e-mail para envio futuro."""
        try:
            assunto = self.entry_assunto_agendamento.get().strip()
            conteudo = self.text_mensagem_agendamento.get(1.0, tk.END).strip()
            
            if not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha o assunto e o conteúdo do e-mail.")
                return
            
            # Obtém a lista de destinatários
            destinatarios = []
            
            for item in self.lista_preview_agendamento.get_children():
                valores = self.lista_preview_agendamento.item(item, 'values')
                email = valores[0]
                destinatarios.append(email)
            
            if not destinatarios:
                messagebox.showwarning("Aviso", "Selecione pelo menos um destinatário.")
                return
            
            # Obtém a data e hora do agendamento
            data = self.data_agendamento.get_date()
            hora = int(self.hora_var.get())
            minuto = int(self.minuto_var.get())
            
            # Cria o datetime do agendamento
            data_hora = datetime.datetime.combine(data, datetime.time(hora, minuto))
            
            # Verifica se a data é futura
            if data_hora <= datetime.datetime.now():
                messagebox.showwarning("Aviso", "A data e hora do agendamento deve ser no futuro.")
                return
            
            # Obtém a recorrência
            recorrencia = self.recorrencia_var.get().lower()
            
            # Opções específicas de recorrência
            recorrencia_opcoes = {}
            
            if recorrencia == "semanal" and hasattr(self, 'combo_dia_semana'):
                recorrencia_opcoes['dia_semana'] = self.combo_dia_semana.get()
            elif recorrencia == "mensal" and hasattr(self, 'combo_dia_mes'):
                recorrencia_opcoes['dia_mes'] = self.combo_dia_mes.get()
            
            # Confirmação
            mensagem = f"Deseja agendar este e-mail para {len(destinatarios)} destinatários?\n\n"
            mensagem += f"Data/Hora: {data_hora.strftime('%d/%m/%Y %H:%M')}\n"
            mensagem += f"Recorrência: {recorrencia.capitalize()}"
            
            if not messagebox.askyesno("Confirmação", mensagem):
                return
            
            # Salva os anexos em uma pasta específica
            anexos_salvos = []
            
            if self.anexos_agendamento:
                # Cria diretório para anexos agendados
                anexos_dir = os.path.join(BASE_DIR, 'anexos_agendados')
                os.makedirs(anexos_dir, exist_ok=True)
                
                # Gera um ID único para este agendamento
                import uuid
                agendamento_id = str(uuid.uuid4())
                
                # Cria subdiretório específico para este agendamento
                agendamento_dir = os.path.join(anexos_dir, agendamento_id)
                os.makedirs(agendamento_dir, exist_ok=True)
                
                # Copia os anexos
                for anexo in self.anexos_agendamento:
                    nome_arquivo = os.path.basename(anexo)
                    destino = os.path.join(agendamento_dir, nome_arquivo)
                    
                    # Copia o arquivo
                    import shutil
                    shutil.copy2(anexo, destino)
                    
                    anexos_salvos.append(destino)
            
            # Serializa os dados para salvar no banco
            import json
            
            destinatarios_json = json.dumps(destinatarios)
            anexos_json = json.dumps(anexos_salvos)
            recorrencia_opcoes_json = json.dumps(recorrencia_opcoes)
            
            # Salva no banco de dados
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO emails_agendados (
                usuario_id, assunto, conteudo, destinatarios, data_agendada, 
                recorrencia, anexos, recorrencia_opcoes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.usuario_atual['id'], assunto, conteudo, destinatarios_json, 
                data_hora.strftime('%Y-%m-%d %H:%M:%S'), recorrencia, 
                anexos_json, recorrencia_opcoes_json, 'pendente'
            ))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "AGENDAMENTO_EMAIL", 
                f"E-mail agendado para {len(destinatarios)} destinatários em {data_hora.strftime('%d/%m/%Y %H:%M')}"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista de agendamentos
            self.atualizar_lista_agendamentos()
            
            # Limpa os campos
            self.limpar_campos_agendamento()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "E-mail agendado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao agendar e-mail: {e}")
            messagebox.showerror("Erro", f"Falha ao agendar e-mail: {e}")
    
    def enviar_email(self, destinatarios, assunto, conteudo, anexos=None):
        """Função de baixo nível para enviar e-mail."""
        try:
            # Obtém as configurações SMTP
            smtp_config = self.config.get('smtp', {}).get(self.prefeitura_atual, {})
            
            servidor = smtp_config.get('servidor')
            porta = smtp_config.get('porta', 587)
            usuario = smtp_config.get('usuario')
            senha = smtp_config.get('senha')
            usar_tls = smtp_config.get('tls', True)
            usar_ssl = smtp_config.get('ssl', False)
            
            if not servidor or not usuario or not senha:
                logger.error("Configurações SMTP incompletas")
                return False
            
            # Cria a mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = usuario
            msg['To'] = ', '.join(destinatarios)
            
            # Corpo da mensagem em HTML
            part = MIMEText(conteudo, 'html')
            msg.attach(part)
            
            # Adiciona anexos
            if anexos:
                for anexo_path in anexos:
                    if os.path.exists(anexo_path):
                        with open(anexo_path, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(anexo_path))
                        
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(anexo_path)}"'
                        msg.attach(part)
            
            # Conecta ao servidor SMTP
            if usar_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(servidor, porta, context=context)
            else:
                server = smtplib.SMTP(servidor, porta)
                
                if usar_tls:
                    server.starttls()
            
            # Login
            server.login(usuario, senha)
            
            # Envia o e-mail
            server.send_message(msg)
            
            # Fecha a conexão
            server.quit()
            
            # Registra o envio no banco de dados
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO emails_enviados (usuario_id, assunto, conteudo, destinatarios, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                self.usuario_atual['id'], assunto, conteudo, 
                ', '.join(destinatarios), 'enviado'
            ))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "ENVIO_EMAIL", 
                f"E-mail enviado para {', '.join(destinatarios)}"
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {e}")
            
            # Registra a falha no banco de dados
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO emails_enviados (usuario_id, assunto, conteudo, destinatarios, status)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.usuario_atual['id'], assunto, conteudo, 
                    ', '.join(destinatarios), f'falha: {e}'
                ))
                
                # Registra no log
                cursor.execute('''
                INSERT INTO logs (usuario_id, acao, descricao)
                VALUES (?, ?, ?)
                ''', (
                    self.usuario_atual['id'], "ERRO_ENVIO", 
                    f"Falha ao enviar e-mail para {', '.join(destinatarios)}: {e}"
                ))
                
                conn.commit()
                conn.close()
            except Exception as db_error:
                logger.error(f"Erro ao registrar falha de envio: {db_error}")
            
            return False
    
    def registrar_envio_massa(self, destinatarios, assunto, conteudo, enviados, falhas):
        """Registra o envio em massa no banco de dados."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "ENVIO_MASSA", 
                f"Envio em massa para {len(destinatarios)} destinatários. Resultado: {enviados} enviados, {falhas} falhas."
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao registrar envio em massa: {e}")
    
    def atualizar_lista_agendamentos(self):
        """Atualiza a lista de e-mails agendados."""
        try:
            # Limpa a lista atual
            for item in self.lista_agendados.get_children():
                self.lista_agendados.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Busca os agendamentos do usuário atual
            cursor.execute('''
            SELECT id, assunto, destinatarios, data_agendada, recorrencia, status 
            FROM emails_agendados 
            WHERE usuario_id = ? 
            ORDER BY data_agendada DESC
            ''', (self.usuario_atual['id'],))
            
            agendamentos = cursor.fetchall()
            
            for agendamento in agendamentos:
                id_agendamento, assunto, destinatarios_json, data_agendada, recorrencia, status = agendamento
                
                # Converte os destinatários de JSON
                import json
                destinatarios = json.loads(destinatarios_json)
                
                # Formata os dados para exibição
                destinatarios_resumo = f"{len(destinatarios)} destinatários"
                data_formatada = datetime.datetime.strptime(data_agendada, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                recorrencia_formatada = recorrencia.capitalize() if recorrencia else "Nenhuma"
                
                self.lista_agendados.insert("", tk.END, values=(
                    id_agendamento, assunto, destinatarios_resumo, data_formatada, recorrencia_formatada, status
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de agendamentos: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar agendamentos: {e}")
    
    def visualizar_agendamento(self):
        """Visualiza os detalhes de um agendamento selecionado."""
        try:
            selecionado = self.lista_agendados.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um agendamento para visualizar.")
                return
            
            valores = self.lista_agendados.item(selecionado[0], 'values')
            agendamento_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT assunto, conteudo, destinatarios, data_agendada, 
                   recorrencia, anexos, recorrencia_opcoes, status 
            FROM emails_agendados 
            WHERE id = ?
            ''', (agendamento_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                assunto, conteudo, destinatarios_json, data_agendada, recorrencia, anexos_json, recorrencia_opcoes_json, status = resultado
                
                # Converte os dados de JSON
                import json
                destinatarios = json.loads(destinatarios_json)
                anexos = json.loads(anexos_json) if anexos_json else []
                recorrencia_opcoes = json.loads(recorrencia_opcoes_json) if recorrencia_opcoes_json else {}
                
                # Cria janela de visualização
                janela_visualizacao = tk.Toplevel(self.root)
                janela_visualizacao.title(f"Agendamento #{agendamento_id}")
                janela_visualizacao.geometry("800x600")
                janela_visualizacao.minsize(600, 400)
                
                frame_visualizacao = ttk.Frame(janela_visualizacao, padding=10)
                frame_visualizacao.pack(fill=tk.BOTH, expand=True)
                
                # Informações do agendamento
                ttk.Label(frame_visualizacao, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                data_formatada = datetime.datetime.strptime(data_agendada, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                ttk.Label(frame_visualizacao, text=f"Data/Hora: {data_formatada}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                recorrencia_formatada = recorrencia.capitalize() if recorrencia else "Nenhuma"
                ttk.Label(frame_visualizacao, text=f"Recorrência: {recorrencia_formatada}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                if recorrencia_opcoes:
                    opcoes_texto = ", ".join([f"{k}: {v}" for k, v in recorrencia_opcoes.items()])
                    ttk.Label(frame_visualizacao, text=f"Opções de recorrência: {opcoes_texto}").pack(anchor=tk.W, pady=(0, 10))
                
                ttk.Label(frame_visualizacao, text=f"Status: {status}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
                
                # Destinatários
                ttk.Label(frame_visualizacao, text=f"Destinatários ({len(destinatarios)}):", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                frame_destinatarios = ttk.Frame(frame_visualizacao)
                frame_destinatarios.pack(fill=tk.X, pady=(0, 10))
                
                text_destinatarios = tk.Text(frame_destinatarios, height=4, width=80)
                text_destinatarios.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                scrollbar_dest = ttk.Scrollbar(frame_destinatarios, orient=tk.VERTICAL, command=text_destinatarios.yview)
                scrollbar_dest.pack(side=tk.RIGHT, fill=tk.Y)
                text_destinatarios.config(yscrollcommand=scrollbar_dest.set)
                
                text_destinatarios.insert(tk.END, "\n".join(destinatarios))
                text_destinatarios.config(state=tk.DISABLED)
                
                # Conteúdo
                ttk.Label(frame_visualizacao, text="Conteúdo:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                
                frame_conteudo = ttk.Frame(frame_visualizacao)
                frame_conteudo.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                text_conteudo = tk.Text(frame_conteudo, wrap=tk.WORD)
                text_conteudo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                scrollbar_cont = ttk.Scrollbar(frame_conteudo, orient=tk.VERTICAL, command=text_conteudo.yview)
                scrollbar_cont.pack(side=tk.RIGHT, fill=tk.Y)
                text_conteudo.config(yscrollcommand=scrollbar_cont.set)
                
                text_conteudo.insert(tk.END, conteudo)
                text_conteudo.config(state=tk.DISABLED)
                
                # Anexos
                if anexos:
                    ttk.Label(frame_visualizacao, text="Anexos:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                    
                    for i, anexo in enumerate(anexos):
                        nome_arquivo = os.path.basename(anexo)
                        if os.path.exists(anexo):
                            tamanho = os.path.getsize(anexo)
                            tamanho_formatado = self.formatar_tamanho(tamanho)
                            ttk.Label(frame_visualizacao, text=f"{i+1}. {nome_arquivo} ({tamanho_formatado})").pack(anchor=tk.W)
                        else:
                            ttk.Label(frame_visualizacao, text=f"{i+1}. {nome_arquivo} (arquivo não encontrado)").pack(anchor=tk.W)
                
                # Botões
                frame_botoes = ttk.Frame(janela_visualizacao)
                frame_botoes.pack(fill=tk.X, pady=10)
                
                btn_fechar = ttk.Button(frame_botoes, text="Fechar", command=janela_visualizacao.destroy)
                btn_fechar.pack(side=tk.RIGHT, padx=5)
                
                btn_editar = ttk.Button(frame_botoes, text="Editar", command=lambda: self.editar_agendamento(agendamento_id))
                btn_editar.pack(side=tk.RIGHT, padx=5)
                
                btn_cancelar = ttk.Button(frame_botoes, text="Cancelar Agendamento", command=lambda: self.cancelar_agendamento(agendamento_id))
                btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao visualizar agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar detalhes do agendamento: {e}")
    
    def cancelar_agendamento(self, agendamento_id=None):
        """Cancela um agendamento de e-mail."""
        try:
            if agendamento_id is None:
                selecionado = self.lista_agendados.selection()
                
                if not selecionado:
                  messagebox.showwarning("Aviso", "Selecione um agendamento para cancelar.")
                  return
                
                valores = self.lista_agendados.item(selecionado[0], 'values')
                agendamento_id = valores[0]
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", "Deseja realmente cancelar este agendamento?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Atualiza o status para cancelado
            cursor.execute('UPDATE emails_agendados SET status = ? WHERE id = ?', ('cancelado', agendamento_id))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "CANCELAMENTO_AGENDAMENTO", 
                f"Agendamento #{agendamento_id} cancelado"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_agendamentos()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Agendamento cancelado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao cancelar agendamento: {e}")
    
    def editar_agendamento(self, agendamento_id=None):
        """Edita um agendamento existente."""
        try:
            if agendamento_id is None:
                selecionado = self.lista_agendados.selection()
                
                if not selecionado:
                    messagebox.showwarning("Aviso", "Selecione um agendamento para editar.")
                    return
                
                valores = self.lista_agendados.item(selecionado[0], 'values')
                agendamento_id = valores[0]
            
            # Verifica o status do agendamento
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT status FROM emails_agendados WHERE id = ?', (agendamento_id,))
            status = cursor.fetchone()[0]
            
            if status == 'cancelado':
                messagebox.showwarning("Aviso", "Não é possível editar um agendamento cancelado.")
                conn.close()
                return
            
            # Obtém os dados do agendamento
            cursor.execute('''
            SELECT assunto, conteudo, destinatarios, data_agendada, recorrencia, 
                   anexos, recorrencia_opcoes
            FROM emails_agendados 
            WHERE id = ?
            ''', (agendamento_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                assunto, conteudo, destinatarios_json, data_agendada, recorrencia, anexos_json, recorrencia_opcoes_json = resultado
                
                # Converte os dados de JSON
                import json
                destinatarios = json.loads(destinatarios_json)
                anexos = json.loads(anexos_json) if anexos_json else []
                recorrencia_opcoes = json.loads(recorrencia_opcoes_json) if recorrencia_opcoes_json else {}
                
                # Preenche os campos do formulário de agendamento
                self.entry_assunto_agendamento.delete(0, tk.END)
                self.entry_assunto_agendamento.insert(0, assunto)
                
                self.text_mensagem_agendamento.delete(1.0, tk.END)
                self.text_mensagem_agendamento.insert(tk.END, conteudo)
                
                # Configura a data e hora
                data_hora = datetime.datetime.strptime(data_agendada, '%Y-%m-%d %H:%M:%S')
                self.data_agendamento.set_date(data_hora.date())
                self.hora_var.set(f"{data_hora.hour:02d}")
                self.minuto_var.set(f"{data_hora.minute:02d}")
                
                # Configura a recorrência
                self.recorrencia_var.set(recorrencia.capitalize() if recorrencia else "Nenhuma")
                self.atualizar_recorrencia()
                
                # Configura opções específicas de recorrência
                if recorrencia == "semanal" and 'dia_semana' in recorrencia_opcoes:
                    self.combo_dia_semana.set(recorrencia_opcoes['dia_semana'])
                elif recorrencia == "mensal" and 'dia_mes' in recorrencia_opcoes:
                    self.combo_dia_mes.set(recorrencia_opcoes['dia_mes'])
                
                # Limpa a lista atual de anexos
                for item in self.lista_anexos_agendamento.get_children():
                    self.lista_anexos_agendamento.delete(item)
                
                self.anexos_agendamento = []
                
                # Adiciona os anexos
                for anexo in anexos:
                    if os.path.exists(anexo):
                        self.anexos_agendamento.append(anexo)
                        
                        nome_arquivo = os.path.basename(anexo)
                        tamanho = os.path.getsize(anexo)
                        tamanho_formatado = self.formatar_tamanho(tamanho)
                        
                        self.lista_anexos_agendamento.insert("", tk.END, values=(nome_arquivo, tamanho_formatado))
                
                # Atualiza a lista de destinatários
                # Limpa a lista atual
                for item in self.lista_preview_agendamento.get_children():
                    self.lista_preview_agendamento.delete(item)
                
                # Busca informações dos destinatários
                placeholders = ','.join(['?'] * len(destinatarios))
                cursor.execute(f'''
                SELECT email, nome, departamento FROM funcionarios 
                WHERE email IN ({placeholders}) AND ativo = 1
                ''', destinatarios)
                
                funcionarios = cursor.fetchall()
                
                # Preenche a lista com os funcionários encontrados
                contador = 0
                for email, nome, departamento in funcionarios:
                    self.lista_preview_agendamento.insert("", tk.END, values=(email, nome, departamento))
                    contador += 1
                
                # Adiciona e-mails que não estão no cadastro de funcionários
                emails_encontrados = [f[0] for f in funcionarios]
                for email in destinatarios:
                    if email not in emails_encontrados:
                        self.lista_preview_agendamento.insert("", tk.END, values=(email, "", ""))
                        contador += 1
                
                # Atualiza o contador
                self.lbl_contador_agendamento.config(text=f"Total de destinatários: {contador}")
                
                # Vai para a aba de agendamento
                self.notebook.select(2)  # Índice da aba de agendamento
                
                # Armazena o ID do agendamento para atualização
                self.agendamento_editando = agendamento_id
                
                # Atualiza o botão de agendamento
                btn_agendar = self.notebook.nametowidget(self.notebook.select()).nametowidget("btn_agendar") if hasattr(self.notebook.nametowidget(self.notebook.select()), "nametowidget") else None
                
                if btn_agendar:
                    btn_agendar.config(text="Atualizar Agendamento", command=self.atualizar_agendamento)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao editar agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar dados do agendamento: {e}")
    
    def atualizar_agendamento(self):
        """Atualiza um agendamento existente."""
        try:
            if not hasattr(self, 'agendamento_editando'):
                messagebox.showwarning("Aviso", "Nenhum agendamento selecionado para atualização.")
                return
            
            agendamento_id = self.agendamento_editando
            
            # Obtém os dados do formulário
            assunto = self.entry_assunto_agendamento.get().strip()
            conteudo = self.text_mensagem_agendamento.get(1.0, tk.END).strip()
            
            if not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha o assunto e o conteúdo do e-mail.")
                return
            
            # Obtém a lista de destinatários
            destinatarios = []
            
            for item in self.lista_preview_agendamento.get_children():
                valores = self.lista_preview_agendamento.item(item, 'values')
                email = valores[0]
                destinatarios.append(email)
            
            if not destinatarios:
                messagebox.showwarning("Aviso", "Selecione pelo menos um destinatário.")
                return
            
            # Obtém a data e hora do agendamento
            data = self.data_agendamento.get_date()
            hora = int(self.hora_var.get())
            minuto = int(self.minuto_var.get())
            
            # Cria o datetime do agendamento
            data_hora = datetime.datetime.combine(data, datetime.time(hora, minuto))
            
            # Verifica se a data é futura
            if data_hora <= datetime.datetime.now():
                messagebox.showwarning("Aviso", "A data e hora do agendamento deve ser no futuro.")
                return
            
            # Obtém a recorrência
            recorrencia = self.recorrencia_var.get().lower()
            
            # Opções específicas de recorrência
            recorrencia_opcoes = {}
            
            if recorrencia == "semanal" and hasattr(self, 'combo_dia_semana'):
                recorrencia_opcoes['dia_semana'] = self.combo_dia_semana.get()
            elif recorrencia == "mensal" and hasattr(self, 'combo_dia_mes'):
                recorrencia_opcoes['dia_mes'] = self.combo_dia_mes.get()
            
            # Confirmação
            mensagem = f"Deseja atualizar este agendamento para {len(destinatarios)} destinatários?\n\n"
            mensagem += f"Data/Hora: {data_hora.strftime('%d/%m/%Y %H:%M')}\n"
            mensagem += f"Recorrência: {recorrencia.capitalize()}"
            
            if not messagebox.askyesno("Confirmação", mensagem):
                return
            
            # Serializa os dados para salvar no banco
            import json
            
            destinatarios_json = json.dumps(destinatarios)
            anexos_json = json.dumps(self.anexos_agendamento)
            recorrencia_opcoes_json = json.dumps(recorrencia_opcoes)
            
            # Atualiza no banco de dados
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE emails_agendados SET 
                assunto = ?, conteudo = ?, destinatarios = ?, data_agendada = ?, 
                recorrencia = ?, anexos = ?, recorrencia_opcoes = ?
            WHERE id = ?
            ''', (
                assunto, conteudo, destinatarios_json, 
                data_hora.strftime('%Y-%m-%d %H:%M:%S'), recorrencia, 
                anexos_json, recorrencia_opcoes_json, agendamento_id
            ))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "ATUALIZACAO_AGENDAMENTO", 
                f"Agendamento #{agendamento_id} atualizado"
            ))
            
            conn.commit()
            conn.close()
            
            # Limpa a variável de edição
            delattr(self, 'agendamento_editando')
            
            # Atualiza a lista de agendamentos
            self.atualizar_lista_agendamentos()
            
            # Limpa os campos
            self.limpar_campos_agendamento()
            
            # Restaura o botão de agendamento
            btn_agendar = self.notebook.nametowidget(self.notebook.select()).nametowidget("btn_agendar") if hasattr(self.notebook.nametowidget(self.notebook.select()), "nametowidget") else None
            
            if btn_agendar:
                btn_agendar.config(text="Agendar E-mail", command=self.agendar_email)
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Agendamento atualizado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar agendamento: {e}")
            messagebox.showerror("Erro", f"Falha ao atualizar agendamento: {e}")
    
    def limpar_campos_email(self):
        """Limpa os campos do formulário de e-mail individual."""
        self.entry_destinatario.delete(0, tk.END)
        self.entry_assunto.delete(0, tk.END)
        self.text_mensagem.delete(1.0, tk.END)
        
        # Limpa a lista de anexos
        for item in self.lista_anexos.get_children():
            self.lista_anexos.delete(item)
        
        self.anexos = []
    
    def limpar_campos_massa(self):
        """Limpa os campos do formulário de e-mail em massa."""
        self.entry_assunto_massa.delete(0, tk.END)
        self.text_mensagem_massa.delete(1.0, tk.END)
        
        # Limpa a lista de anexos
        for item in self.lista_anexos_massa.get_children():
            self.lista_anexos_massa.delete(item)
        
        self.anexos_massa = []
        
        # Limpa a lista de destinatários
        for item in self.lista_preview.get_children():
            self.lista_preview.delete(item)
        
        self.lbl_contador.config(text="Total de destinatários: 0")
    
    def limpar_campos_agendamento(self):
        """Limpa os campos do formulário de agendamento."""
        self.entry_assunto_agendamento.delete(0, tk.END)
        self.text_mensagem_agendamento.delete(1.0, tk.END)
        
        # Reset da data para hoje
        self.data_agendamento.set_date(datetime.date.today())
        
        # Reset da hora para 08:00
        self.hora_var.set("08")
        self.minuto_var.set("00")
        
        # Reset da recorrência
        self.recorrencia_var.set("Nenhuma")
        self.atualizar_recorrencia()
        
        # Limpa a lista de anexos
        for item in self.lista_anexos_agendamento.get_children():
            self.lista_anexos_agendamento.delete(item)
        
        self.anexos_agendamento = []
        
        # Limpa a lista de destinatários
        for item in self.lista_preview_agendamento.get_children():
            self.lista_preview_agendamento.delete(item)
        
        self.lbl_contador_agendamento.config(text="Total de destinatários: 0")
    
    def limpar_campos_template(self):
        """Limpa os campos do formulário de template."""
        self.entry_nome_template.delete(0, tk.END)
        self.entry_assunto_template.delete(0, tk.END)
        self.text_conteudo_template.delete(1.0, tk.END)
        self.combo_departamento_template.set("")
    
    def limpar_campos_funcionario(self):
        """Limpa os campos do formulário de funcionário."""
        self.entry_nome_funcionario.delete(0, tk.END)
        self.entry_email_funcionario.delete(0, tk.END)
        self.entry_cargo_funcionario.delete(0, tk.END)
        self.combo_departamento_funcionario.set("")
        self.entry_telefone_funcionario.delete(0, tk.END)
    
    def limpar_campos_usuario(self):
        """Limpa os campos do formulário de usuário."""
        self.entry_nome_usuario.delete(0, tk.END)
        self.entry_email_usuario.delete(0, tk.END)
        self.entry_senha_usuario.delete(0, tk.END)
        self.entry_confirmar_senha.delete(0, tk.END)
        self.entry_cargo_usuario.delete(0, tk.END)
        self.combo_departamento_usuario.set("")
        self.entry_telefone_usuario.delete(0, tk.END)
        self.combo_nivel_acesso.current(0)
    
    def limpar_campos_grupo(self):
        """Limpa os campos do formulário de grupo."""
        self.entry_nome_grupo.delete(0, tk.END)
        self.entry_descricao_grupo.delete(0, tk.END)
    
    def limpar_filtros_log(self):
        """Limpa os filtros da lista de logs."""
        self.combo_acao_log.set("")
        self.combo_usuario_log.set("")
        
        # Reset das datas
        self.data_inicial_log.set_date(datetime.date.today() - datetime.timedelta(days=7))
        self.data_final_log.set_date(datetime.date.today())
        
        # Atualiza a lista de logs
        self.atualizar_lista_logs()
    
    def salvar_template(self):
        """Salva um novo template ou atualiza um existente."""
        try:
            nome = self.entry_nome_template.get().strip()
            assunto = self.entry_assunto_template.get().strip()
            conteudo = self.text_conteudo_template.get(1.0, tk.END).strip()
            departamento = self.combo_departamento_template.get().strip()
            
            if not nome or not assunto or not conteudo:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios.")
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Verifica se é um template existente sendo editado
            template_existente = False
            template_id = None
            
            for item in self.lista_templates.selection():
                valores = self.lista_templates.item(item, 'values')
                template_id = valores[0]
                template_existente = True
                break
            
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            if template_existente and template_id:
                # Atualiza o template existente
                cursor.execute('''
                UPDATE templates SET 
                    nome = ?, assunto = ?, conteudo = ?, 
                    departamento = ?, ultima_modificacao = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (nome, assunto, conteudo, departamento, template_id))
                
                mensagem_log = f"Template #{template_id} atualizado"
                mensagem_sucesso = "Template atualizado com sucesso!"
                
            else:
                # Cria um novo template
                cursor.execute('''
                INSERT INTO templates (nome, assunto, conteudo, prefeitura, departamento)
                VALUES (?, ?, ?, ?, ?)
                ''', (nome, assunto, conteudo, prefeitura_codigo, departamento))
                
                template_id = cursor.lastrowid
                mensagem_log = f"Novo template #{template_id} criado"
                mensagem_sucesso = "Template criado com sucesso!"
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (self.usuario_atual['id'], "TEMPLATE", mensagem_log))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista de templates
            self.atualizar_lista_templates()
            
            # Limpa os campos
            self.limpar_campos_template()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", mensagem_sucesso)
            
        except Exception as e:
            logger.error(f"Erro ao salvar template: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar template: {e}")
    
    def atualizar_lista_templates(self):
        """Atualiza a lista de templates."""
        try:
            # Limpa a lista atual
            for item in self.lista_templates.get_children():
                self.lista_templates.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            prefeitura_codigo = 'sj' if self.prefeitura_atual == 'sj' else 'floripa'
            
            cursor.execute('''
            SELECT id, nome, assunto, departamento, ultima_modificacao 
            FROM templates 
            WHERE prefeitura = ? 
            ORDER BY nome
            ''', (prefeitura_codigo,))
            
            templates = cursor.fetchall()
            
            for template in templates:
                id_template, nome, assunto, departamento, data = template
                
                # Formata a data
                data_formatada = datetime.datetime.strptime(data, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M') if data else ""
                
                self.lista_templates.insert("", tk.END, values=(
                    id_template, nome, assunto, departamento, data_formatada
                ))
            
            # Atualiza os comboboxes de templates
            self.carregar_templates_combo()
            self.carregar_templates_combo_agendamento()
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de templates: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar templates: {e}")
    
    def visualizar_template_selecionado(self):
        """Visualiza o template selecionado na lista."""
        try:
            selecionado = self.lista_templates.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um template para visualizar.")
                return
            
            valores = self.lista_templates.item(selecionado[0], 'values')
            template_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, assunto, conteudo, departamento FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, assunto, conteudo, departamento = resultado
                
                # Cria janela de visualização
                janela_visualizacao = tk.Toplevel(self.root)
                janela_visualizacao.title(f"Template: {nome}")
                janela_visualizacao.geometry("700x500")
                janela_visualizacao.minsize(600, 400)
                
                frame_visualizacao = ttk.Frame(janela_visualizacao, padding=10)
                frame_visualizacao.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(frame_visualizacao, text=f"Nome: {nome}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                ttk.Label(frame_visualizacao, text=f"Assunto: {assunto}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
                ttk.Label(frame_visualizacao, text=f"Departamento: {departamento}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
                
                # Visualização com substituição de variáveis de exemplo
                ttk.Label(frame_visualizacao, text="Prévia com valores de exemplo:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
                
                frame_conteudo = ttk.Frame(frame_visualizacao)
                frame_conteudo.pack(fill=tk.BOTH, expand=True)
                
                text_conteudo = tk.Text(frame_conteudo, wrap=tk.WORD)
                text_conteudo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                scrollbar = ttk.Scrollbar(frame_conteudo, orient=tk.VERTICAL, command=text_conteudo.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_conteudo.config(yscrollcommand=scrollbar.set)
                
                # Substitui variáveis com valores de exemplo
                conteudo_exemplo = conteudo.replace("{nome}", "Nome do Destinatário")
                conteudo_exemplo = conteudo_exemplo.replace("{email}", "exemplo@email.com")
                conteudo_exemplo = conteudo_exemplo.replace("{cargo}", "Cargo do Destinatário")
                conteudo_exemplo = conteudo_exemplo.replace("{departamento}", departamento or "Departamento")
                conteudo_exemplo = conteudo_exemplo.replace("{telefone}", "Telefone do Destinatário")
                conteudo_exemplo = conteudo_exemplo.replace("{data}", datetime.datetime.now().strftime("%d/%m/%Y"))
                conteudo_exemplo = conteudo_exemplo.replace("{hora}", datetime.datetime.now().strftime("%H:%M"))
                conteudo_exemplo = conteudo_exemplo.replace("{prefeitura}", "São José" if self.prefeitura_atual == 'sj' else "Florianópolis")
                
                text_conteudo.insert(tk.END, conteudo_exemplo)
                
                # Configura tags para formatação básica de HTML
                text_conteudo.tag_configure("bold", font=('Helvetica', 10, 'bold'))
                text_conteudo.tag_configure("italic", font=('Helvetica', 10, 'italic'))
                text_conteudo.tag_configure("underline", underline=True)
                
                # Aplica formatação básica
                self.aplicar_formatacao_html(text_conteudo)
                
                text_conteudo.config(state=tk.DISABLED)
                
                # Botões
                frame_botoes = ttk.Frame(janela_visualizacao)
                frame_botoes.pack(fill=tk.X, pady=10)
                
                btn_fechar = ttk.Button(frame_botoes, text="Fechar", command=janela_visualizacao.destroy)
                btn_fechar.pack(side=tk.RIGHT, padx=5)
                
                btn_editar = ttk.Button(frame_botoes, text="Editar", command=lambda: self.editar_template(template_id))
                btn_editar.pack(side=tk.RIGHT, padx=5)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao visualizar template: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar template: {e}")
    
    def editar_template(self, template_id=None):
        """Carrega um template para edição."""
        try:
            if template_id is None:
                selecionado = self.lista_templates.selection()
                
                if not selecionado:
                    messagebox.showwarning("Aviso", "Selecione um template para editar.")
                    return
                
                valores = self.lista_templates.item(selecionado[0], 'values')
                template_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, assunto, conteudo, departamento FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, assunto, conteudo, departamento = resultado
                
                # Preenche os campos
                self.entry_nome_template.delete(0, tk.END)
                self.entry_nome_template.insert(0, nome)
                
                self.entry_assunto_template.delete(0, tk.END)
                self.entry_assunto_template.insert(0, assunto)
                
                self.text_conteudo_template.delete(1.0, tk.END)
                self.text_conteudo_template.insert(tk.END, conteudo)
                
                self.combo_departamento_template.set(departamento)
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao editar template: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar template para edição: {e}")
    
    def excluir_template(self):
        """Exclui um template selecionado."""
        try:
            selecionado = self.lista_templates.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um template para excluir.")
                return
            
            valores = self.lista_templates.item(selecionado[0], 'values')
            template_id = valores[0]
            nome = valores[1]
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente excluir o template '{nome}'?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))

            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXCLUSAO_TEMPLATE", 
                f"Template #{template_id} ({nome}) excluído"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_templates()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Template excluído com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao excluir template: {e}")
            messagebox.showerror("Erro", f"Falha ao excluir template: {e}")
    
    def duplicar_template(self):
        """Duplica um template selecionado."""
        try:
            selecionado = self.lista_templates.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um template para duplicar.")
                return
            
            valores = self.lista_templates.item(selecionado[0], 'values')
            template_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, assunto, conteudo, prefeitura, departamento FROM templates WHERE id = ?', (template_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, assunto, conteudo, prefeitura, departamento = resultado
                
                # Cria um novo nome para a cópia
                novo_nome = f"{nome} - Cópia"
                
                # Insere a cópia
                cursor.execute('''
                INSERT INTO templates (nome, assunto, conteudo, prefeitura, departamento)
                VALUES (?, ?, ?, ?, ?)
                ''', (novo_nome, assunto, conteudo, prefeitura, departamento))
                
                novo_id = cursor.lastrowid
                
                # Registra no log
                cursor.execute('''
                INSERT INTO logs (usuario_id, acao, descricao)
                VALUES (?, ?, ?)
                ''', (
                    self.usuario_atual['id'], "DUPLICACAO_TEMPLATE", 
                    f"Template #{template_id} duplicado como #{novo_id}"
                ))
                
                conn.commit()
                conn.close()
                
                # Atualiza a lista
                self.atualizar_lista_templates()
                
                # Mensagem de sucesso
                messagebox.showinfo("Sucesso", "Template duplicado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao duplicar template: {e}")
            messagebox.showerror("Erro", f"Falha ao duplicar template: {e}")
    
    def atualizar_lista_funcionarios(self):
        """Atualiza a lista de funcionários."""
        try:
            # Limpa a lista atual
            for item in self.lista_funcionarios.get_children():
                self.lista_funcionarios.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, nome, email, cargo, departamento, prefeitura, ativo
            FROM funcionarios
            ORDER BY nome
            ''')
            
            funcionarios = cursor.fetchall()
            
            for func in funcionarios:
                id_func, nome, email, cargo, departamento, prefeitura, ativo = func
                
                # Formata o status
                status = "Ativo" if ativo else "Inativo"
                
                # Formata a prefeitura
                prefeitura_nome = "São José" if prefeitura == 'sj' else "Florianópolis"
                
                self.lista_funcionarios.insert("", tk.END, values=(
                    id_func, nome, email, cargo, departamento, prefeitura_nome, status
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de funcionários: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar funcionários: {e}")
    
    def buscar_funcionario(self, event=None):
        """Busca funcionários conforme o filtro."""
        try:
            busca = self.entry_busca_funcionario.get().strip()
            filtro = self.filtro_funcionario.get().lower()
            
            # Limpa a lista atual
            for item in self.lista_funcionarios.get_children():
                self.lista_funcionarios.delete(item)
            
            if not busca:
                self.atualizar_lista_funcionarios()
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            campo_filtro = ''
            
            if filtro == 'nome':
                campo_filtro = 'nome'
            elif filtro == 'e-mail':
                campo_filtro = 'email'
            elif filtro == 'cargo':
                campo_filtro = 'cargo'
            elif filtro == 'departamento':
                campo_filtro = 'departamento'
            
            cursor.execute(f'''
            SELECT id, nome, email, cargo, departamento, prefeitura, ativo
            FROM funcionarios
            WHERE {campo_filtro} LIKE ?
            ORDER BY nome
            ''', (f'%{busca}%',))
            
            funcionarios = cursor.fetchall()
            
            for func in funcionarios:
                id_func, nome, email, cargo, departamento, prefeitura, ativo = func
                
                # Formata o status
                status = "Ativo" if ativo else "Inativo"
                
                # Formata a prefeitura
                prefeitura_nome = "São José" if prefeitura == 'sj' else "Florianópolis"
                
                self.lista_funcionarios.insert("", tk.END, values=(
                    id_func, nome, email, cargo, departamento, prefeitura_nome, status
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {e}")
            messagebox.showerror("Erro", f"Falha na busca: {e}")
    
    def salvar_funcionario(self):
        """Salva um novo funcionário ou atualiza um existente."""
        try:
            nome = self.entry_nome_funcionario.get().strip()
            email = self.entry_email_funcionario.get().strip()
            cargo = self.entry_cargo_funcionario.get().strip()
            departamento = self.combo_departamento_funcionario.get().strip()
            telefone = self.entry_telefone_funcionario.get().strip()
            
            # Prefeitura selecionada
            prefeitura = 'sj' if self.combo_prefeitura_funcionario.get() == "São José" else 'floripa'
            
            if not nome or not email:
                messagebox.showwarning("Aviso", "Nome e e-mail são campos obrigatórios.")
                return
            
            # Validação básica de e-mail
            import re
            padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(padrao_email, email):
                messagebox.showwarning("Aviso", "O e-mail informado parece ser inválido.")
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Verifica se é um funcionário existente sendo editado
            funcionario_existente = False
            funcionario_id = None
            
            for item in self.lista_funcionarios.selection():
                valores = self.lista_funcionarios.item(item, 'values')
                funcionario_id = valores[0]
                funcionario_existente = True
                break
            
            if funcionario_existente and funcionario_id:
                # Atualiza o funcionário existente
                cursor.execute('''
                UPDATE funcionarios SET 
                    nome = ?, email = ?, cargo = ?, 
                    departamento = ?, telefone = ?, prefeitura = ?
                WHERE id = ?
                ''', (nome, email, cargo, departamento, telefone, prefeitura, funcionario_id))
                
                mensagem_log = f"Funcionário #{funcionario_id} atualizado"
                mensagem_sucesso = "Funcionário atualizado com sucesso!"
                
            else:
                # Verifica se o e-mail já existe
                cursor.execute('SELECT id FROM funcionarios WHERE email = ?', (email,))
                if cursor.fetchone():
                    messagebox.showwarning("Aviso", "Já existe um funcionário com este e-mail.")
                    conn.close()
                    return
                
                # Cria um novo funcionário
                cursor.execute('''
                INSERT INTO funcionarios (nome, email, cargo, departamento, telefone, prefeitura)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (nome, email, cargo, departamento, telefone, prefeitura))
                
                funcionario_id = cursor.lastrowid
                mensagem_log = f"Novo funcionário #{funcionario_id} criado"
                mensagem_sucesso = "Funcionário cadastrado com sucesso!"
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (self.usuario_atual['id'], "FUNCIONARIO", mensagem_log))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_funcionarios()
            
            # Atualiza os departamentos
            self.carregar_departamentos()
            
            # Limpa os campos
            self.limpar_campos_funcionario()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", mensagem_sucesso)
            
        except Exception as e:
            logger.error(f"Erro ao salvar funcionário: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar funcionário: {e}")
    
    def editar_funcionario(self):
        """Carrega um funcionário para edição."""
        try:
            selecionado = self.lista_funcionarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para editar.")
                return
            
            valores = self.lista_funcionarios.item(selecionado[0], 'values')
            funcionario_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT nome, email, cargo, departamento, telefone, prefeitura
            FROM funcionarios
            WHERE id = ?
            ''', (funcionario_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                nome, email, cargo, departamento, telefone, prefeitura = resultado
                
                # Preenche os campos
                self.entry_nome_funcionario.delete(0, tk.END)
                self.entry_nome_funcionario.insert(0, nome)
                
                self.entry_email_funcionario.delete(0, tk.END)
                self.entry_email_funcionario.insert(0, email)
                
                self.entry_cargo_funcionario.delete(0, tk.END)
                self.entry_cargo_funcionario.insert(0, cargo or "")
                
                self.combo_departamento_funcionario.set(departamento or "")
                
                self.entry_telefone_funcionario.delete(0, tk.END)
                self.entry_telefone_funcionario.insert(0, telefone or "")
                
                self.combo_prefeitura_funcionario.set("São José" if prefeitura == 'sj' else "Florianópolis")
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao editar funcionário: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar funcionário para edição: {e}")
    
    def excluir_funcionario(self):
        """Exclui um funcionário selecionado."""
        try:
            selecionado = self.lista_funcionarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para excluir.")
                return
            
            valores = self.lista_funcionarios.item(selecionado[0], 'values')
            funcionario_id = valores[0]
            nome = valores[1]
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente excluir o funcionário '{nome}'?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Remove o funcionário de grupos
            cursor.execute('DELETE FROM grupo_funcionario WHERE funcionario_id = ?', (funcionario_id,))
            
            # Exclui o funcionário
            cursor.execute('DELETE FROM funcionarios WHERE id = ?', (funcionario_id,))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXCLUSAO_FUNCIONARIO", 
                f"Funcionário #{funcionario_id} ({nome}) excluído"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_funcionarios()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Funcionário excluído com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao excluir funcionário: {e}")
            messagebox.showerror("Erro", f"Falha ao excluir funcionário: {e}")
    
    def alternar_status_funcionario(self):
        """Alterna o status de um funcionário entre ativo e inativo."""
        try:
            selecionado = self.lista_funcionarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para alterar o status.")
                return
            
            valores = self.lista_funcionarios.item(selecionado[0], 'values')
            funcionario_id = valores[0]
            nome = valores[1]
            status_atual = valores[6]
            
            # Determina o novo status
            novo_status = 0 if status_atual == "Ativo" else 1
            texto_status = "inativo" if status_atual == "Ativo" else "ativo"
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente alterar o status do funcionário '{nome}' para {texto_status}?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Atualiza o status
            cursor.execute('UPDATE funcionarios SET ativo = ? WHERE id = ?', (novo_status, funcionario_id))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "ALTERACAO_STATUS_FUNCIONARIO", 
                f"Funcionário #{funcionario_id} ({nome}) alterado para {texto_status}"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_funcionarios()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", f"Funcionário alterado para {texto_status} com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao alterar status do funcionário: {e}")
            messagebox.showerror("Erro", f"Falha ao alterar status do funcionário: {e}")
    
    def adicionar_funcionario_grupo(self):
        """Adiciona um funcionário selecionado a um grupo."""
        try:
            selecionado = self.lista_funcionarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para adicionar a um grupo.")
                return
            
            valores = self.lista_funcionarios.item(selecionado[0], 'values')
            funcionario_id = valores[0]
            nome = valores[1]
            
            # Obtém a lista de grupos disponíveis
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            prefeitura = 'sj' if valores[5] == "São José" else 'floripa'
            
            cursor.execute('SELECT id, nome FROM grupos WHERE prefeitura = ?', (prefeitura,))
            grupos = cursor.fetchall()
            
            if not grupos:
                messagebox.showwarning("Aviso", "Não há grupos cadastrados para esta prefeitura.")
                conn.close()
                return
            
            # Obtém os grupos aos quais o funcionário já pertence
            cursor.execute('''
            SELECT grupo_id FROM grupo_funcionario
            WHERE funcionario_id = ?
            ''', (funcionario_id,))
            
            grupos_atuais = [g[0] for g in cursor.fetchall()]
            
            # Cria janela de seleção de grupos
            janela_grupos = tk.Toplevel(self.root)
            janela_grupos.title(f"Adicionar '{nome}' a Grupos")
            janela_grupos.geometry("400x500")
            janela_grupos.minsize(400, 400)
            janela_grupos.transient(self.root)
            janela_grupos.grab_set()
            
            frame_grupos = ttk.Frame(janela_grupos, padding=10)
            frame_grupos.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame_grupos, text="Selecione os grupos:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # Variáveis para os checkboxes
            var_grupos = {}
            
            # Frame para a lista de grupos
            frame_lista = ttk.Frame(frame_grupos)
            frame_lista.pack(fill=tk.BOTH, expand=True)
            
            canvas = tk.Canvas(frame_lista)
            scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=canvas.yview)
            
            scrollable_frame = ttk.Frame(canvas)
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Cria um checkbox para cada grupo
            for grupo_id, grupo_nome in grupos:
                var_grupos[grupo_id] = tk.BooleanVar(value=grupo_id in grupos_atuais)
                
                chk = ttk.Checkbutton(scrollable_frame, text=grupo_nome, variable=var_grupos[grupo_id])
                chk.pack(anchor=tk.W, pady=2)
            
            # Botões de ação
            frame_botoes = ttk.Frame(janela_grupos)
            frame_botoes.pack(fill=tk.X, pady=10)
            
            btn_salvar = ttk.Button(frame_botoes, text="Salvar", command=lambda: salvar_grupos())
            btn_salvar.pack(side=tk.RIGHT, padx=5)
            
            btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_grupos.destroy)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Função para salvar os grupos
            def salvar_grupos():
                try:
                    # Remove o funcionário de todos os grupos
                    cursor.execute('DELETE FROM grupo_funcionario WHERE funcionario_id = ?', (funcionario_id,))
                    
                    # Adiciona o funcionário aos grupos selecionados
                    grupos_selecionados = []
                    
                    for grupo_id, var in var_grupos.items():
                        if var.get():
                            cursor.execute('''
                            INSERT INTO grupo_funcionario (grupo_id, funcionario_id)
                            VALUES (?, ?)
                            ''', (grupo_id, funcionario_id))
                            
                            grupos_selecionados.append(grupo_id)
                    
                    # Registra no log
                    cursor.execute('''
                    INSERT INTO logs (usuario_id, acao, descricao)
                    VALUES (?, ?, ?)
                    ''', (
                        self.usuario_atual['id'], "GRUPOS_FUNCIONARIO", 
                        f"Grupos do funcionário #{funcionario_id} ({nome}) atualizados"
                    ))
                    
                    conn.commit()
                    
                    # Mensagem de sucesso
                    messagebox.showinfo("Sucesso", "Grupos do funcionário atualizados com sucesso!")
                    
                    # Fecha a janela
                    janela_grupos.destroy()
                    
                except Exception as e:
                    logger.error(f"Erro ao salvar grupos do funcionário: {e}")
                    messagebox.showerror("Erro", f"Falha ao salvar grupos: {e}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao adicionar funcionário a grupo: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir seleção de grupos: {e}")
    
    def importar_funcionarios(self):
        """Importa funcionários de arquivo CSV ou Excel."""
        try:
            filetypes = [
                ('Arquivos CSV', '*.csv'),
                ('Arquivos Excel', '*.xlsx *.xls')
            ]
            
            filename = filedialog.askopenfilename(
                title="Selecionar arquivo de funcionários",
                filetypes=filetypes
            )
            
            if not filename:
                return
            
            # Cria janela de importação
            janela_importacao = tk.Toplevel(self.root)
            janela_importacao.title("Importar Funcionários")
            janela_importacao.geometry("800x600")
            janela_importacao.minsize(600, 400)
            janela_importacao.transient(self.root)
            janela_importacao.grab_set()
            
            frame_importacao = ttk.Frame(janela_importacao, padding=10)
            frame_importacao.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame_importacao, text="Importação de Funcionários", font=('Helvetica', 12, 'bold')).pack(pady=(0, 10))
            
            # Pré-visualização
            ttk.Label(frame_importacao, text="Pré-visualização dos dados:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            
            frame_preview = ttk.Frame(frame_importacao)
            frame_preview.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Tabela de pré-visualização
            colunas = ('nome', 'email', 'cargo', 'departamento', 'telefone', 'prefeitura')
            
            tabela_preview = ttk.Treeview(frame_preview, columns=colunas, show='headings', height=10)
            tabela_preview.heading('nome', text='Nome')
            tabela_preview.heading('email', text='E-mail')
            tabela_preview.heading('cargo', text='Cargo')
            tabela_preview.heading('departamento', text='Departamento')
            tabela_preview.heading('telefone', text='Telefone')
            tabela_preview.heading('prefeitura', text='Prefeitura')
            
            tabela_preview.column('nome', width=150)
            tabela_preview.column('email', width=150)
            tabela_preview.column('cargo', width=100)
            tabela_preview.column('departamento', width=100)
            tabela_preview.column('telefone', width=100)
            tabela_preview.column('prefeitura', width=100)
            
            tabela_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(frame_preview, orient=tk.VERTICAL, command=tabela_preview.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tabela_preview.config(yscrollcommand=scrollbar.set)
            
            # Mapeamento de colunas
            ttk.Label(frame_importacao, text="Mapeamento de colunas:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
            
            frame_mapeamento = ttk.Frame(frame_importacao)
            frame_mapeamento.pack(fill=tk.X, pady=(0, 10))
            
            # Carrega os dados do arquivo
            try:
                # Identifica o tipo de arquivo
                extensao = os.path.splitext(filename)[1].lower()
                
                if extensao == '.csv':
                    # Carrega CSV
                    with open(filename, 'r', encoding='utf-8') as f:
                        import csv
                        reader = csv.reader(f)
                        cabecalho = next(reader)
                        dados = [row for row in reader]
                elif extensao in ['.xlsx', '.xls']:
                    # Carrega Excel
                    df = pd.read_excel(filename)
                    cabecalho = df.columns.tolist()
                    dados = df.values.tolist()
                else:
                    raise ValueError("Formato de arquivo não suportado")
                
                # Cria o mapeamento de colunas
                mapeamento = {}
                cabecalho_opcoes = ["Nenhum"] + cabecalho
                
                # Frame para colunas obrigatórias
                frame_obrigatorias = ttk.LabelFrame(frame_mapeamento, text="Colunas Obrigatórias", padding=10)
                frame_obrigatorias.pack(fill=tk.X, pady=(0, 10))
                
                ttk.Label(frame_obrigatorias, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(frame_obrigatorias, text="E-mail:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
                
                mapeamento['nome'] = tk.StringVar()
                mapeamento['email'] = tk.StringVar()
                
                combo_nome = ttk.Combobox(frame_obrigatorias, textvariable=mapeamento['nome'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_nome.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                combo_nome.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                combo_email = ttk.Combobox(frame_obrigatorias, textvariable=mapeamento['email'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_email.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
                combo_email.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                # Tenta identificar colunas automaticamente
                for i, col in enumerate(cabecalho):
                    col_lower = str(col).lower()
                    if 'nome' in col_lower:
                        mapeamento['nome'].set(col)
                    elif 'email' in col_lower or 'e-mail' in col_lower:
                        mapeamento['email'].set(col)
                
                # Frame para colunas opcionais
                frame_opcionais = ttk.LabelFrame(frame_mapeamento, text="Colunas Opcionais", padding=10)
                frame_opcionais.pack(fill=tk.X)
                
                ttk.Label(frame_opcionais, text="Cargo:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(frame_opcionais, text="Departamento:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(frame_opcionais, text="Telefone:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(frame_opcionais, text="Prefeitura:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
                
                mapeamento['cargo'] = tk.StringVar(value="Nenhum")
                mapeamento['departamento'] = tk.StringVar(value="Nenhum")
                mapeamento['telefone'] = tk.StringVar(value="Nenhum")
                mapeamento['prefeitura'] = tk.StringVar(value="Nenhum")
                
                combo_cargo = ttk.Combobox(frame_opcionais, textvariable=mapeamento['cargo'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_cargo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
                combo_cargo.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                combo_departamento = ttk.Combobox(frame_opcionais, textvariable=mapeamento['departamento'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_departamento.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
                combo_departamento.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                combo_telefone = ttk.Combobox(frame_opcionais, textvariable=mapeamento['telefone'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_telefone.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
                combo_telefone.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                combo_prefeitura = ttk.Combobox(frame_opcionais, textvariable=mapeamento['prefeitura'], values=cabecalho_opcoes, state="readonly", width=30)
                combo_prefeitura.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
                combo_prefeitura.bind("<<ComboboxSelected>>", lambda e: atualizar_preview())
                
                # Tenta identificar colunas opcionais automaticamente
                for i, col in enumerate(cabecalho):
                    col_lower = str(col).lower()
                    if 'cargo' in col_lower or 'função' in col_lower:
                        mapeamento['cargo'].set(col)
                    elif 'departamento' in col_lower or 'setor' in col_lower:
                        mapeamento['departamento'].set(col)
                    elif 'telefone' in col_lower or 'fone' in col_lower or 'celular' in col_lower:
                        mapeamento['telefone'].set(col)
                    elif 'prefeitura' in col_lower or 'cidade' in col_lower or 'local' in col_lower:
                        mapeamento['prefeitura'].set(col)
                
                # Prefeitura padrão
                frame_prefeitura = ttk.Frame(frame_importacao)
                frame_prefeitura.pack(fill=tk.X, pady=(0, 10))
                
                ttk.Label(frame_prefeitura, text="Prefeitura padrão (para registros sem prefeitura definida):", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
                
                prefeitura_padrao = tk.StringVar(value="São José" if self.prefeitura_atual == 'sj' else "Florianópolis")
                
                rb_sj = ttk.Radiobutton(frame_prefeitura, text="São José", variable=prefeitura_padrao, value="São José")
                rb_sj.pack(side=tk.LEFT, padx=5, pady=5)
                
                rb_floripa = ttk.Radiobutton(frame_prefeitura, text="Florianópolis", variable=prefeitura_padrao, value="Florianópolis")
                rb_floripa.pack(side=tk.LEFT, padx=5, pady=5)
                
                # Função para atualizar a pré-visualização
                def atualizar_preview():
                    # Limpa a tabela
                    for item in tabela_preview.get_children():
                        tabela_preview.delete(item)
                    
                    # Limita a pré-visualização a 50 registros
                    dados_preview = dados[:50]
                    
                    # Para cada linha, extrai os valores conforme o mapeamento
                    for linha in dados_preview:
                        valores = {}
                        
                        for campo, coluna in mapeamento.items():
                            col_nome = coluna.get()
                            
                            if col_nome != "Nenhum" and col_nome in cabecalho:
                                idx = cabecalho.index(col_nome)
                                valores[campo] = linha[idx] if idx < len(linha) else ""
                            else:
                                valores[campo] = ""
                        
                        # Determina a prefeitura
                        if valores.get('prefeitura'):
                            pref = str(valores['prefeitura']).lower()
                            if 'jose' in pref or 'josé' in pref or 'sj' in pref:
                                valores['prefeitura'] = "São José"
                            elif 'floripa' in pref or 'florianópolis' in pref or 'fpolis' in pref:
                                valores['prefeitura'] = "Florianópolis"
                            else:
                                valores['prefeitura'] = prefeitura_padrao.get()
                        else:
                            valores['prefeitura'] = prefeitura_padrao.get()
                        
                        # Insere na tabela
                        if valores.get('nome') and valores.get('email'):
                            tabela_preview.insert("", tk.END, values=(
                                valores.get('nome', ""),
                                valores.get('email', ""),
                                valores.get('cargo', ""),
                                valores.get('departamento', ""),
                                valores.get('telefone', ""),
                                valores.get('prefeitura', "")
                            ))
                
                # Contador de registros
                lbl_contador = ttk.Label(frame_importacao, text=f"Total de registros no arquivo: {len(dados)}")
                lbl_contador.pack(anchor=tk.W, pady=(0, 10))
                
                # Atualiza a pré-visualização inicial
                atualizar_preview()
                
                # Botões de ação
                frame_botoes = ttk.Frame(janela_importacao)
                frame_botoes.pack(fill=tk.X, pady=10)
                
                btn_importar = ttk.Button(frame_botoes, text="Importar", command=lambda: importar_dados())
                btn_importar.pack(side=tk.RIGHT, padx=5)
                
                btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_importacao.destroy)
                btn_cancelar.pack(side=tk.RIGHT, padx=5)
                
                # Função para importar os dados
                def importar_dados():
                    try:
                        # Verifica mapeamento obrigatório
                        if mapeamento['nome'].get() == "Nenhum" or mapeamento['email'].get() == "Nenhum":
                            messagebox.showwarning("Aviso", "É necessário mapear as colunas 'Nome' e 'E-mail'.")
                            return
                        
                        # Processa todos os registros
                        importados = 0
                        ignorados = 0
                        
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        
                        for linha in dados:
                            valores = {}
                            
                            for campo, coluna in mapeamento.items():
                                col_nome = coluna.get()
                                
                                if col_nome != "Nenhum" and col_nome in cabecalho:
                                    idx = cabecalho.index(col_nome)
                                    valores[campo] = linha[idx] if idx < len(linha) else ""
                                else:
                                    valores[campo] = ""
                            
                            # Verifica campos obrigatórios
                            if not valores.get('nome') or not valores.get('email'):
                                ignorados += 1
                                continue
                            
                            # Determina a prefeitura
                            prefeitura_codigo = 'sj'  # Padrão
                            
                            if valores.get('prefeitura'):
                                pref = str(valores['prefeitura']).lower()
                                if 'jose' in pref or 'josé' in pref or 'sj' in pref:
                                    prefeitura_codigo = 'sj'
                                elif 'floripa' in pref or 'florianópolis' in pref or 'fpolis' in pref:
                                    prefeitura_codigo = 'floripa'
                                else:
                                    prefeitura_codigo = 'sj' if prefeitura_padrao.get() == "São José" else 'floripa'
                            else:
                                prefeitura_codigo = 'sj' if prefeitura_padrao.get() == "São José" else 'floripa'
                            
                            # Verifica se já existe um funcionário com este e-mail
                            cursor.execute('SELECT id FROM funcionarios WHERE email = ?', (valores.get('email'),))
                            existente = cursor.fetchone()
                            
                            if existente:
                                # Atualiza o funcionário existente
                                cursor.execute('''
                                UPDATE funcionarios SET 
                                    nome = ?, cargo = ?, departamento = ?, 
                                    telefone = ?, prefeitura = ?
                                WHERE email = ?
                                ''', (
                                    valores.get('nome', ""),
                                    valores.get('cargo', ""),
                                    valores.get('departamento', ""),
                                    valores.get('telefone', ""),
                                    prefeitura_codigo,
                                    valores.get('email', "")
                                ))
                            else:
                                # Insere novo funcionário
                                cursor.execute('''
                                INSERT INTO funcionarios 
                                    (nome, email, cargo, departamento, telefone, prefeitura)
                                VALUES (?, ?, ?, ?, ?, ?)
                                ''', (
                                    valores.get('nome', ""),
                                    valores.get('email', ""),
                                    valores.get('cargo', ""),
                                    valores.get('departamento', ""),
                                    valores.get('telefone', ""),
                                    prefeitura_codigo
                                ))
                            
                            importados += 1
                        
                        # Registra no log
                        cursor.execute('''
                        INSERT INTO logs (usuario_id, acao, descricao)
                        VALUES (?, ?, ?)
                        ''', (
                            self.usuario_atual['id'], "IMPORTACAO_FUNCIONARIOS", 
                            f"Importados {importados} funcionários, ignorados {ignorados} registros"
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        # Atualiza a lista de funcionários
                        self.atualizar_lista_funcionarios()
                        
                        # Atualiza departamentos
                        self.carregar_departamentos()
                        
                        # Mensagem de sucesso
                        messagebox.showinfo(
                            "Importação Concluída", 
                            f"Importação concluída com sucesso!\n\n"
                            f"Registros importados: {importados}\n"
                            f"Registros ignorados: {ignorados}"
                        )
                        
                        # Fecha a janela
                        janela_importacao.destroy()
                        
                    except Exception as e:
                        logger.error(f"Erro ao importar dados: {e}")
                        messagebox.showerror("Erro", f"Falha ao importar dados: {e}")
                
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo: {e}")
                messagebox.showerror("Erro", f"Falha ao carregar o arquivo: {e}")
                janela_importacao.destroy()
                
        except Exception as e:
            logger.error(f"Erro ao importar funcionários: {e}")
            messagebox.showerror("Erro", f"Falha ao iniciar importação: {e}")
    
    def exportar_funcionarios_csv(self):
        """Exporta a lista de funcionários para um arquivo CSV."""
        try:
            filetypes = [('Arquivos CSV', '*.csv')]
            
            filename = filedialog.asksaveasfilename(
                title="Exportar Funcionários para CSV",
                filetypes=filetypes,
                defaultextension=".csv"
            )
            
            if not filename:
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Obtém todos os funcionários
            cursor.execute('''
            SELECT nome, email, cargo, departamento, telefone, 
                   CASE WHEN prefeitura = 'sj' THEN 'São José' ELSE 'Florianópolis' END as prefeitura, 
                   CASE WHEN ativo = 1 THEN 'Ativo' ELSE 'Inativo' END as status
            FROM funcionarios
            ORDER BY nome
            ''')
            
            funcionarios = cursor.fetchall()
            
            conn.close()
            
            # Escreve o arquivo CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeçalho
                writer.writerow(['Nome', 'E-mail', 'Cargo', 'Departamento', 'Telefone', 'Prefeitura', 'Status'])
                
                # Dados
                for func in funcionarios:
                    writer.writerow(func)
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", f"Funcionários exportados com sucesso para {filename}")
            
            # Registra no log
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXPORTACAO_FUNCIONARIOS", 
                f"Exportados {len(funcionarios)} funcionários para CSV"
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao exportar funcionários para CSV: {e}")
            messagebox.showerror("Erro", f"Falha ao exportar funcionários: {e}")
    
    def exportar_funcionarios_excel(self):
        """Exporta a lista de funcionários para um arquivo Excel."""
        try:
            filetypes = [('Arquivos Excel', '*.xlsx')]
            
            filename = filedialog.asksaveasfilename(
                title="Exportar Funcionários para Excel",
                filetypes=filetypes,
                defaultextension=".xlsx"
            )
            
            if not filename:
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Obtém todos os funcionários
            cursor.execute('''
            SELECT nome, email, cargo, departamento, telefone, 
                   CASE WHEN prefeitura = 'sj' THEN 'São José' ELSE 'Florianópolis' END as prefeitura, 
                   CASE WHEN ativo = 1 THEN 'Ativo' ELSE 'Inativo' END as status
            FROM funcionarios
            ORDER BY nome
            ''')
            
            funcionarios = cursor.fetchall()
            
            conn.close()
            
            # Cria DataFrame e exporta para Excel
            df = pd.DataFrame(funcionarios, columns=['Nome', 'E-mail', 'Cargo', 'Departamento', 'Telefone', 'Prefeitura', 'Status'])
            df.to_excel(filename, index=False)
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", f"Funcionários exportados com sucesso para {filename}")
            
            # Registra no log
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXPORTACAO_FUNCIONARIOS", 
                f"Exportados {len(funcionarios)} funcionários para Excel"
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao exportar funcionários para Excel: {e}")
            messagebox.showerror("Erro", f"Falha ao exportar funcionários: {e}")
    
    def atualizar_lista_usuarios(self):
        """Atualiza a lista de usuários."""
        try:
            # Limpa a lista atual
            for item in self.lista_usuarios.get_children():
                self.lista_usuarios.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, nome, email, prefeitura, nivel_acesso, ultimo_acesso
            FROM usuarios
            ORDER BY nome
            ''')
            
            usuarios = cursor.fetchall()
            
            for user in usuarios:
                id_user, nome, email, prefeitura, nivel, ultimo_acesso = user
                
                # Formata a prefeitura
                prefeitura_nome = "São José" if prefeitura == 'sj' else "Florianópolis"
                
                # Formata o nível de acesso
                if nivel == 1:
                    nivel_texto = "Usuário"
                elif nivel == 2:
                    nivel_texto = "Supervisor"
                else:
                    nivel_texto = "Administrador"
                
                # Formata a data de último acesso
                if ultimo_acesso:
                    data_formatada = datetime.datetime.strptime(ultimo_acesso, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                else:
                    data_formatada = "Nunca acessou"
                
                self.lista_usuarios.insert("", tk.END, values=(
                    id_user, nome, email, prefeitura_nome, nivel_texto, data_formatada
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de usuários: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar usuários: {e}")
    
    def salvar_usuario(self):
        """Salva um novo usuário ou atualiza um existente."""
        try:
            nome = self.entry_nome_usuario.get().strip()
            email = self.entry_email_usuario.get().strip()
            senha = self.entry_senha_usuario.get()
            confirmar_senha = self.entry_confirmar_senha.get()
            cargo = self.entry_cargo_usuario.get().strip()
            departamento = self.combo_departamento_usuario.get().strip()
            telefone = self.entry_telefone_usuario.get().strip()
            
            # Prefeitura selecionada
            prefeitura = 'sj' if self.combo_prefeitura_usuario.get() == "São José" else 'floripa'
            
            # Nível de acesso
            nivel_texto = self.combo_nivel_acesso.get()
            if nivel_texto == "Administrador":
                nivel = 3
            elif nivel_texto == "Supervisor":
                nivel = 2
            else:
                nivel = 1
            
            if not nome or not email:
                messagebox.showwarning("Aviso", "Nome e e-mail são campos obrigatórios.")
                return
            
            # Validação básica de e-mail
            import re
            padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(padrao_email, email):
                messagebox.showwarning("Aviso", "O e-mail informado parece ser inválido.")
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Verifica se é um usuário existente sendo editado
            usuario_existente = False
            usuario_id = None
            
            for item in self.lista_usuarios.selection():
                valores = self.lista_usuarios.item(item, 'values')
                usuario_id = valores[0]
                usuario_existente = True
                break
            
            if usuario_existente and usuario_id:
                # Se a senha foi preenchida, atualiza também a senha
                if senha:
                    if senha != confirmar_senha:
                        messagebox.showwarning("Aviso", "A senha e a confirmação não coincidem.")
                        conn.close()
                        return
                    
                    # Hash da senha
                    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                    
                    # Atualiza o usuário existente com nova senha
                    cursor.execute('''
                    UPDATE usuarios SET 
                        nome = ?, email = ?, senha = ?, cargo = ?, 
                        departamento = ?, telefone = ?, prefeitura = ?, nivel_acesso = ?
                    WHERE id = ?
                    ''', (nome, email, senha_hash, cargo, departamento, telefone, prefeitura, nivel, usuario_id))
                else:
                    # Atualiza o usuário existente sem alterar a senha
                    cursor.execute('''
                    UPDATE usuarios SET 
                        nome = ?, email = ?, cargo = ?, 
                        departamento = ?, telefone = ?, prefeitura = ?, nivel_acesso = ?
                    WHERE id = ?
                    ''', (nome, email, cargo, departamento, telefone, prefeitura, nivel, usuario_id))
                
                mensagem_log = f"Usuário #{usuario_id} atualizado"
                mensagem_sucesso = "Usuário atualizado com sucesso!"
                
            else:
                # Verifica se o e-mail já existe
                cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
                if cursor.fetchone():
                    messagebox.showwarning("Aviso", "Já existe um usuário com este e-mail.")
                    conn.close()
                    return
                
                # Verifica se a senha foi preenchida
                if not senha:
                    messagebox.showwarning("Aviso", "A senha é obrigatória para novos usuários.")
                    conn.close()
                    return
                
                if senha != confirmar_senha:
                    messagebox.showwarning("Aviso", "A senha e a confirmação não coincidem.")
                    conn.close()
                    return
                
                # Hash da senha
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                
                # Cria um novo usuário
                cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, cargo, departamento, telefone, prefeitura, nivel_acesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nome, email, senha_hash, cargo, departamento, telefone, prefeitura, nivel))
                
                usuario_id = cursor.lastrowid
                mensagem_log = f"Novo usuário #{usuario_id} criado"
                mensagem_sucesso = "Usuário cadastrado com sucesso!"
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (self.usuario_atual['id'], "USUARIO", mensagem_log))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_usuarios()
            
            # Limpa os campos
            self.limpar_campos_usuario()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", mensagem_sucesso)
            
        except Exception as e:
            logger.error(f"Erro ao salvar usuário: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar usuário: {e}")
    
    def editar_usuario(self):
        """Carrega um usuário para edição."""
        try:
            selecionado = self.lista_usuarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um usuário para editar.")
                return
            
            valores = self.lista_usuarios.item(selecionado[0], 'values')
            usuario_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT nome, email, cargo, departamento, telefone, prefeitura, nivel_acesso
            FROM usuarios
            WHERE id = ?
            ''', (usuario_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                nome, email, cargo, departamento, telefone, prefeitura, nivel = resultado
                
                # Preenche os campos
                self.entry_nome_usuario.delete(0, tk.END)
                self.entry_nome_usuario.insert(0, nome)
                
                self.entry_email_usuario.delete(0, tk.END)
                self.entry_email_usuario.insert(0, email)
                
                # Limpa os campos de senha
                self.entry_senha_usuario.delete(0, tk.END)
                self.entry_confirmar_senha.delete(0, tk.END)
                
                self.entry_cargo_usuario.delete(0, tk.END)
                self.entry_cargo_usuario.insert(0, cargo or "")
                
                self.combo_departamento_usuario.set(departamento or "")
                
                self.entry_telefone_usuario.delete(0, tk.END)
                self.entry_telefone_usuario.insert(0, telefone or "")
                
                self.combo_prefeitura_usuario.set("São José" if prefeitura == 'sj' else "Florianópolis")
                
                # Nível de acesso
                if nivel == 3:
                    self.combo_nivel_acesso.current(2)  # Administrador
                elif nivel == 2:
                    self.combo_nivel_acesso.current(1)  # Supervisor
                else:
                    self.combo_nivel_acesso.current(0)  # Usuário
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao editar usuário: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar usuário para edição: {e}")
    
    def excluir_usuario(self):
        """Exclui um usuário selecionado."""
        try:
            selecionado = self.lista_usuarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um usuário para excluir.")
                return
            
            valores = self.lista_usuarios.item(selecionado[0], 'values')
            usuario_id = valores[0]
            nome = valores[1]
            
            # Não permite excluir o próprio usuário
            if int(usuario_id) == self.usuario_atual['id']:
                messagebox.showwarning("Aviso", "Não é possível excluir o próprio usuário.")
                return
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente excluir o usuário '{nome}'?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Exclui o usuário
            cursor.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXCLUSAO_USUARIO", 
                f"Usuário #{usuario_id} ({nome}) excluído"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_usuarios()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao excluir usuário: {e}")
            messagebox.showerror("Erro", f"Falha ao excluir usuário: {e}")
    
    def resetar_senha_usuario(self):
        """Reseta a senha de um usuário para o valor padrão."""
        try:
            selecionado = self.lista_usuarios.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um usuário para resetar a senha.")
                return
            
            valores = self.lista_usuarios.item(selecionado[0], 'values')
            usuario_id = valores[0]
            nome = valores[1]
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente resetar a senha do usuário '{nome}'?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Senha padrão: "123456"
            senha_padrao = "123456"
            senha_hash = hashlib.sha256(senha_padrao.encode()).hexdigest()
            
            # Atualiza a senha
            cursor.execute('UPDATE usuarios SET senha = ? WHERE id = ?', (senha_hash, usuario_id))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "RESET_SENHA", 
                f"Senha do usuário #{usuario_id} ({nome}) resetada"
            ))
            
            conn.commit()
            conn.close()
            
            # Mensagem de sucesso
            messagebox.showinfo(
                "Senha Resetada", 
                f"A senha do usuário '{nome}' foi resetada para '{senha_padrao}'.\n\n"
                f"Oriente o usuário a alterar a senha após o primeiro acesso."
            )
            
        except Exception as e:
            logger.error(f"Erro ao resetar senha: {e}")
            messagebox.showerror("Erro", f"Falha ao resetar senha: {e}")
    
    def atualizar_lista_grupos(self):
        """Atualiza a lista de grupos."""
        try:
            # Limpa a lista atual
            for item in self.lista_grupos.get_children():
                self.lista_grupos.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT g.id, g.nome, g.descricao, g.prefeitura, COUNT(gf.funcionario_id) as membros
            FROM grupos g
            LEFT JOIN grupo_funcionario gf ON g.id = gf.grupo_id
            GROUP BY g.id
            ORDER BY g.nome''')
            
            grupos = cursor.fetchall()
            
            for grupo in grupos:
                id_grupo, nome, descricao, prefeitura, membros = grupo
                
                # Formata a prefeitura
                prefeitura_nome = "São José" if prefeitura == 'sj' else "Florianópolis"
                
                self.lista_grupos.insert("", tk.END, values=(
                    id_grupo, nome, descricao, prefeitura_nome, membros
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de grupos: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar grupos: {e}")
    
    def salvar_grupo(self):
        """Salva um novo grupo ou atualiza um existente."""
        try:
            nome = self.entry_nome_grupo.get().strip()
            descricao = self.entry_descricao_grupo.get().strip()
            
            # Prefeitura selecionada
            prefeitura = 'sj' if self.combo_prefeitura_grupo.get() == "São José" else 'floripa'
            
            if not nome:
                messagebox.showwarning("Aviso", "O nome do grupo é obrigatório.")
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Verifica se é um grupo existente sendo editado
            grupo_existente = False
            grupo_id = None
            
            for item in self.lista_grupos.selection():
                valores = self.lista_grupos.item(item, 'values')
                grupo_id = valores[0]
                grupo_existente = True
                break
            
            if grupo_existente and grupo_id:
                # Atualiza o grupo existente
                cursor.execute('''
                UPDATE grupos SET 
                    nome = ?, descricao = ?, prefeitura = ?
                WHERE id = ?
                ''', (nome, descricao, prefeitura, grupo_id))
                
                mensagem_log = f"Grupo #{grupo_id} atualizado"
                mensagem_sucesso = "Grupo atualizado com sucesso!"
                
            else:
                # Cria um novo grupo
                cursor.execute('''
                INSERT INTO grupos (nome, descricao, prefeitura)
                VALUES (?, ?, ?)
                ''', (nome, descricao, prefeitura))
                
                grupo_id = cursor.lastrowid
                mensagem_log = f"Novo grupo #{grupo_id} criado"
                mensagem_sucesso = "Grupo criado com sucesso!"
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (self.usuario_atual['id'], "GRUPO", mensagem_log))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_grupos()
            
            # Limpa os campos
            self.limpar_campos_grupo()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", mensagem_sucesso)
            
        except Exception as e:
            logger.error(f"Erro ao salvar grupo: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar grupo: {e}")
    
    def editar_grupo(self):
        """Carrega um grupo para edição."""
        try:
            selecionado = self.lista_grupos.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um grupo para editar.")
                return
            
            valores = self.lista_grupos.item(selecionado[0], 'values')
            grupo_id = valores[0]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT nome, descricao, prefeitura FROM grupos WHERE id = ?', (grupo_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                nome, descricao, prefeitura = resultado
                
                # Preenche os campos
                self.entry_nome_grupo.delete(0, tk.END)
                self.entry_nome_grupo.insert(0, nome)
                
                self.entry_descricao_grupo.delete(0, tk.END)
                self.entry_descricao_grupo.insert(0, descricao or "")
                
                self.combo_prefeitura_grupo.set("São José" if prefeitura == 'sj' else "Florianópolis")
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao editar grupo: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar grupo para edição: {e}")
    
    def excluir_grupo(self):
        """Exclui um grupo selecionado."""
        try:
            selecionado = self.lista_grupos.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um grupo para excluir.")
                return
            
            valores = self.lista_grupos.item(selecionado[0], 'values')
            grupo_id = valores[0]
            nome = valores[1]
            
            # Confirmação
            if not messagebox.askyesno("Confirmação", f"Deseja realmente excluir o grupo '{nome}'?"):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Remove os funcionários do grupo
            cursor.execute('DELETE FROM grupo_funcionario WHERE grupo_id = ?', (grupo_id,))
            
            # Exclui o grupo
            cursor.execute('DELETE FROM grupos WHERE id = ?', (grupo_id,))
            
            # Registra no log
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "EXCLUSAO_GRUPO", 
                f"Grupo #{grupo_id} ({nome}) excluído"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_grupos()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", "Grupo excluído com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao excluir grupo: {e}")
            messagebox.showerror("Erro", f"Falha ao excluir grupo: {e}")
    
    def gerenciar_membros_grupo(self):
        """Gerencia os membros de um grupo."""
        try:
            selecionado = self.lista_grupos.selection()
            
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um grupo para gerenciar membros.")
                return
            
            valores = self.lista_grupos.item(selecionado[0], 'values')
            grupo_id = valores[0]
            nome_grupo = valores[1]
            prefeitura = 'sj' if valores[3] == "São José" else 'floripa'
            
            # Cria janela de gerenciamento de membros
            janela_membros = tk.Toplevel(self.root)
            janela_membros.title(f"Membros do Grupo: {nome_grupo}")
            janela_membros.geometry("800x600")
            janela_membros.minsize(600, 400)
            janela_membros.transient(self.root)
            janela_membros.grab_set()
            
            frame_membros = ttk.Frame(janela_membros, padding=10)
            frame_membros.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame_membros, text=f"Gerenciar membros do grupo: {nome_grupo}", font=('Helvetica', 12, 'bold')).pack(pady=(0, 10))
            
            # Frame de busca
            frame_busca = ttk.Frame(frame_membros)
            frame_busca.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(frame_busca, text="Buscar funcionário:").pack(side=tk.LEFT, padx=5)
            
            entry_busca = ttk.Entry(frame_busca, width=30)
            entry_busca.pack(side=tk.LEFT, padx=5)
            
            btn_buscar = ttk.Button(frame_busca, text="Buscar", command=lambda: buscar_funcionarios())
            btn_buscar.pack(side=tk.LEFT, padx=5)
            
            # Frame para listas
            frame_listas = ttk.Frame(frame_membros)
            frame_listas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Frame para lista de funcionários disponíveis
            frame_disponiveis = ttk.LabelFrame(frame_listas, text="Funcionários Disponíveis")
            frame_disponiveis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            lista_disponiveis = ttk.Treeview(frame_disponiveis, columns=('id', 'nome', 'email', 'departamento'), show='headings', height=15)
            lista_disponiveis.heading('id', text='ID')
            lista_disponiveis.heading('nome', text='Nome')
            lista_disponiveis.heading('email', text='E-mail')
            lista_disponiveis.heading('departamento', text='Departamento')
            
            lista_disponiveis.column('id', width=50)
            lista_disponiveis.column('nome', width=150)
            lista_disponiveis.column('email', width=150)
            lista_disponiveis.column('departamento', width=100)
            
            lista_disponiveis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_disponiveis = ttk.Scrollbar(frame_disponiveis, orient=tk.VERTICAL, command=lista_disponiveis.yview)
            scrollbar_disponiveis.pack(side=tk.RIGHT, fill=tk.Y)
            lista_disponiveis.config(yscrollcommand=scrollbar_disponiveis.set)
            
            # Frame de botões para adicionar/remover
            frame_botoes_mover = ttk.Frame(frame_listas)
            frame_botoes_mover.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            btn_adicionar = ttk.Button(frame_botoes_mover, text=">>", width=5, command=lambda: adicionar_membro())
            btn_adicionar.pack(pady=5)
            
            btn_remover = ttk.Button(frame_botoes_mover, text="<<", width=5, command=lambda: remover_membro())
            btn_remover.pack(pady=5)
            
            # Frame para lista de membros
            frame_membros_grupo = ttk.LabelFrame(frame_listas, text="Membros do Grupo")
            frame_membros_grupo.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            lista_membros = ttk.Treeview(frame_membros_grupo, columns=('id', 'nome', 'email', 'departamento'), show='headings', height=15)
            lista_membros.heading('id', text='ID')
            lista_membros.heading('nome', text='Nome')
            lista_membros.heading('email', text='E-mail')
            lista_membros.heading('departamento', text='Departamento')
            
            lista_membros.column('id', width=50)
            lista_membros.column('nome', width=150)
            lista_membros.column('email', width=150)
            lista_membros.column('departamento', width=100)
            
            lista_membros.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar_membros = ttk.Scrollbar(frame_membros_grupo, orient=tk.VERTICAL, command=lista_membros.yview)
            scrollbar_membros.pack(side=tk.RIGHT, fill=tk.Y)
            lista_membros.config(yscrollcommand=scrollbar_membros.set)
            
            # Contadores
            frame_contadores = ttk.Frame(frame_membros)
            frame_contadores.pack(fill=tk.X, pady=(0, 10))
            
            lbl_contador_disponiveis = ttk.Label(frame_contadores, text="Disponíveis: 0")
            lbl_contador_disponiveis.pack(side=tk.LEFT, padx=5)
            
            lbl_contador_membros = ttk.Label(frame_contadores, text="Membros: 0")
            lbl_contador_membros.pack(side=tk.RIGHT, padx=5)
            
            # Botões de ação
            frame_botoes = ttk.Frame(janela_membros)
            frame_botoes.pack(fill=tk.X, pady=10)
            
            btn_salvar = ttk.Button(frame_botoes, text="Salvar", command=lambda: salvar_membros())
            btn_salvar.pack(side=tk.RIGHT, padx=5)
            
            btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", command=janela_membros.destroy)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Função para buscar funcionários
            def buscar_funcionarios():
                try:
                    busca = entry_busca.get().strip()
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Limpa a lista de funcionários disponíveis
                    for item in lista_disponiveis.get_children():
                        lista_disponiveis.delete(item)
                    
                    # Busca funcionários da mesma prefeitura que não são membros do grupo
                    if busca:
                        cursor.execute('''
                        SELECT f.id, f.nome, f.email, f.departamento
                        FROM funcionarios f
                        WHERE f.prefeitura = ? AND f.ativo = 1
                        AND f.id NOT IN (
                            SELECT funcionario_id FROM grupo_funcionario WHERE grupo_id = ?
                        )
                        AND (f.nome LIKE ? OR f.email LIKE ? OR f.departamento LIKE ?)
                        ORDER BY f.nome
                        ''', (prefeitura, grupo_id, f'%{busca}%', f'%{busca}%', f'%{busca}%'))
                    else:
                        cursor.execute('''
                        SELECT f.id, f.nome, f.email, f.departamento
                        FROM funcionarios f
                        WHERE f.prefeitura = ? AND f.ativo = 1
                        AND f.id NOT IN (
                            SELECT funcionario_id FROM grupo_funcionario WHERE grupo_id = ?
                        )
                        ORDER BY f.nome
                        ''', (prefeitura, grupo_id))
                    
                    funcionarios = cursor.fetchall()
                    
                    for func in funcionarios:
                        lista_disponiveis.insert("", tk.END, values=func)
                    
                    # Atualiza o contador
                    lbl_contador_disponiveis.config(text=f"Disponíveis: {len(funcionarios)}")
                    
                    conn.close()
                except Exception as e:
                    logger.error(f"Erro ao buscar funcionários: {e}")
                    messagebox.showerror("Erro", f"Falha ao buscar funcionários: {e}")
            
            # Função para carregar membros do grupo
            def carregar_membros():
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Limpa a lista de membros
                    for item in lista_membros.get_children():
                        lista_membros.delete(item)
                    
                    # Busca os membros do grupo
                    cursor.execute('''
                    SELECT f.id, f.nome, f.email, f.departamento
                    FROM funcionarios f
                    JOIN grupo_funcionario gf ON f.id = gf.funcionario_id
                    WHERE gf.grupo_id = ?
                    ORDER BY f.nome
                    ''', (grupo_id,))
                    
                    membros = cursor.fetchall()
                    
                    for membro in membros:
                        lista_membros.insert("", tk.END, values=membro)
                    
                    # Atualiza o contador
                    lbl_contador_membros.config(text=f"Membros: {len(membros)}")
                    
                    conn.close()
                except Exception as e:
                    logger.error(f"Erro ao carregar membros: {e}")
                    messagebox.showerror("Erro", f"Falha ao carregar membros: {e}")
            
            # Função para adicionar membro
            def adicionar_membro():
                try:
                    selecionados = lista_disponiveis.selection()
                    
                    if not selecionados:
                        messagebox.showwarning("Aviso", "Selecione pelo menos um funcionário para adicionar.")
                        return
                    
                    for item in selecionados:
                        valores = lista_disponiveis.item(item, 'values')
                        
                        # Adiciona à lista de membros
                        lista_membros.insert("", tk.END, values=valores)
                        
                        # Remove da lista de disponíveis
                        lista_disponiveis.delete(item)
                    
                    # Atualiza contadores
                    lbl_contador_disponiveis.config(text=f"Disponíveis: {len(lista_disponiveis.get_children())}")
                    lbl_contador_membros.config(text=f"Membros: {len(lista_membros.get_children())}")
                except Exception as e:
                    logger.error(f"Erro ao adicionar membro: {e}")
                    messagebox.showerror("Erro", f"Falha ao adicionar membro: {e}")
            
            # Função para remover membro
            def remover_membro():
                try:
                    selecionados = lista_membros.selection()
                    
                    if not selecionados:
                        messagebox.showwarning("Aviso", "Selecione pelo menos um membro para remover.")
                        return
                    
                    for item in selecionados:
                        valores = lista_membros.item(item, 'values')
                        
                        # Adiciona à lista de disponíveis
                        lista_disponiveis.insert("", tk.END, values=valores)
                        
                        # Remove da lista de membros
                        lista_membros.delete(item)
                    
                    # Atualiza contadores
                    lbl_contador_disponiveis.config(text=f"Disponíveis: {len(lista_disponiveis.get_children())}")
                    lbl_contador_membros.config(text=f"Membros: {len(lista_membros.get_children())}")
                except Exception as e:
                    logger.error(f"Erro ao remover membro: {e}")
                    messagebox.showerror("Erro", f"Falha ao remover membro: {e}")
            
            # Função para salvar membros
            def salvar_membros():
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Remove todos os membros atuais
                    cursor.execute('DELETE FROM grupo_funcionario WHERE grupo_id = ?', (grupo_id,))
                    
                    # Adiciona os novos membros
                    for item in lista_membros.get_children():
                        valores = lista_membros.item(item, 'values')
                        funcionario_id = valores[0]
                        
                        cursor.execute('''
                        INSERT INTO grupo_funcionario (grupo_id, funcionario_id)
                        VALUES (?, ?)
                        ''', (grupo_id, funcionario_id))
                    
                    # Registra no log
                    cursor.execute('''
                    INSERT INTO logs (usuario_id, acao, descricao)
                    VALUES (?, ?, ?)
                    ''', (
                        self.usuario_atual['id'], "MEMBROS_GRUPO", 
                        f"Membros do grupo #{grupo_id} ({nome_grupo}) atualizados"
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    # Atualiza a lista de grupos
                    self.atualizar_lista_grupos()
                    
                    # Mensagem de sucesso
                    messagebox.showinfo("Sucesso", "Membros do grupo atualizados com sucesso!")
                    
                    # Fecha a janela
                    janela_membros.destroy()
                except Exception as e:
                    logger.error(f"Erro ao salvar membros: {e}")
                    messagebox.showerror("Erro", f"Falha ao salvar membros: {e}")
            
            # Carrega os dados iniciais
            buscar_funcionarios()
            carregar_membros()
            
        except Exception as e:
            logger.error(f"Erro ao gerenciar membros: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir gerenciamento de membros: {e}")
    
    def atualizar_lista_logs(self):
        """Atualiza a lista de logs."""
        try:
            # Limpa a lista atual
            for item in self.lista_logs.get_children():
                self.lista_logs.delete(item)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Obtém os filtros
            acao = self.combo_acao_log.get() if hasattr(self, 'combo_acao_log') and self.combo_acao_log.get() else None
            usuario = self.combo_usuario_log.get() if hasattr(self, 'combo_usuario_log') and self.combo_usuario_log.get() else None
            data_inicial = self.data_inicial_log.get_date() if hasattr(self, 'data_inicial_log') else None
            data_final = self.data_final_log.get_date() if hasattr(self, 'data_final_log') else None
            
            # Constrói a consulta SQL com os filtros
            sql = '''
            SELECT l.id, l.data, IFNULL(u.nome, 'Sistema'), l.acao, l.descricao
            FROM logs l
            LEFT JOIN usuarios u ON l.usuario_id = u.id
            WHERE 1=1
            '''
            params = []
            
            if acao:
                sql += " AND l.acao = ?"
                params.append(acao)
            
            if usuario:
                usuario_id = usuario.split(" - ")[0] if " - " in usuario else None
                if usuario_id:
                    sql += " AND l.usuario_id = ?"
                    params.append(usuario_id)
            
            if data_inicial:
                sql += " AND date(l.data) >= date(?)"
                params.append(data_inicial.strftime('%Y-%m-%d'))
            
            if data_final:
                sql += " AND date(l.data) <= date(?)"
                params.append(data_final.strftime('%Y-%m-%d'))
            
            sql += " ORDER BY l.data DESC LIMIT 1000"
            
            cursor.execute(sql, params)
            logs = cursor.fetchall()
            
            for log in logs:
                id_log, data, usuario, acao, descricao = log
                
                # Formata a data
                data_formatada = datetime.datetime.strptime(data, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                
                self.lista_logs.insert("", tk.END, values=(
                    id_log, data_formatada, usuario, acao, descricao
                ))
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar lista de logs: {e}")
            messagebox.showerror("Erro", f"Falha ao carregar logs: {e}")
    
    def carregar_dados_filtros_log(self):
        """Carrega os dados para os filtros de logs."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Carrega as ações
            cursor.execute('SELECT DISTINCT acao FROM logs ORDER BY acao')
            acoes = [a[0] for a in cursor.fetchall()]
            self.combo_acao_log.config(values=[""] + acoes)
            
            # Carrega os usuários
            cursor.execute('SELECT id, nome FROM usuarios ORDER BY nome')
            usuarios = [f"{id} - {nome}" for id, nome in cursor.fetchall()]
            self.combo_usuario_log.config(values=[""] + usuarios)
            
            # Configura as datas padrão
            self.data_inicial_log.set_date(datetime.date.today() - datetime.timedelta(days=7))
            self.data_final_log.set_date(datetime.date.today())
            
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar dados para filtros de logs: {e}")
    
    def filtrar_logs(self):
        """Aplica os filtros à lista de logs."""
        self.atualizar_lista_logs()
    
    def exportar_logs(self):
        """Exporta os logs filtrados para um arquivo CSV."""
        try:
            filetypes = [('Arquivos CSV', '*.csv')]
            
            filename = filedialog.asksaveasfilename(
                title="Exportar Logs",
                filetypes=filetypes,
                defaultextension=".csv"
            )
            
            if not filename:
                return
            
            # Obtém os logs da lista atual
            logs = []
            for item in self.lista_logs.get_children():
                valores = self.lista_logs.item(item, 'values')
                logs.append(valores)
            
            # Escreve o arquivo CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeçalho
                writer.writerow(['ID', 'Data/Hora', 'Usuário', 'Ação', 'Descrição'])
                
                # Dados
                for log in logs:
                    writer.writerow(log)
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", f"Logs exportados com sucesso para {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar logs: {e}")
            messagebox.showerror("Erro", f"Falha ao exportar logs: {e}")
    
    def limpar_logs_antigos(self):
        """Limpa logs antigos do sistema."""
        try:
            # Confirmação
            if not messagebox.askyesno(
                "Confirmação", 
                "Deseja realmente limpar logs antigos?\n\n"
                "Esta ação excluirá todos os logs com mais de 90 dias."
            ):
                return
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Exclui logs mais antigos que 90 dias
            cursor.execute('''
            DELETE FROM logs 
            WHERE date(data) < date('now', '-90 days')
            ''')
            
            qtd_removidos = cursor.rowcount
            
            # Registra a ação
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "LIMPEZA_LOGS", 
                f"Removidos {qtd_removidos} logs antigos"
            ))
            
            conn.commit()
            conn.close()
            
            # Atualiza a lista
            self.atualizar_lista_logs()
            
            # Mensagem de sucesso
            messagebox.showinfo("Sucesso", f"Foram removidos {qtd_removidos} logs antigos do sistema.")
            
        except Exception as e:
            logger.error(f"Erro ao limpar logs antigos: {e}")
            messagebox.showerror("Erro", f"Falha ao limpar logs: {e}")
    
    def salvar_configuracoes_sistema(self):
        """Salva as configurações do sistema."""
        try:
            # Configurações gerais
            self.config['prefeitura_padrao'] = 'sj' if self.prefeitura_padrao_var.get() == "São José" else 'floripa'
            
            # Backup
            self.config['backup'] = {
                'automatico': self.backup_automatico_var.get(),
                'intervalo': self.intervalo_backup_var.get().lower(),
                'hora': f"{self.hora_backup_var.get()}:{self.minuto_backup_var.get()}"
            }
            
            # SMTP
            for prefeitura in ['sj', 'floripa']:
                self.config['smtp'][prefeitura] = {
                    'servidor': self.entry_servidor_smtp[prefeitura].get(),
                    'porta': int(self.entry_porta_smtp[prefeitura].get()),
                    'usuario': self.entry_usuario_smtp[prefeitura].get(),
                    'senha': self.entry_senha_smtp[prefeitura].get(),
                    'tls': self.tls_var[prefeitura].get(),
                    'ssl': self.ssl_var[prefeitura].get()
                }
            
            # Assinaturas
            self.config['assinaturas']['sj']['padrao'] = self.text_assinatura_sj.get(1.0, tk.END).strip()
            self.config['assinaturas']['floripa']['padrao'] = self.text_assinatura_floripa.get(1.0, tk.END).strip()
            
            # Salva as configurações
            if self.salvar_configuracoes():
                # Registra no log
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO logs (usuario_id, acao, descricao)
                VALUES (?, ?, ?)
                ''', (
                    self.usuario_atual['id'], "CONFIGURACOES", 
                    "Configurações do sistema atualizadas"
                ))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar configurações: {e}")
    
    def restaurar_configuracoes_padrao(self):
        """Restaura as configurações padrão do sistema."""
        try:
            if not messagebox.askyesno(
                "Confirmação", 
                "Deseja realmente restaurar as configurações padrão?\n\n"
                "Esta ação substituirá todas as configurações atuais."
            ):
                return
            
            # Restaura configurações padrão
            self.config = self.configuracoes_padrao()
            
            # Atualiza a interface
            self.prefeitura_padrao_var.set("São José" if self.config['prefeitura_padrao'] == 'sj' else "Florianópolis")
            
            self.backup_automatico_var.set(self.config['backup']['automatico'])
            self.intervalo_backup_var.set(self.config['backup']['intervalo'].capitalize())
            
            hora, minuto = self.config['backup']['hora'].split(':')
            self.hora_backup_var.set(hora)
            self.minuto_backup_var.set(minuto)
            
            for prefeitura in ['sj', 'floripa']:
                self.entry_servidor_smtp[prefeitura].delete(0, tk.END)
                self.entry_servidor_smtp[prefeitura].insert(0, self.config['smtp'][prefeitura]['servidor'])
                
                self.entry_porta_smtp[prefeitura].delete(0, tk.END)
                self.entry_porta_smtp[prefeitura].insert(0, str(self.config['smtp'][prefeitura]['porta']))
                
                self.entry_usuario_smtp[prefeitura].delete(0, tk.END)
                self.entry_usuario_smtp[prefeitura].insert(0, self.config['smtp'][prefeitura]['usuario'])
                
                self.entry_senha_smtp[prefeitura].delete(0, tk.END)
                self.entry_senha_smtp[prefeitura].insert(0, self.config['smtp'][prefeitura]['senha'])
                
                self.tls_var[prefeitura].set(self.config['smtp'][prefeitura]['tls'])
                self.ssl_var[prefeitura].set(self.config['smtp'][prefeitura]['ssl'])
            
            self.text_assinatura_sj.delete(1.0, tk.END)
            self.text_assinatura_sj.insert(tk.END, self.config['assinaturas']['sj']['padrao'])
            
            self.text_assinatura_floripa.delete(1.0, tk.END)
            self.text_assinatura_floripa.insert(tk.END, self.config['assinaturas']['floripa']['padrao'])
            
            # Salva as configurações
            self.salvar_configuracoes()
            
            # Registra no log
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "CONFIGURACOES", 
                "Configurações padrão restauradas"
            ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", "Configurações padrão restauradas com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao restaurar configurações padrão: {e}")
            messagebox.showerror("Erro", f"Falha ao restaurar configurações: {e}")
    
    def testar_conexao_smtp(self):
        """Testa a conexão com o servidor SMTP configurado."""
        try:
            prefeitura = self.prefeitura_atual
            
            # Obtém as configurações SMTP
            servidor = self.entry_servidor_smtp[prefeitura].get()
            porta = self.entry_porta_smtp[prefeitura].get()
            usuario = self.entry_usuario_smtp[prefeitura].get()
            senha = self.entry_senha_smtp[prefeitura].get()
            usar_tls = self.tls_var[prefeitura].get()
            usar_ssl = self.ssl_var[prefeitura].get()
            
            if not servidor or not porta or not usuario or not senha:
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios de configuração SMTP.")
                return
            
            # Inicia o teste em uma thread separada para não bloquear a interface
            threading.Thread(target=self.realizar_teste_smtp, args=(
                servidor, int(porta), usuario, senha, usar_tls, usar_ssl
            ), daemon=True).start()
            
            # Exibe mensagem de teste em andamento
            messagebox.showinfo("Teste em Andamento", "Teste de conexão SMTP iniciado.\n\nUma mensagem será exibida com o resultado.")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar teste SMTP: {e}")
            messagebox.showerror("Erro", f"Falha ao iniciar teste de conexão: {e}")
    
    def realizar_teste_smtp(self, servidor, porta, usuario, senha, usar_tls, usar_ssl):
        """Realiza o teste de conexão SMTP."""
        try:
            # Conecta ao servidor SMTP
            if usar_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(servidor, porta, context=context)
            else:
                server = smtplib.SMTP(servidor, porta)
                
                if usar_tls:
                    server.starttls()
            
            # Login
            server.login(usuario, senha)
            
            # Fecha a conexão
            server.quit()
            
            # Registra o sucesso
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "TESTE_SMTP", 
                f"Teste de conexão SMTP realizado com sucesso para {servidor}:{porta}"
            ))
            
            conn.commit()
            conn.close()
            
            # Exibe mensagem de sucesso
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Conexão SMTP estabelecida com sucesso!"))
            
        except Exception as e:
            logger.error(f"Erro no teste SMTP: {e}")
            
            # Registra a falha
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "ERRO_TESTE_SMTP", 
                f"Falha no teste de conexão SMTP para {servidor}:{porta}: {e}"
            ))
            
            conn.commit()
            conn.close()
            
            # Exibe mensagem de erro
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na conexão SMTP: {e}"))
    
    def escolher_diretorio_backup(self):
        """Abre o diálogo para escolher o diretório de backup."""
        try:
            diretorio = filedialog.askdirectory(
                title="Selecionar Diretório de Backup",
                initialdir=self.entry_dir_backup.get()
            )
            
            if diretorio:
                self.entry_dir_backup.delete(0, tk.END)
                self.entry_dir_backup.insert(0, diretorio)
        except Exception as e:
            logger.error(f"Erro ao escolher diretório de backup: {e}")
            messagebox.showerror("Erro", f"Falha ao selecionar diretório: {e}")
    
    def fazer_backup_manual(self):
        """Realiza um backup manual do banco de dados e configurações."""
        try:
            # Obtém o diretório de backup
            diretorio_backup = self.entry_dir_backup.get() if hasattr(self, 'entry_dir_backup') else BACKUP_DIR
            
            # Verifica se o diretório existe
            if not os.path.exists(diretorio_backup):
                os.makedirs(diretorio_backup, exist_ok=True)
            
            # Nome do arquivo de backup
            data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"backup_{data_atual}.zip"
            caminho_arquivo = os.path.join(diretorio_backup, nome_arquivo)
            
            # Cria o arquivo ZIP
            with zipfile.ZipFile(caminho_arquivo, 'w') as zip_file:
                # Adiciona o banco de dados
                zip_file.write(DB_FILE, os.path.basename(DB_FILE))
                
                # Adiciona as configurações
                if os.path.exists(CONFIG_FILE):
                    zip_file.write(CONFIG_FILE, os.path.basename(CONFIG_FILE))
                
                # Adiciona os arquivos de template
                if os.path.exists(TEMPLATE_DIR):
                    for root, dirs, files in os.walk(TEMPLATE_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(TEMPLATE_DIR))
                            zip_file.write(file_path, os.path.join("templates", arcname))
                
                # Adiciona as imagens de logo
                if os.path.exists(RESOURCES_DIR):
                    for root, dirs, files in os.walk(RESOURCES_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(RESOURCES_DIR))
                            zip_file.write(file_path, os.path.join("resources", arcname))
            
            # Registra o backup
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (usuario_id, acao, descricao)
            VALUES (?, ?, ?)
            ''', (
                self.usuario_atual['id'], "BACKUP_MANUAL", 
                f"Backup manual realizado: {nome_arquivo}"
            ))
            
            conn.commit()
            conn.close()
            
            # Exibe mensagem de sucesso
            messagebox.showinfo(
                "Backup Concluído", 
                f"Backup realizado com sucesso!\n\n"
                f"Arquivo: {nome_arquivo}\n"
                f"Local: {diretorio_backup}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao realizar backup manual: {e}")
            messagebox.showerror("Erro", f"Falha ao realizar backup: {e}")
    
    def executar_agendador(self):
        """Executa o agendador em uma thread separada."""
        logger.info("Iniciando thread do agendador de tarefas")
        
        try:
            # Configura o agendador
            schedule.every(1).minutes.do(self.verificar_emails_agendados)
            schedule.every(1).days.at("03:00").do(self.limpar_logs_antigos_automatico)
            
            # Verificações de backup
            schedule.every(1).hours.do(self.verificar_backup_automatico)
            
            # Contador de falhas
            falhas_consecutivas = 0
            
            # Loop principal do agendador
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(30)  # Verifica a cada 30 segundos
                    falhas_consecutivas = 0  # Reseta o contador se executou sem erros
                except Exception as e:
                    falhas_consecutivas += 1
                    logger.error(f"Erro no loop do agendador: {e}")
                    
                    # Se houver muitas falhas consecutivas, força uma pausa maior
                    if falhas_consecutivas > 5:
                        logger.warning(f"Muitas falhas consecutivas no agendador. Pausando por 5 minutos.")
                        time.sleep(300)  # Pausa de 5 minutos
                        falhas_consecutivas = 0
                    else:
                        time.sleep(60)  # Pausa de 1 minuto após uma falha
        except Exception as e:
            logger.error(f"Erro fatal na thread do agendador: {e}")
    
    def verificar_emails_agendados(self):
        """Verifica se há e-mails agendados para envio e os processa."""
        logger.debug("Verificando e-mails agendados")
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Obtém a data e hora atual
            data_atual = datetime.datetime.now()
            
            # Busca e-mails agendados pendentes
            cursor.execute('''
            SELECT id, usuario_id, assunto, conteudo, destinatarios, data_agendada, 
                   recorrencia, anexos, recorrencia_opcoes
            FROM emails_agendados 
            WHERE status = 'pendente' AND datetime(data_agendada) <= datetime(?)
            ''', (data_atual.strftime('%Y-%m-%d %H:%M:%S'),))
            
            agendamentos = cursor.fetchall()
            
            for agendamento in agendamentos:
                id_agendamento, usuario_id, assunto, conteudo, destinatarios_json, data_agendada, recorrencia, anexos_json, recorrencia_opcoes_json = agendamento
                
                # Converte os dados JSON
                import json
                destinatarios = json.loads(destinatarios_json)
                anexos = json.loads(anexos_json) if anexos_json else []
                recorrencia_opcoes = json.loads(recorrencia_opcoes_json) if recorrencia_opcoes_json else {}
                
                # Se for um agendamento recorrente, recalcula a próxima data
                if recorrencia and recorrencia != "nenhuma":
                    proxima_data = self.calcular_proxima_data_recorrencia(
                        data_agendada, recorrencia, recorrencia_opcoes
                    )
                    
                    if proxima_data:
                        # Atualiza o agendamento com a próxima data
                        cursor.execute('''
                        UPDATE emails_agendados
                        SET data_agendada = ?
                        WHERE id = ?
                        ''', (proxima_data.strftime('%Y-%m-%d %H:%M:%S'), id_agendamento))
                    else:
                        # Se não houver próxima data, marca como concluído
                        cursor.execute('UPDATE emails_agendados SET status = ? WHERE id = ?', ('concluído', id_agendamento))
                else:
                    # Se não for recorrente, marca como concluído
                    cursor.execute('UPDATE emails_agendados SET status = ? WHERE id = ?', ('concluído', id_agendamento))
                
                # Busca informações do usuário que agendou
                cursor.execute('SELECT email, prefeitura FROM usuarios WHERE id = ?', (usuario_id,))
                usuario = cursor.fetchone()
                
                if not usuario:
                    logger.error(f"Usuário {usuario_id} não encontrado para o agendamento #{id_agendamento}")
                    continue
                
                email_usuario, prefeitura = usuario
                
                # Obtém as configurações SMTP da prefeitura
                smtp_config = self.config.get('smtp', {}).get(prefeitura, {})
                
                servidor = smtp_config.get('servidor')
                porta = smtp_config.get('porta', 587)
                usuario_smtp = smtp_config.get('usuario')
                senha = smtp_config.get('senha')
                usar_tls = smtp_config.get('tls', True)
                usar_ssl = smtp_config.get('ssl', False)
                
                if not servidor or not usuario_smtp or not senha:
                    logger.error(f"Configurações SMTP incompletas para o agendamento #{id_agendamento}")
                    continue
                
                # Envia o e-mail
                try:
                    # Cria a mensagem
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = assunto
                    msg['From'] = usuario_smtp
                    msg['To'] = ', '.join(destinatarios)
                    
                    # Corpo da mensagem em HTML
                    part = MIMEText(conteudo, 'html')
                    msg.attach(part)
                    
                    # Adiciona anexos
                    for anexo_path in anexos:
                        if os.path.exists(anexo_path):
                            with open(anexo_path, 'rb') as f:
                                part = MIMEApplication(f.read(), Name=os.path.basename(anexo_path))
                            
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(anexo_path)}"'
                            msg.attach(part)
                    
                    # Conecta ao servidor SMTP
                    if usar_ssl:
                        context = ssl.create_default_context()
                        server = smtplib.SMTP_SSL(servidor, porta, context=context)
                    else:
                        server = smtplib.SMTP(servidor, porta)
                        
                        if usar_tls:
                            server.starttls()
                    
                    # Login
                    server.login(usuario_smtp, senha)
                    
                    # Envia o e-mail
                    server.send_message(msg)
                    
                    # Fecha a conexão
                    server.quit()
                    
                    # Registra o envio
                    cursor.execute('''
                    INSERT INTO emails_enviados (usuario_id, assunto, conteudo, destinatarios, status)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        usuario_id, assunto, conteudo, 
                        ', '.join(destinatarios), 'enviado (agendado)'
                    ))
                    
                    # Registra no log
                    cursor.execute('''
                    INSERT INTO logs (usuario_id, acao, descricao)
                    VALUES (?, ?, ?)
                    ''', (
                        usuario_id, "ENVIO_AGENDADO", 
                        f"E-mail agendado #{id_agendamento} enviado para {len(destinatarios)} destinatários"
                    ))
                    
                    logger.info(f"E-mail agendado #{id_agendamento} enviado com sucesso")
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar e-mail agendado #{id_agendamento}: {e}")
                    
                    # Registra a falha
                    cursor.execute('''
                    INSERT INTO emails_enviados (usuario_id, assunto, conteudo, destinatarios, status)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        usuario_id, assunto, conteudo, 
                        ', '.join(destinatarios), f'falha (agendado): {e}'
                    ))
                    
                    # Registra no log
                    cursor.execute('''
                    INSERT INTO logs (usuario_id, acao, descricao)
                    VALUES (?, ?, ?)
                    ''', (
                        usuario_id, "ERRO_ENVIO_AGENDADO", 
                        f"Falha ao enviar e-mail agendado #{id_agendamento}: {e}"
                    ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao verificar e-mails agendados: {e}")
    
    def calcular_proxima_data_recorrencia(self, data_agendada, recorrencia, opcoes):
        """Calcula a próxima data para um agendamento recorrente."""
        try:
            # Converte a string de data para datetime
            if isinstance(data_agendada, str):
                data = datetime.datetime.strptime(data_agendada, '%Y-%m-%d %H:%M:%S')
            else:
                data = data_agendada
            
            if recorrencia == "diaria":
                # Adiciona 1 dia
                return data + datetime.timedelta(days=1)
                
            elif recorrencia == "semanal":
                # Adiciona 7 dias
                return data + datetime.timedelta(days=7)
                
            elif recorrencia == "mensal":
                # Adiciona 1 mês (aproximadamente 30 dias)
                dia_mes = int(opcoes.get('dia_mes', data.day))
                
                # Calcula o próximo mês
                proximo_mes = data.month + 1
                proximo_ano = data.year
                
                if proximo_mes > 12:
                    proximo_mes = 1
                    proximo_ano += 1
                
                # Ajusta o dia se necessário (por exemplo, 31 de abril não existe)
                ultimo_dia = calendar.monthrange(proximo_ano, proximo_mes)[1]
                dia_ajustado = min(dia_mes, ultimo_dia)
                
                return datetime.datetime(proximo_ano, proximo_mes, dia_ajustado, data.hour, data.minute)
            
            # Se não for um tipo de recorrência conhecido, retorna None
            return None
            
        except Exception as e:
            logger.error(f"Erro ao calcular próxima data de recorrência: {e}")
            return None
    
    def verificar_backup_automatico(self):
        """Verifica se é hora de realizar o backup automático."""
        try:
            # Verifica se o backup automático está ativado
            if not self.config.get('backup', {}).get('automatico', True):
                return
            
            # Obtém a hora configurada para backup
            hora_backup = self.config.get('backup', {}).get('hora', '23:00')
            hora, minuto = hora_backup.split(':')
            hora_atual = datetime.datetime.now().hour
            minuto_atual = datetime.datetime.now().minute
            
            # Verifica a frequência de backup
            intervalo = self.config.get('backup', {}).get('intervalo', 'diario')
            
            # Para backup diário, verifica se é a hora configurada
            if intervalo == 'diario' and hora_atual == int(hora) and minuto_atual == int(minuto):
                self.realizar_backup_automatico()
                
            # Para backup semanal, verifica se é domingo e a hora configurada
            elif intervalo == 'semanal' and datetime.datetime.now().weekday() == 6 and hora_atual == int(hora) and minuto_atual == int(minuto):
                self.realizar_backup_automatico()
                
            # Para backup mensal, verifica se é o primeiro dia do mês e a hora configurada
            elif intervalo == 'mensal' and datetime.datetime.now().day == 1 and hora_atual == int(hora) and minuto_atual == int(minuto):
                self.realizar_backup_automatico()
                
        except Exception as e:
            logger.error(f"Erro ao verificar backup automático: {e}")
    
    def realizar_backup_automatico(self):
        """Realiza um backup automático do banco de dados e configurações."""
        try:
            logger.info("Iniciando backup automático")
            
            # Obtém o diretório de backup
            diretorio_backup = BACKUP_DIR
            
            # Verifica se o diretório existe
            if not os.path.exists(diretorio_backup):
                os.makedirs(diretorio_backup, exist_ok=True)
            
            # Nome do arquivo de backup
            data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"backup_auto_{data_atual}.zip"
            caminho_arquivo = os.path.join(diretorio_backup, nome_arquivo)
            
            # Cria o arquivo ZIP
            with zipfile.ZipFile(caminho_arquivo, 'w') as zip_file:
                # Adiciona o banco de dados
                zip_file.write(DB_FILE, os.path.basename(DB_FILE))
                
                # Adiciona as configurações
                if os.path.exists(CONFIG_FILE):
                    zip_file.write(CONFIG_FILE, os.path.basename(CONFIG_FILE))
                
                # Adiciona os arquivos de template
                if os.path.exists(TEMPLATE_DIR):
                    for root, dirs, files in os.walk(TEMPLATE_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(TEMPLATE_DIR))
                            zip_file.write(file_path, os.path.join("templates", arcname))
                
                # Adiciona as imagens de logo
                if os.path.exists(RESOURCES_DIR):
                    for root, dirs, files in os.walk(RESOURCES_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(RESOURCES_DIR))
                            zip_file.write(file_path, os.path.join("resources", arcname))
            
            # Registra o backup automático
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (acao, descricao)
            VALUES (?, ?)
            ''', (
                "BACKUP_AUTOMATICO", 
                f"Backup automático realizado: {nome_arquivo}"
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Backup automático concluído: {nome_arquivo}")
            
            # Limpa backups antigos
            self.limpar_backups_antigos()
            
        except Exception as e:
            logger.error(f"Erro ao realizar backup automático: {e}")
    
    def limpar_backups_antigos(self):
        """Remove backups automáticos antigos para economizar espaço."""
        try:
            # Obtém o diretório de backup
            diretorio_backup = BACKUP_DIR
            
            if not os.path.exists(diretorio_backup):
                return
            
            # Lista todos os arquivos de backup automático
            arquivos_backup = [f for f in os.listdir(diretorio_backup) if f.startswith("backup_auto_") and f.endswith(".zip")]
            
            # Ordena por data (mais recentes primeiro)
            arquivos_backup.sort(reverse=True)
            
            # Mantém apenas os 10 backups mais recentes
            if len(arquivos_backup) > 10:
                for arquivo in arquivos_backup[10:]:
                    os.remove(os.path.join(diretorio_backup, arquivo))
                    logger.info(f"Backup antigo removido: {arquivo}")
                
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {e}")
    
    def limpar_logs_antigos_automatico(self):
        """Limpa logs antigos do sistema automaticamente."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Exclui logs mais antigos que 90 dias
            cursor.execute('''
            DELETE FROM logs 
            WHERE date(data) < date('now', '-90 days')
            ''')
            
            qtd_removidos = cursor.rowcount
            
            # Registra a ação
            if qtd_removidos > 0:
                cursor.execute('''
                INSERT INTO logs (acao, descricao)
                VALUES (?, ?)
                ''', (
                    "LIMPEZA_LOGS_AUTOMATICA", 
                    f"Removidos {qtd_removidos} logs antigos automaticamente"
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Limpeza automática de logs: {qtd_removidos} registros removidos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar logs antigos automaticamente: {e}")


def main():
    """Função principal para iniciar o aplicativo."""
    root = tk.Tk()
    app = SistemaEmail(root)
    root.mainloop()


if __name__ == "__main__":
    main()
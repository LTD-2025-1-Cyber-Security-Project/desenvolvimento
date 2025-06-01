import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3
from datetime import datetime
import os
import re
import hashlib
from tkinter import simpledialog
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, grey
from PIL import Image, ImageTk
import webbrowser
import io
import sys

class SistemaGeradorDeOficios:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Gerador de Ofícios - Prefeituras de Florianópolis e São José")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        # Definições de cores e estilos
        self.cor_primaria = "#1A5276"  # Azul escuro
        self.cor_secundaria = "#2E86C1"  # Azul médio
        self.cor_destaque = "#3498DB"  # Azul claro
        self.cor_bg = "#F5F5F5"  # Cinza claro
        self.cor_texto = "#333333"  # Quase preto
        
        self.fonte_titulo = ("Calibri", 14, "bold")
        self.fonte_texto = ("Calibri", 11)
        self.fonte_rotulo = ("Calibri", 11, "bold")
        
        # Configurar diretório de dados
        self.configurar_diretorio_dados()
        
        # Configuração do banco de dados
        self.inicializar_banco_dados()
        
        # Estado da aplicação
        self.id_usuario_atual = None
        self.nome_usuario_atual = None
        self.perfil_usuario_atual = None
        self.municipio_usuario_atual = None
        self.id_oficio_atual = None
        
        # Carregar tela de login
        self.mostrar_tela_login()

    def configurar_diretorio_dados(self):
        """
        Configura o diretório onde os dados do sistema serão armazenados.
        Tenta diferentes localizações dependendo do sistema operacional e contexto de execução.
        """
        try:
            # Se executando como executável PyInstaller
            if getattr(sys, 'frozen', False):
                # Executável PyInstaller
                if hasattr(sys, '_MEIPASS'):
                    # Diretório temporário do PyInstaller
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                # Executando como script Python
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Tentar criar diretório de dados no mesmo local do executável
            self.diretorio_dados = os.path.join(base_dir, "dados_sistema")
            
            # Se não conseguir escrever no diretório do executável, usar diretório do usuário
            if not self.verificar_permissao_escrita(base_dir):
                # Usar diretório do usuário como fallback
                import tempfile
                user_data_dir = os.path.expanduser("~")
                
                # Criar diretório específico para o sistema
                self.diretorio_dados = os.path.join(user_data_dir, "SistemaGeradorOficios", "dados")
            
            # Criar diretório se não existir
            os.makedirs(self.diretorio_dados, exist_ok=True)
            
            # Definir caminho do banco de dados
            self.caminho_banco = os.path.join(self.diretorio_dados, "oficios_sistema.db")
            
            print(f"Diretório de dados configurado: {self.diretorio_dados}")
            print(f"Caminho do banco de dados: {self.caminho_banco}")
            
        except Exception as e:
            # Em caso de erro, usar diretório temporário
            import tempfile
            self.diretorio_dados = tempfile.gettempdir()
            self.caminho_banco = os.path.join(self.diretorio_dados, "oficios_sistema.db")
            print(f"Usando diretório temporário: {self.diretorio_dados}")
            print(f"Erro na configuração: {str(e)}")

    def verificar_permissao_escrita(self, diretorio):
        """
        Verifica se o diretório tem permissão de escrita.
        """
        try:
            # Tentar criar um arquivo temporário
            arquivo_teste = os.path.join(diretorio, "teste_permissao.tmp")
            with open(arquivo_teste, 'w') as f:
                f.write("teste")
            os.remove(arquivo_teste)
            return True
        except:
            return False

    def obter_conexao_banco(self):
        """
        Obtém uma conexão com o banco de dados SQLite de forma segura.
        """
        try:
            # Criar o diretório pai se não existir
            os.makedirs(os.path.dirname(self.caminho_banco), exist_ok=True)
            
            # Conectar ao banco de dados
            conn = sqlite3.connect(self.caminho_banco, timeout=30.0)
            
            # Configurar WAL mode para melhor concorrência
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA temp_store=MEMORY;')
            conn.execute('PRAGMA mmap_size=268435456;')  # 256MB
            
            return conn
        except Exception as e:
            print(f"Erro ao conectar com o banco de dados: {str(e)}")
            messagebox.showerror("Erro de Banco de Dados", 
                               f"Não foi possível conectar com o banco de dados.\n\n"
                               f"Erro: {str(e)}\n\n"
                               f"Caminho: {self.caminho_banco}")
            raise

    def atualizar_estrutura_banco_dados(self):
        """
        Atualiza a estrutura do banco de dados para incluir as novas colunas no modelo de ofício.
        Esta função deve ser chamada em inicializar_banco_dados() após a criação das tabelas.
        """
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Verificar quais colunas existem na tabela de ofícios
            cursor.execute("PRAGMA table_info(oficios)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            
            # Lista de novas colunas a serem adicionadas se não existirem
            novas_colunas = {
                "protocolo": "TEXT",
                "cumprimentos": "TEXT",
                "despedida": "TEXT",
                "remetente": "TEXT",
                "cargo_remetente": "TEXT",
                "tem_logotipo": "INTEGER DEFAULT 0",
                "caminho_logotipo": "TEXT",
                "tem_assinatura": "INTEGER DEFAULT 0",
                "caminho_assinatura": "TEXT"
            }
            
            # Adicionar cada coluna que não existe
            for coluna, tipo in novas_colunas.items():
                if coluna not in colunas_existentes:
                    try:
                        cursor.execute(f"ALTER TABLE oficios ADD COLUMN {coluna} {tipo}")
                        print(f"Coluna '{coluna}' adicionada com sucesso.")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna '{coluna}': {str(e)}")
            
            conn.commit()
            print("Estrutura do banco de dados atualizada com sucesso.")
            
        except Exception as e:
            print(f"Erro ao atualizar estrutura do banco de dados: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def inicializar_banco_dados(self):
        """
        Inicializa o banco de dados do sistema, criando as tabelas necessárias
        e um usuário administrador padrão, se não existirem.
        """
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Tabela de Usuários
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                municipio TEXT NOT NULL,
                departamento TEXT,
                cargo TEXT,
                perfil TEXT NOT NULL,
                data_cadastro TEXT NOT NULL,
                ultimo_acesso TEXT
            )
            ''')
            
            # Tabela de Oficios com todas as colunas necessárias
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS oficios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL,
                protocolo TEXT,
                assunto TEXT NOT NULL,
                destinatario TEXT NOT NULL,
                cargo_destinatario TEXT,
                orgao_destinatario TEXT,
                conteudo TEXT NOT NULL,
                cumprimentos TEXT,
                despedida TEXT,
                remetente TEXT,
                cargo_remetente TEXT,
                tem_logotipo INTEGER DEFAULT 0,
                caminho_logotipo TEXT,
                tem_assinatura INTEGER DEFAULT 0,
                caminho_assinatura TEXT,
                data_criacao TEXT NOT NULL,
                data_modificacao TEXT,
                status TEXT NOT NULL,
                usuario_id INTEGER NOT NULL,
                caminho_arquivo TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')
            
            # Verificar se já existe um administrador, se não, criar um
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'admin'")
            if cursor.fetchone()[0] == 0:
                # Criar administrador padrão
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                senha_hash = self.hash_senha("admin123")
                
                cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, municipio, departamento, cargo, perfil, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("Administrador", "admin@sistema.gov.br", senha_hash, "Ambos", 
                    "TI", "Administrador do Sistema", "admin", agora))
                
                # Criar um usuário de Florianópolis para teste
                senha_hash = self.hash_senha("floripa123")
                cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, municipio, departamento, cargo, perfil, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("Usuário Florianópolis", "usuario@floripa.sc.gov.br", senha_hash, "Florianópolis", 
                    "Administração", "Assistente Administrativo", "usuario", agora))
                
                # Criar um usuário de São José para teste
                senha_hash = self.hash_senha("saojose123")
                cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, municipio, departamento, cargo, perfil, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("Usuário São José", "usuario@saojose.sc.gov.br", senha_hash, "São José", 
                    "Recursos Humanos", "Analista", "usuario", agora))
                
                print("Usuários padrão criados com sucesso.")
            
            # Verificar se é necessário atualizar a estrutura de tabelas existentes
            self.atualizar_estrutura_banco_dados()
            
            conn.commit()
            print("Banco de dados inicializado com sucesso.")
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            messagebox.showerror("Erro de Inicialização", 
                               f"Não foi possível inicializar o banco de dados.\n\n"
                               f"Erro: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def hash_senha(self, senha):
        # Criar hash da senha usando SHA-256
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def verificar_senha(self, senha_digitada, senha_hash):
        # Verificar se a senha digitada corresponde ao hash armazenado
        return self.hash_senha(senha_digitada) == senha_hash
    
    # ================ FUNÇÕES DE AUTENTICAÇÃO E USUÁRIOS ================
    
    def mostrar_tela_login(self):
        # Limpar a tela atual
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configurar a janela para o login
        self.root.configure(background=self.cor_bg)
        
        frame_login = tk.Frame(self.root, bg=self.cor_bg, padx=20, pady=20)
        frame_login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Logo ou título
        titulo = tk.Label(frame_login, text="SISTEMA GERADOR DE OFÍCIOS", 
                          font=("Calibri", 24, "bold"), bg=self.cor_bg, fg=self.cor_primaria)
        titulo.grid(row=0, column=0, columnspan=2, pady=20)
        
        subtitulo = tk.Label(frame_login, text="Prefeituras de Florianópolis e São José", 
                          font=("Calibri", 16), bg=self.cor_bg, fg=self.cor_secundaria)
        subtitulo.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Formulário de login
        frame_formulario = tk.Frame(frame_login, bg=self.cor_bg, padx=30, pady=30,
                                   highlightbackground=self.cor_secundaria, highlightthickness=1)
        frame_formulario.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Email
        tk.Label(frame_formulario, text="Email:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.email_var = tk.StringVar()
        email_entry = tk.Entry(frame_formulario, textvariable=self.email_var, 
                              font=self.fonte_texto, width=30)
        email_entry.grid(row=0, column=1, pady=(0, 5), padx=10)
        email_entry.focus()
        
        # Senha
        tk.Label(frame_formulario, text="Senha:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        self.senha_var = tk.StringVar()
        senha_entry = tk.Entry(frame_formulario, textvariable=self.senha_var, 
                              font=self.fonte_texto, width=30, show="•")
        senha_entry.grid(row=1, column=1, pady=(10, 5), padx=10)
        senha_entry.bind("<Return>", lambda event: self.fazer_login())
        
        # Botão de Login
        btn_login = tk.Button(frame_formulario, text="Entrar", font=self.fonte_texto,
                             bg="light gray", fg=self.cor_texto, padx=20, pady=5,
                             command=self.fazer_login, cursor="hand2")
        btn_login.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Link para registrar
        link_registrar = tk.Label(frame_login, text="Não tem conta? Registre-se aqui",
                                 font=("Calibri", 10, "underline"), bg=self.cor_bg,
                                 fg=self.cor_secundaria, cursor="hand2")
        link_registrar.grid(row=3, column=0, columnspan=2, pady=5)
        link_registrar.bind("<Button-1>", lambda e: self.mostrar_tela_registro())
        
        # Informações sobre o banco de dados
        info_bd = tk.Label(frame_login, text=f"BD: {os.path.basename(self.caminho_banco)}", 
                         font=("Calibri", 8), bg=self.cor_bg, fg="gray")
        info_bd.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Rodapé com informações do sistema
        rodape = tk.Label(frame_login, text="© 2025 - Sistema Gerador de Ofícios v1.0", 
                         font=("Calibri", 9), bg=self.cor_bg, fg="gray")
        rodape.grid(row=5, column=0, columnspan=2, pady=20)
    
    def fazer_login(self):
        email = self.email_var.get().strip()
        senha = self.senha_var.get()
        
        if not email or not senha:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Buscar usuário pelo email
            cursor.execute("SELECT id, nome, senha, perfil, municipio FROM usuarios WHERE email = ?", (email,))
            resultado = cursor.fetchone()
            
            if resultado and self.verificar_senha(senha, resultado[2]):
                # Login bem-sucedido
                self.id_usuario_atual = resultado[0]
                self.nome_usuario_atual = resultado[1]
                self.perfil_usuario_atual = resultado[3]
                self.municipio_usuario_atual = resultado[4]
                
                # Atualizar último acesso
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE usuarios SET ultimo_acesso = ? WHERE id = ?", 
                              (agora, self.id_usuario_atual))
                conn.commit()
                
                # Redirecionar para o dashboard
                self.mostrar_dashboard()
            else:
                messagebox.showerror("Erro", "Email ou senha incorretos.")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fazer login: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def mostrar_tela_registro(self):
        # Limpar a tela atual
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configurar a janela
        self.root.configure(background=self.cor_bg)
        
        frame_registro = tk.Frame(self.root, bg=self.cor_bg, padx=20, pady=10)
        frame_registro.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Título
        titulo = tk.Label(frame_registro, text="REGISTRO DE NOVO USUÁRIO", 
                         font=("Calibri", 20, "bold"), bg=self.cor_bg, fg=self.cor_primaria)
        titulo.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Formulário de registro
        frame_formulario = tk.Frame(frame_registro, bg=self.cor_bg, padx=20, pady=20,
                                   highlightbackground=self.cor_secundaria, highlightthickness=1)
        frame_formulario.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Nome completo
        tk.Label(frame_formulario, text="Nome completo:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.reg_nome_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_nome_var, 
                font=self.fonte_texto, width=30).grid(row=0, column=1, pady=5, padx=10)
        
        # Email
        tk.Label(frame_formulario, text="Email institucional:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.reg_email_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_email_var, 
                font=self.fonte_texto, width=30).grid(row=1, column=1, pady=5, padx=10)
        
        # Município
        tk.Label(frame_formulario, text="Município:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.reg_municipio_var = tk.StringVar()
        municipio_combo = ttk.Combobox(frame_formulario, textvariable=self.reg_municipio_var, 
                                     font=self.fonte_texto, width=28, state="readonly")
        municipio_combo['values'] = ('Florianópolis', 'São José')
        municipio_combo.grid(row=2, column=1, pady=5, padx=10)
        municipio_combo.current(0)
        
        # Departamento
        tk.Label(frame_formulario, text="Departamento:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.reg_departamento_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_departamento_var, 
                font=self.fonte_texto, width=30).grid(row=3, column=1, pady=5, padx=10)
        
        # Cargo
        tk.Label(frame_formulario, text="Cargo:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.reg_cargo_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_cargo_var, 
                font=self.fonte_texto, width=30).grid(row=4, column=1, pady=5, padx=10)
        
        # Senha
        tk.Label(frame_formulario, text="Senha:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=5, column=0, sticky=tk.W, pady=5)
        self.reg_senha_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_senha_var, 
                font=self.fonte_texto, width=30, show="•").grid(row=5, column=1, pady=5, padx=10)
        
        # Confirmar senha
        tk.Label(frame_formulario, text="Confirmar senha:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=6, column=0, sticky=tk.W, pady=5)
        self.reg_conf_senha_var = tk.StringVar()
        tk.Entry(frame_formulario, textvariable=self.reg_conf_senha_var, 
                font=self.fonte_texto, width=30, show="•").grid(row=6, column=1, pady=5, padx=10)
        
        # Botões
        frame_botoes = tk.Frame(frame_formulario, bg=self.cor_bg)
        frame_botoes.grid(row=7, column=0, columnspan=2, pady=15)
        
        btn_voltar = tk.Button(frame_botoes, text="Voltar", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=self.mostrar_tela_login, cursor="hand2")
        btn_voltar.grid(row=0, column=0, padx=10)
        
        btn_registrar = tk.Button(frame_botoes, text="Registrar", font=self.fonte_texto,
                                 bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                                 command=self.registrar_usuario, cursor="hand2")
        btn_registrar.grid(row=0, column=1, padx=10)
        
        # Informação
        info = tk.Label(frame_registro, text="Nota: O registro está sujeito à aprovação pelo administrador", 
                       font=("Calibri", 9, "italic"), bg=self.cor_bg, fg="gray")
        info.grid(row=2, column=0, columnspan=2, pady=10)
    
    def registrar_usuario(self):
        # Obter dados do formulário
        nome = self.reg_nome_var.get().strip()
        email = self.reg_email_var.get().strip()
        municipio = self.reg_municipio_var.get()
        departamento = self.reg_departamento_var.get().strip()
        cargo = self.reg_cargo_var.get().strip()
        senha = self.reg_senha_var.get()
        conf_senha = self.reg_conf_senha_var.get()
        
        # Validar campos obrigatórios
        if not nome or not email or not municipio or not senha:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos obrigatórios.")
            return
        
        # Validar email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Erro", "Por favor, insira um email válido.")
            return
        
        # Validar email institucional (deve terminar com .gov.br)
        if not email.lower().endswith('.gov.br'):
            messagebox.showerror("Erro", "Por favor, use um email institucional (.gov.br).")
            return
        
        # Validar senhas
        if senha != conf_senha:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
            
        if len(senha) < 6:
            messagebox.showerror("Erro", "A senha deve ter pelo menos 6 caracteres.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Verificar se o email já existe
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro", "Este email já está registrado.")
                return
            
            # Inserir novo usuário
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            senha_hash = self.hash_senha(senha)
            
            cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, municipio, departamento, cargo, perfil, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, senha_hash, municipio, departamento, cargo, "usuario", agora))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Registro realizado com sucesso! Você já pode fazer login.")
            self.mostrar_tela_login()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar usuário: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    # ================ DASHBOARD E NAVEGAÇÃO PRINCIPAL ================
    
    def mostrar_dashboard(self):
        # Limpar a tela atual
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configurar a janela
        self.root.configure(background="#F5F5F5")
        
        # Criar frames principais
        self.frame_topo = tk.Frame(self.root, bg=self.cor_primaria, height=60)
        self.frame_topo.pack(fill=tk.X)
        
        self.frame_menu = tk.Frame(self.root, bg=self.cor_secundaria, width=200)
        self.frame_menu.pack(side=tk.LEFT, fill=tk.Y)
        
        self.frame_conteudo = tk.Frame(self.root, bg="white")
        self.frame_conteudo.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Barra superior
        titulo_sistema = tk.Label(self.frame_topo, text="SISTEMA GERADOR DE OFÍCIOS", 
                                 font=("Calibri", 16, "bold"), bg=self.cor_primaria, fg="white")
        titulo_sistema.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Informações do usuário
        info_usuario = tk.Label(self.frame_topo, 
                              text=f"Usuário: {self.nome_usuario_atual} | {self.municipio_usuario_atual}",
                              font=("Calibri", 11), bg=self.cor_primaria, fg="white")
        info_usuario.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Menu lateral
        tk.Label(self.frame_menu, text="MENU", font=("Calibri", 14, "bold"), 
                bg=self.cor_secundaria, fg="white").pack(pady=(20, 10))
        
        # Botões do menu com cores atualizadas
        self.criar_botao_menu("Início", self.mostrar_tela_inicio)
        self.criar_botao_menu("Novo Ofício", self.mostrar_tela_novo_oficio)
        self.criar_botao_menu("Meus Ofícios", self.mostrar_tela_meus_oficios)
        
        # Adicionar opções administrativas se for administrador
        if self.perfil_usuario_atual == "admin":
            tk.Frame(self.frame_menu, height=2, bg="white").pack(fill=tk.X, padx=10, pady=10)
            tk.Label(self.frame_menu, text="ADMINISTRAÇÃO", font=("Calibri", 12, "bold"), 
                    bg=self.cor_secundaria, fg="white").pack(pady=(5, 10))
            self.criar_botao_menu("Gerenciar Usuários", self.mostrar_tela_gerenciar_usuarios)
        
        tk.Frame(self.frame_menu, height=2, bg="white").pack(fill=tk.X, padx=10, pady=10)
        self.criar_botao_menu("Meu Perfil", self.mostrar_tela_perfil)
        self.criar_botao_menu("Sair", self.fazer_logout)
        
        # Mostrar a tela inicial por padrão
        self.mostrar_tela_inicio()
    
    def criar_botao_menu(self, texto, comando):
        """
        Cria um botão padronizado para o menu lateral com efeito hover.
        
        Args:
            texto (str): Texto a ser exibido no botão
            comando (function): Função a ser chamada quando o botão for clicado
        
        Returns:
            tk.Button: O botão criado
        """
        # Criar o botão com cores padrão
        btn = tk.Button(self.frame_menu, text=texto, font=self.fonte_texto,
                    bg="light gray", fg=self.cor_texto, bd=0, padx=10, pady=8,
                    activebackground=self.cor_destaque, activeforeground="white",
                    anchor="w", width=20, cursor="hand2", command=comando)
        
        # Adicionar efeitos de hover (passar o mouse sobre o botão)
        def on_enter(e):
            # Quando o mouse entra no botão, destacar com uma cor mais escura
            btn['bg'] = '#CCCCCC'  # Cinza um pouco mais escuro
            
        def on_leave(e):
            # Quando o mouse sai do botão, voltar à cor original
            btn['bg'] = 'light gray'
        
        # Vincular eventos de mouse aos handlers
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        btn.pack(fill=tk.X, padx=0, pady=1)
        return btn
    
    def limpar_frame_conteudo(self):
        # Limpar o frame de conteúdo para exibir nova tela
        for widget in self.frame_conteudo.winfo_children():
            widget.destroy()
    
    def fazer_logout(self):
        # Resetar variáveis de sessão
        self.id_usuario_atual = None
        self.nome_usuario_atual = None
        self.perfil_usuario_atual = None
        self.municipio_usuario_atual = None
        
        # Voltar para a tela de login
        self.mostrar_tela_login()
    
    # ================ TELAS PRINCIPAIS ================
    
    def mostrar_tela_inicio(self):
        self.limpar_frame_conteudo()
        
        # Frame de boas-vindas
        frame_bv = tk.Frame(self.frame_conteudo, bg="white", padx=30, pady=30)
        frame_bv.pack(fill=tk.BOTH, expand=True)
        
        # Título de boas-vindas
        titulo = tk.Label(frame_bv, text=f"Bem-vindo(a), {self.nome_usuario_atual}!",
                         font=("Calibri", 24, "bold"), bg="white", fg=self.cor_primaria)
        titulo.pack(pady=(20, 30))
        
        # Data atual
        data_atual = datetime.now().strftime("%d/%m/%Y - %H:%M")
        data_label = tk.Label(frame_bv, text=f"Data: {data_atual}", 
                             font=("Calibri", 14), bg="white", fg=self.cor_texto)
        data_label.pack(pady=(0, 30))
        
        # Cards com estatísticas e ações rápidas
        frame_cards = tk.Frame(frame_bv, bg="white")
        frame_cards.pack(fill=tk.X, pady=20)
        
        # Obter estatísticas do banco de dados
        total_oficios = self.contar_oficios_usuario()
        oficios_pendentes = self.contar_oficios_usuario(status="Pendente")
        oficios_finalizados = self.contar_oficios_usuario(status="Finalizado")
        
        # Card 1 - Total de ofícios
        self.criar_card(frame_cards, "Total de Ofícios", str(total_oficios), 0)
        
        # Card 2 - Ofícios pendentes
        self.criar_card(frame_cards, "Ofícios Pendentes", str(oficios_pendentes), 1)
        
        # Card 3 - Ofícios finalizados
        self.criar_card(frame_cards, "Ofícios Finalizados", str(oficios_finalizados), 2)
        
        # Frame de ações rápidas
        frame_acoes = tk.Frame(frame_bv, bg="white", pady=30)
        frame_acoes.pack(fill=tk.X)
        
        tk.Label(frame_acoes, text="Ações Rápidas:", font=("Calibri", 16, "bold"), 
                bg="white", fg=self.cor_primaria).pack(anchor=tk.W, pady=(0, 15))
        
        # Botões de ações rápidas
        frame_botoes = tk.Frame(frame_acoes, bg="white")
        frame_botoes.pack(fill=tk.X)
        
        btn_novo = tk.Button(frame_botoes, text="Criar Novo Ofício", 
                            font=self.fonte_texto, bg="light gray", fg=self.cor_texto,
                            padx=15, pady=8, cursor="hand2", command=self.mostrar_tela_novo_oficio)
        btn_novo.grid(row=0, column=0, padx=10)
        
        btn_listar = tk.Button(frame_botoes, text="Ver Meus Ofícios", 
                              font=self.fonte_texto, bg="light gray", fg=self.cor_texto,
                              padx=15, pady=8, cursor="hand2", command=self.mostrar_tela_meus_oficios)
        btn_listar.grid(row=0, column=1, padx=10)
        
        btn_perfil = tk.Button(frame_botoes, text="Editar Meu Perfil", 
                              font=self.fonte_texto, bg="WHITE", fg=self.cor_texto,
                              padx=15, pady=8, cursor="hand2", command=self.mostrar_tela_perfil)
        btn_perfil.grid(row=0, column=2, padx=10)
        
        # Informações do sistema
        info_sistema = tk.Label(frame_bv, text=f"Banco de dados: {os.path.basename(self.caminho_banco)}", 
                               font=("Calibri", 9), bg="white", fg="gray")
        info_sistema.pack(side=tk.BOTTOM, pady=(5, 0))
        
        # Rodapé com informações do sistema
        rodape = tk.Label(frame_bv, text="© 2025 - Sistema Gerador de Ofícios v1.0", 
                         font=("Calibri", 9), bg="white", fg="gray")
        rodape.pack(side=tk.BOTTOM, pady=20)
    
    def criar_card(self, frame_pai, titulo, valor, coluna):
        card = tk.Frame(frame_pai, bg="white", padx=15, pady=15, 
                       highlightbackground=self.cor_destaque, highlightthickness=1)
        card.grid(row=0, column=coluna, padx=15, sticky=tk.W+tk.E)
        
        # Título do card
        tk.Label(card, text=titulo, font=("Calibri", 14), 
                bg="white", fg=self.cor_primaria).pack(pady=(0, 10))
        
        # Valor do card
        tk.Label(card, text=valor, font=("Calibri", 24, "bold"), 
                bg="white", fg=self.cor_secundaria).pack()
        
        return card
    
    def contar_oficios_usuario(self, status=None):
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                SELECT COUNT(*) FROM oficios 
                WHERE usuario_id = ? AND status = ?
                """, (self.id_usuario_atual, status))
            else:
                cursor.execute("""
                SELECT COUNT(*) FROM oficios 
                WHERE usuario_id = ?
                """, (self.id_usuario_atual,))
                
            resultado = cursor.fetchone()[0]
            return resultado
        except Exception as e:
            print(f"Erro ao contar ofícios: {str(e)}")
            return 0
        finally:
            if 'conn' in locals():
                conn.close()
    
    # ================ TELA DE NOVO OFÍCIO ================
    
    def mostrar_tela_novo_oficio(self, oficio_id=None):
        """
        Exibe a tela de criação ou edição de ofícios.
        
        Args:
            oficio_id (int, optional): ID do ofício a ser editado. Se None, cria um novo ofício.
        """
        self.limpar_frame_conteudo()
        self.id_oficio_atual = oficio_id
        
        # Frame principal
        frame_oficio = tk.Frame(self.frame_conteudo, bg="white", padx=30, pady=20)
        frame_oficio.pack(fill=tk.BOTH, expand=True)
        
        # Título da página
        if oficio_id:
            titulo_texto = "Editar Ofício"
            # Carregar dados do ofício
            dados_oficio = self.obter_dados_oficio(oficio_id)
        else:
            titulo_texto = "Novo Ofício"
            dados_oficio = None
        
        titulo = tk.Label(frame_oficio, text=titulo_texto, 
                        font=("Calibri", 20, "bold"), bg="WHITE", fg=self.cor_texto)
        titulo.pack(anchor=tk.W, pady=(0, 20))
        
        # Criar frame de rolagem para acomodar todos os campos
        canvas = tk.Canvas(frame_oficio, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_oficio, orient="vertical", command=canvas.yview)
        frame_rolagem = tk.Frame(canvas, bg="white")
        
        frame_rolagem.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_rolagem, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame do formulário dentro do frame de rolagem
        frame_form = tk.Frame(frame_rolagem, bg="white")
        frame_form.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # === PRIMEIRA SEÇÃO: DADOS BÁSICOS DO OFÍCIO ===
        
        # Primeira linha - Número, Protocolo e Assunto
        frame_linha1 = tk.Frame(frame_form, bg="white")
        frame_linha1.pack(fill=tk.X, pady=10)
        
        # Número do ofício
        tk.Label(frame_linha1, text="Número do Ofício:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W)
        
        self.num_oficio_var = tk.StringVar()
        if dados_oficio and dados_oficio['numero']:
            self.num_oficio_var.set(dados_oficio['numero'])
        else:
            # Gerar automaticamente o próximo número
            self.num_oficio_var.set(self.gerar_proximo_numero_oficio())
            
        num_entry = tk.Entry(frame_linha1, textvariable=self.num_oficio_var, 
                        font=self.fonte_texto, width=15)
        num_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W)
        
        # Protocolo (OE)
        tk.Label(frame_linha1, text="Protocolo (OE):", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=2, sticky=tk.W)
        
        self.protocolo_var = tk.StringVar()
        if dados_oficio and dados_oficio.get('protocolo'):
            self.protocolo_var.set(dados_oficio['protocolo'])
            
        protocolo_entry = tk.Entry(frame_linha1, textvariable=self.protocolo_var, 
                                font=self.fonte_texto, width=15)
        protocolo_entry.grid(row=0, column=3, padx=(5, 0), sticky=tk.W)
        
        # Assunto (Segunda linha)
        frame_linha_assunto = tk.Frame(frame_form, bg="white")
        frame_linha_assunto.pack(fill=tk.X, pady=10)
        
        tk.Label(frame_linha_assunto, text="Assunto:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).pack(side=tk.LEFT, padx=(0, 5))
        
        self.assunto_var = tk.StringVar()
        if dados_oficio and dados_oficio['assunto']:
            self.assunto_var.set(dados_oficio['assunto'])
            
        assunto_entry = tk.Entry(frame_linha_assunto, textvariable=self.assunto_var, 
                            font=self.fonte_texto, width=70)
        assunto_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        # === SEGUNDA SEÇÃO: DESTINATÁRIO ===
        frame_destinatario = tk.LabelFrame(frame_form, text="Destinatário", 
                                        font=self.fonte_rotulo, bg="white", fg=self.cor_primaria, 
                                        padx=10, pady=10)
        frame_destinatario.pack(fill=tk.X, pady=15)
        
        # Nome do destinatário
        tk.Label(frame_destinatario, text="Nome:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.destinatario_var = tk.StringVar()
        if dados_oficio and dados_oficio['destinatario']:
            self.destinatario_var.set(dados_oficio['destinatario'])
            
        dest_entry = tk.Entry(frame_destinatario, textvariable=self.destinatario_var, 
                            font=self.fonte_texto, width=40)
        dest_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W+tk.E)
        
        # Cargo do destinatário
        tk.Label(frame_destinatario, text="Cargo:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.cargo_dest_var = tk.StringVar()
        if dados_oficio and dados_oficio['cargo_destinatario']:
            self.cargo_dest_var.set(dados_oficio['cargo_destinatario'])
            
        cargo_entry = tk.Entry(frame_destinatario, textvariable=self.cargo_dest_var, 
                            font=self.fonte_texto, width=40)
        cargo_entry.grid(row=1, column=1, padx=(5, 20), sticky=tk.W+tk.E)
        
        # Órgão/Instituição
        tk.Label(frame_destinatario, text="Órgão/Instituição:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.orgao_var = tk.StringVar()
        if dados_oficio and dados_oficio['orgao_destinatario']:
            self.orgao_var.set(dados_oficio['orgao_destinatario'])
            
        orgao_entry = tk.Entry(frame_destinatario, textvariable=self.orgao_var, 
                            font=self.fonte_texto, width=40)
        orgao_entry.grid(row=2, column=1, padx=(5, 20), sticky=tk.W+tk.E)
        
        # === TERCEIRA SEÇÃO: CONTEÚDO DO OFÍCIO ===
        frame_conteudo_section = tk.LabelFrame(frame_form, text="Conteúdo do Ofício", 
                                            font=self.fonte_rotulo, bg="white", 
                                            fg=self.cor_primaria, padx=10, pady=10)
        frame_conteudo_section.pack(fill=tk.X, pady=15)
        
        # Cumprimentos
        tk.Label(frame_conteudo_section, text="Cumprimentos:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.cumprimentos_var = tk.StringVar()
        if dados_oficio and dados_oficio.get('cumprimentos'):
            self.cumprimentos_var.set(dados_oficio['cumprimentos'])
        else:
            self.cumprimentos_var.set("Prezado(a) Senhor(a),")
            
        cumprimentos_entry = tk.Entry(frame_conteudo_section, textvariable=self.cumprimentos_var, 
                                font=self.fonte_texto, width=60)
        cumprimentos_entry.grid(row=0, column=1, padx=(5, 0), sticky=tk.W+tk.E)
        
        # Área de texto para o conteúdo
        tk.Label(frame_conteudo_section, text="Texto do Ofício:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        frame_texto = tk.Frame(frame_conteudo_section, bg="white")
        frame_texto.grid(row=1, column=1, sticky=tk.W+tk.E)
        
        self.conteudo_text = scrolledtext.ScrolledText(frame_texto, 
                                                    font=("Calibri", 12), 
                                                    width=80, height=15)
        self.conteudo_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Se estiver editando, preencher o conteúdo
        if dados_oficio and dados_oficio['conteudo']:
            self.conteudo_text.insert(tk.INSERT, dados_oficio['conteudo'])
        else:
            # Texto padrão para novo ofício
            modelo_texto = """[Insira aqui o texto do ofício. Seja claro e objetivo. Inicie falando sobre o motivo do ofício e siga com as informações relevantes.]

    [Parágrafo adicional com mais detalhes, se necessário.]

    [Terceiro parágrafo para conclusões e/ou solicitações.]"""
            self.conteudo_text.insert(tk.INSERT, modelo_texto)
        
        # Despedida
        tk.Label(frame_conteudo_section, text="Despedida:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.despedida_var = tk.StringVar()
        if dados_oficio and dados_oficio.get('despedida'):
            self.despedida_var.set(dados_oficio['despedida'])
        else:
            self.despedida_var.set("Atenciosamente,")
            
        despedida_entry = tk.Entry(frame_conteudo_section, textvariable=self.despedida_var, 
                                font=self.fonte_texto, width=60)
        despedida_entry.grid(row=2, column=1, padx=(5, 0), sticky=tk.W+tk.E)
        
        # === QUARTA SEÇÃO: REMETENTE ===
        frame_remetente = tk.LabelFrame(frame_form, text="Remetente", 
                                    font=self.fonte_rotulo, bg="white", fg=self.cor_primaria, 
                                    padx=10, pady=10)
        frame_remetente.pack(fill=tk.X, pady=15)
        
        # Nome do remetente
        tk.Label(frame_remetente, text="Nome:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.remetente_var = tk.StringVar()
        if dados_oficio and dados_oficio.get('remetente'):
            self.remetente_var.set(dados_oficio['remetente'])
        else:
            self.remetente_var.set(self.nome_usuario_atual)
            
        remetente_entry = tk.Entry(frame_remetente, textvariable=self.remetente_var, 
                                font=self.fonte_texto, width=40)
        remetente_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W+tk.E)
        
        # Cargo do remetente
        tk.Label(frame_remetente, text="Cargo:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.cargo_remetente_var = tk.StringVar()
        if dados_oficio and dados_oficio.get('cargo_remetente'):
            self.cargo_remetente_var.set(dados_oficio['cargo_remetente'])
        else:
            # Obter cargo do usuário do banco de dados
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            cursor.execute("SELECT cargo FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
            cargo_usuario = cursor.fetchone()
            conn.close()
            
            if cargo_usuario and cargo_usuario[0]:
                self.cargo_remetente_var.set(cargo_usuario[0])
            else:
                self.cargo_remetente_var.set("")
            
        cargo_remetente_entry = tk.Entry(frame_remetente, textvariable=self.cargo_remetente_var, 
                                    font=self.fonte_texto, width=40)
        cargo_remetente_entry.grid(row=1, column=1, padx=(5, 20), sticky=tk.W+tk.E)
        
        # === QUINTA SEÇÃO: ELEMENTOS OPCIONAIS ===
        frame_opcionais = tk.LabelFrame(frame_form, text="Elementos Opcionais", 
                                    font=self.fonte_rotulo, bg="white", fg=self.cor_primaria, 
                                    padx=10, pady=10)
        frame_opcionais.pack(fill=tk.X, pady=15)
        
        # Inicializar caminhos de arquivos opcionais
        self.caminho_logotipo = None
        self.caminho_assinatura = None
        
        # Logotipo
        frame_logotipo = tk.Frame(frame_opcionais, bg="white")
        frame_logotipo.grid(row=0, column=0, sticky=tk.W, pady=10, padx=20)
        
        self.tem_logotipo_var = tk.BooleanVar()
        if dados_oficio and dados_oficio.get('tem_logotipo') == 1:
            self.tem_logotipo_var.set(True)
            self.caminho_logotipo = dados_oficio.get('caminho_logotipo')
        else:
            self.tem_logotipo_var.set(False)
        
        cb_logotipo = tk.Checkbutton(frame_logotipo, text="Incluir logotipo", 
                                    variable=self.tem_logotipo_var, 
                                    bg="white", font=self.fonte_texto)
        cb_logotipo.pack(side=tk.LEFT)
        
        btn_logotipo = tk.Button(frame_logotipo, text="Selecionar", font=self.fonte_texto,
                                bg="light gray", fg=self.cor_texto, padx=10, pady=2,
                                command=self.selecionar_logotipo, cursor="hand2")
        btn_logotipo.pack(side=tk.LEFT, padx=10)
        
        self.logotipo_label = tk.Label(frame_logotipo, text="Nenhum arquivo selecionado", 
                                    font=("Calibri", 9, "italic"), bg="white", fg="grey")
        self.logotipo_label.pack(side=tk.LEFT)
        
        if self.caminho_logotipo:
            self.logotipo_label.config(text=os.path.basename(self.caminho_logotipo))
        
        # Assinatura
        frame_assinatura = tk.Frame(frame_opcionais, bg="white")
        frame_assinatura.grid(row=1, column=0, sticky=tk.W, pady=10, padx=20)
        
        self.tem_assinatura_var = tk.BooleanVar()
        if dados_oficio and dados_oficio.get('tem_assinatura') == 1:
            self.tem_assinatura_var.set(True)
            self.caminho_assinatura = dados_oficio.get('caminho_assinatura')
        else:
            self.tem_assinatura_var.set(False)
        
        cb_assinatura = tk.Checkbutton(frame_assinatura, text="Incluir assinatura digital", 
                                    variable=self.tem_assinatura_var, 
                                    bg="white", font=self.fonte_texto)
        cb_assinatura.pack(side=tk.LEFT)
        
        btn_assinatura = tk.Button(frame_assinatura, text="Selecionar", font=self.fonte_texto,
                                bg="light gray", fg=self.cor_texto, padx=10, pady=2,
                                command=self.selecionar_assinatura, cursor="hand2")
        btn_assinatura.pack(side=tk.LEFT, padx=10)
        
        self.assinatura_label = tk.Label(frame_assinatura, text="Nenhum arquivo selecionado", 
                                    font=("Calibri", 9, "italic"), bg="white", fg="grey")
        self.assinatura_label.pack(side=tk.LEFT)
        
        if self.caminho_assinatura:
            self.assinatura_label.config(text=os.path.basename(self.caminho_assinatura))
        
        # Linha de status (apenas para edição)
        if oficio_id:
            frame_status = tk.Frame(frame_form, bg="white")
            frame_status.pack(fill=tk.X, pady=10)
            
            tk.Label(frame_status, text="Status:", font=self.fonte_rotulo, 
                    bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W)
            
            self.status_var = tk.StringVar()
            if dados_oficio and dados_oficio['status']:
                self.status_var.set(dados_oficio['status'])
            else:
                self.status_var.set("Pendente")
                
            status_combo = ttk.Combobox(frame_status, textvariable=self.status_var, 
                                    font=self.fonte_texto, width=20, state="readonly")
            status_combo['values'] = ('Pendente', 'Em andamento', 'Finalizado', 'Cancelado')
            status_combo.grid(row=0, column=1, padx=(5, 20), sticky=tk.W)
            
            # Data de criação (apenas para exibição)
            if dados_oficio and dados_oficio['data_criacao']:
                tk.Label(frame_status, text="Criado em:", font=self.fonte_rotulo, 
                        bg="white", fg=self.cor_texto).grid(row=0, column=2, sticky=tk.W)
                
                data_criacao = datetime.strptime(dados_oficio['data_criacao'], "%Y-%m-%d %H:%M:%S")
                data_formatada = data_criacao.strftime("%d/%m/%Y %H:%M")
                
                data_label = tk.Label(frame_status, text=data_formatada, 
                                    font=self.fonte_texto, bg="white", fg=self.cor_texto)
                data_label.grid(row=0, column=3, padx=(5, 20), sticky=tk.W)
        
        # Frame de botões
        frame_botoes = tk.Frame(frame_form, bg="white")
        frame_botoes.pack(fill=tk.X, pady=20)
        
        # Botão voltar
        btn_voltar = tk.Button(frame_botoes, text="Cancelar", font=self.fonte_texto,
                            bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                            command=self.mostrar_tela_meus_oficios, cursor="hand2")
        btn_voltar.pack(side=tk.LEFT, padx=5)
        
        # Botão visualizar prévia
        btn_previa = tk.Button(frame_botoes, text="Visualizar Prévia", font=self.fonte_texto,
                            bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                            command=self.visualizar_previa_oficio, cursor="hand2")
        btn_previa.pack(side=tk.LEFT, padx=5)
        
        # Botão salvar/atualizar
        if oficio_id:
            btn_texto = "Atualizar Ofício"
            btn_comando = lambda: self.salvar_oficio(atualizar=True)
        else:
            btn_texto = "Salvar Ofício"
            btn_comando = lambda: self.salvar_oficio(atualizar=False)
            
        btn_salvar = tk.Button(frame_botoes, text=btn_texto, font=self.fonte_texto,
                            bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                            command=btn_comando, cursor="hand2")
        btn_salvar.pack(side=tk.LEFT, padx=5)
        
        # Se estiver editando, adicionar botão para gerar PDF
        if oficio_id:
            btn_pdf = tk.Button(frame_botoes, text="Gerar PDF", font=self.fonte_texto,
                            bg="#388E3C", fg="white", padx=15, pady=5, cursor="hand2",
                            command=self.gerar_pdf_oficio)
            btn_pdf.pack(side=tk.LEFT, padx=5)    

    def gerar_proximo_numero_oficio(self):
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Obter o ano atual
            ano_atual = datetime.now().year
            
            # Contar ofícios do usuário para o ano atual
            cursor.execute("""
            SELECT COUNT(*) FROM oficios 
            WHERE usuario_id = ? AND numero LIKE ?
            """, (self.id_usuario_atual, f"%{ano_atual}"))
            
            contador = cursor.fetchone()[0] + 1
            
            # Gerar novo número no formato: 000X/ANO/SIGLA-DEPARTAMENTO
            if self.municipio_usuario_atual == "Florianópolis":
                sigla = "PMF"
            else:
                sigla = "PMSJ"
                
            # Obter departamento do usuário
            cursor.execute("SELECT departamento FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
            departamento = cursor.fetchone()[0]
            
            # Extrair sigla do departamento (primeiras letras de cada palavra)
            sigla_dep = ""
            if departamento:
                partes = departamento.split()
                for parte in partes:
                    if parte[0].isalpha():
                        sigla_dep += parte[0].upper()
            
            if not sigla_dep:
                sigla_dep = "GER"  # Sigla genérica
            
            numero_formatado = f"{contador:04d}/{ano_atual}/{sigla}-{sigla_dep}"
            return numero_formatado
            
        except Exception as e:
            print(f"Erro ao gerar número de ofício: {str(e)}")
            return f"0001/{datetime.now().year}/ERRO"
        finally:
            if 'conn' in locals():
                conn.close()
    
    def obter_dados_oficio(self, oficio_id):
        try:
            conn = self.obter_conexao_banco()
            conn.row_factory = sqlite3.Row  # Para acessar resultados por nome de coluna
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM oficios WHERE id = ? AND usuario_id = ?
            """, (oficio_id, self.id_usuario_atual))
            
            resultado = cursor.fetchone()
            
            if resultado:
                dados = dict(resultado)
                return dados
            return None
            
        except Exception as e:
            print(f"Erro ao obter dados do ofício: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def visualizar_previa_oficio(self):
        # Obter dados dos campos
        numero = self.num_oficio_var.get().strip()
        assunto = self.assunto_var.get().strip()
        destinatario = self.destinatario_var.get().strip()
        cargo = self.cargo_dest_var.get().strip()
        orgao = self.orgao_var.get().strip()
        conteudo = self.conteudo_text.get("1.0", tk.END).strip()
        
        # Validar campos obrigatórios
        if not numero or not assunto or not destinatario or not conteudo:
            messagebox.showwarning("Atenção", "Preencha pelo menos o número, assunto, destinatário e conteúdo.")
            return
        
        # Criar janela de prévia
        janela_previa = tk.Toplevel(self.root)
        janela_previa.title("Prévia do Ofício")
        janela_previa.geometry("800x600")
        janela_previa.grab_set()  # Torna modal
        
        # Frame principal
        frame_principal = tk.Frame(janela_previa, bg="white", padx=40, pady=30)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        if self.municipio_usuario_atual == "Florianópolis":
            municipio_texto = "PREFEITURA MUNICIPAL DE FLORIANÓPOLIS"
            endereco = "Rua Tenente Silveira, 60 - Centro, Florianópolis - SC, 88010-300"
        else:
            municipio_texto = "PREFEITURA MUNICIPAL DE SÃO JOSÉ"
            endereco = "Av. Acioni Souza Filho, 403 - Centro, São José - SC, 88103-790"
        
        titulo_mun = tk.Label(frame_principal, text=municipio_texto, 
                             font=("Calibri", 14, "bold"), bg="white", fg=self.cor_primaria)
        titulo_mun.pack(pady=(0, 5))
        
        # Secretaria/Departamento
        conn = self.obter_conexao_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT departamento FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
        departamento = cursor.fetchone()[0]
        conn.close()
        
        if departamento:
            dep_label = tk.Label(frame_principal, text=departamento.upper(), 
                               font=("Calibri", 12), bg="white", fg=self.cor_texto)
            dep_label.pack(pady=(0, 5))
        
        # Endereço
        end_label = tk.Label(frame_principal, text=endereco, 
                           font=("Calibri", 10), bg="white", fg=self.cor_texto)
        end_label.pack(pady=(0, 15))
        
        # Separador
        frame_linha = tk.Frame(frame_principal, height=2, bg=self.cor_secundaria)
        frame_linha.pack(fill=tk.X, pady=10)
        
        # Número e data
        frame_header = tk.Frame(frame_principal, bg="white")
        frame_header.pack(fill=tk.X, pady=10)
        
        num_label = tk.Label(frame_header, text=f"OFÍCIO Nº {numero}", 
                           font=("Calibri", 12, "bold"), bg="white", fg=self.cor_texto)
        num_label.pack(side=tk.LEFT)
        
        data_atual = datetime.now().strftime("%d de %B de %Y")
        data_label = tk.Label(frame_header, text=f"{self.municipio_usuario_atual}, {data_atual}", 
                            font=("Calibri", 12), bg="white", fg=self.cor_texto)
        data_label.pack(side=tk.RIGHT)
        
        # Destinatário
        frame_dest = tk.Frame(frame_principal, bg="white")
        frame_dest.pack(fill=tk.X, anchor=tk.W, pady=30)
        
        dest_text = f"A Sua Senhoria o(a) Senhor(a)\n{destinatario}"
        if cargo:
            dest_text += f"\n{cargo}"
        if orgao:
            dest_text += f"\n{orgao}"
            
        dest_label = tk.Label(frame_dest, text=dest_text, 
                            font=("Calibri", 12), bg="white", fg=self.cor_texto,
                            justify=tk.LEFT)
        dest_label.pack(anchor=tk.W)
        
        # Assunto
        frame_assunto = tk.Frame(frame_principal, bg="white")
        frame_assunto.pack(fill=tk.X, anchor=tk.W, pady=20)
        
        assunto_label = tk.Label(frame_assunto, text=f"Assunto: {assunto}", 
                               font=("Calibri", 12, "bold"), bg="white", fg=self.cor_texto,
                               justify=tk.LEFT)
        assunto_label.pack(anchor=tk.W)
        
        # Conteúdo
        frame_conteudo = tk.Frame(frame_principal, bg="white")
        frame_conteudo.pack(fill=tk.BOTH, expand=True, pady=10)
        
        conteudo_text = scrolledtext.ScrolledText(frame_conteudo, font=("Calibri", 12), 
                                               width=80, height=15, wrap=tk.WORD)
        conteudo_text.pack(fill=tk.BOTH, expand=True)
        conteudo_text.insert(tk.INSERT, conteudo)
        conteudo_text.configure(state="disabled")  # Somente leitura
        
        # Botões
        frame_botoes = tk.Frame(janela_previa, bg=self.cor_bg, padx=10, pady=10)
        frame_botoes.pack(fill=tk.X)
        
        btn_fechar = tk.Button(frame_botoes, text="Fechar", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=janela_previa.destroy, cursor="hand2")
        btn_fechar.pack(side=tk.RIGHT, padx=10)
    
    def salvar_oficio(self, atualizar=False):
        """
        Salva ou atualiza um ofício no banco de dados.
        
        Args:
            atualizar (bool, optional): Se True, atualiza um ofício existente. 
                                    Se False, cria um novo ofício.
        """
        # Obter dados dos campos
        numero = self.num_oficio_var.get().strip()
        protocolo = self.protocolo_var.get().strip()
        assunto = self.assunto_var.get().strip()
        destinatario = self.destinatario_var.get().strip()
        cargo = self.cargo_dest_var.get().strip()
        orgao = self.orgao_var.get().strip()
        conteudo = self.conteudo_text.get("1.0", tk.END).strip()
        cumprimentos = self.cumprimentos_var.get().strip()
        despedida = self.despedida_var.get().strip()
        remetente = self.remetente_var.get().strip()
        cargo_remetente = self.cargo_remetente_var.get().strip()
        tem_logotipo = self.tem_logotipo_var.get()
        tem_assinatura = self.tem_assinatura_var.get()
        
        # Verificar se os caminhos dos arquivos estão definidos
        if tem_logotipo and not self.caminho_logotipo:
            messagebox.showwarning("Atenção", "Logotipo selecionado mas nenhum arquivo escolhido.")
            return
            
        if tem_assinatura and not self.caminho_assinatura:
            messagebox.showwarning("Atenção", "Assinatura selecionada mas nenhum arquivo escolhido.")
            return
        
        # Validar campos obrigatórios
        if not numero or not assunto or not destinatario or not conteudo:
            messagebox.showwarning("Atenção", "Preencha pelo menos o número, assunto, destinatário e conteúdo.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if atualizar and self.id_oficio_atual:
                # Se houver status, obter do campo, senão manter como Pendente
                if hasattr(self, 'status_var'):
                    status = self.status_var.get()
                else:
                    # Obter status atual
                    cursor.execute("SELECT status FROM oficios WHERE id = ?", (self.id_oficio_atual,))
                    resultado = cursor.fetchone()
                    status = resultado[0] if resultado else "Pendente"
                
                # Atualizar ofício existente
                cursor.execute("""
                UPDATE oficios SET 
                numero = ?, protocolo = ?, assunto = ?, destinatario = ?, cargo_destinatario = ?,
                orgao_destinatario = ?, conteudo = ?, cumprimentos = ?, despedida = ?,
                remetente = ?, cargo_remetente = ?, tem_logotipo = ?, caminho_logotipo = ?,
                tem_assinatura = ?, caminho_assinatura = ?, data_modificacao = ?, status = ?
                WHERE id = ? AND usuario_id = ?
                """, (numero, protocolo, assunto, destinatario, cargo, orgao, conteudo, 
                    cumprimentos, despedida, remetente, cargo_remetente, 
                    1 if tem_logotipo else 0, self.caminho_logotipo if tem_logotipo else None,
                    1 if tem_assinatura else 0, self.caminho_assinatura if tem_assinatura else None,
                    agora, status, self.id_oficio_atual, self.id_usuario_atual))
                
                mensagem = "Ofício atualizado com sucesso!"
            else:
                # Inserir novo ofício
                cursor.execute("""
                INSERT INTO oficios (
                    numero, protocolo, assunto, destinatario, cargo_destinatario, orgao_destinatario,
                    conteudo, cumprimentos, despedida, remetente, cargo_remetente,
                    tem_logotipo, caminho_logotipo, tem_assinatura, caminho_assinatura,
                    data_criacao, status, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (numero, protocolo, assunto, destinatario, cargo, orgao, conteudo, 
                    cumprimentos, despedida, remetente, cargo_remetente, 
                    1 if tem_logotipo else 0, self.caminho_logotipo if tem_logotipo else None,
                    1 if tem_assinatura else 0, self.caminho_assinatura if tem_assinatura else None,
                    agora, "Pendente", self.id_usuario_atual))
                
                # Obter o ID do ofício recém-criado
                self.id_oficio_atual = cursor.lastrowid
                mensagem = "Ofício criado com sucesso!"
            
            conn.commit()
            messagebox.showinfo("Sucesso", mensagem)
            
            # Perguntar se deseja gerar PDF
            if messagebox.askyesno("Gerar PDF", "Deseja gerar o PDF do ofício agora?"):
                self.gerar_pdf_oficio()
            else:
                # Redirecionar para a lista de ofícios
                self.mostrar_tela_meus_oficios()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar ofício: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def selecionar_logotipo(self):
        """Permite ao usuário selecionar um arquivo de logotipo."""
        if self.tem_logotipo_var.get():
            arquivo = filedialog.askopenfilename(
                title="Selecionar Logotipo",
                filetypes=[
                    ("Imagens", "*.png *.jpg *.jpeg *.gif"),
                    ("Todos os arquivos", "*.*")
                ]
            )
            if arquivo:
                self.caminho_logotipo = arquivo
                self.logotipo_label.config(text=os.path.basename(arquivo))
            else:
                self.tem_logotipo_var.set(False)
        else:
            self.caminho_logotipo = None
            self.logotipo_label.config(text="Nenhum arquivo selecionado")

    def selecionar_assinatura(self):
        """Permite ao usuário selecionar um arquivo de assinatura."""
        arquivo = filedialog.askopenfilename(
            title="Selecionar Assinatura",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.gif"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if arquivo:
            self.caminho_assinatura = arquivo
            self.tem_assinatura_var.set(True)
            self.assinatura_label.config(text=os.path.basename(arquivo))
        
    def gerar_pdf_oficio(self):
        """Gera um arquivo PDF do ofício atual."""
        if not self.id_oficio_atual:
            messagebox.showerror("Erro", "Nenhum ofício selecionado.")
            return
        
        # Obter dados do ofício
        dados_oficio = self.obter_dados_oficio(self.id_oficio_atual)
        if not dados_oficio:
            messagebox.showerror("Erro", "Não foi possível obter os dados do ofício.")
            return
        
        # Solicitar local para salvar o arquivo
        arquivo_saida = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            initialfile=f"Oficio_{dados_oficio['numero'].replace('/', '_')}.pdf"
        )
        
        if not arquivo_saida:
            return  # Usuário cancelou
        
        try:
            # Criar o PDF
            c = canvas.Canvas(arquivo_saida, pagesize=A4)
            largura, altura = A4
            
            # Registrar fonte padrão
            try:
                pdfmetrics.registerFont(TTFont('Calibri', 'calibri.ttf'))
                pdfmetrics.registerFont(TTFont('CalibriB', 'calibrib.ttf'))
            except:
                # Caso as fontes Calibri não estejam disponíveis, usar fontes padrão
                print("Fontes Calibri não encontradas, usando fontes padrão.")
            
            # Configurações iniciais do PDF
            estilo_titulo = ParagraphStyle('Titulo', fontName='Helvetica-Bold', fontSize=14, 
                                        alignment=TA_CENTER, textColor=black)
            estilo_subtitulo = ParagraphStyle('Subtitulo', fontName='Helvetica', fontSize=12, 
                                            alignment=TA_CENTER, textColor=black)
            estilo_endereco = ParagraphStyle('Endereco', fontName='Helvetica', fontSize=10, 
                                            alignment=TA_CENTER, textColor=black)
            estilo_conteudo = ParagraphStyle('Conteudo', fontName='Helvetica', fontSize=12, 
                                            alignment=TA_JUSTIFY, leading=14, textColor=black)
            estilo_data = ParagraphStyle('Data', fontName='Helvetica', fontSize=12, 
                                        alignment=TA_RIGHT, textColor=black)
            estilo_assinatura = ParagraphStyle('Assinatura', fontName='Helvetica-Bold', fontSize=12, 
                                            alignment=TA_CENTER, textColor=black)
            
            # Posição Y inicial
            y_pos = altura - 50  # Iniciar 50 pontos abaixo do topo
            
            # Adicionar logotipo se solicitado
            if dados_oficio.get('tem_logotipo') == 1 and dados_oficio.get('caminho_logotipo'):
                try:
                    logo_path = dados_oficio['caminho_logotipo']
                    if os.path.exists(logo_path):
                        # Calcular dimensões para o logotipo (tamanho máximo de 1.5 polegadas)
                        img = Image.open(logo_path)
                        w, h = img.size
                        aspect = w / float(h)
                        max_width = 108  # 1.5 inches at 72 dpi
                        width = min(max_width, w)
                        height = width / aspect
                        
                        # Posicionar no topo da página
                        c.drawImage(logo_path, 50, altura-70, width=width, height=height)
                        
                        # Ajustar posição Y para começar abaixo do logotipo
                        y_pos = altura - 80 - height
                    else:
                        print("Arquivo de logotipo não encontrado:", logo_path)
                except Exception as e:
                    print(f"Erro ao adicionar logotipo: {str(e)}")
            
            # Cabeçalho
            if self.municipio_usuario_atual == "Florianópolis":
                municipio_texto = "PREFEITURA MUNICIPAL DE FLORIANÓPOLIS"
                endereco = "Rua Tenente Silveira, 60 - Centro, Florianópolis - SC, 88010-300"
            else:
                municipio_texto = "PREFEITURA MUNICIPAL DE SÃO JOSÉ"
                endereco = "Av. Acioni Souza Filho, 403 - Centro, São José - SC, 88103-790"
            
            # Consultar departamento do usuário
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            cursor.execute("SELECT departamento FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
            departamento = cursor.fetchone()
            departamento = departamento[0] if departamento and departamento[0] else ""
            conn.close()
            
            # Desenhar o cabeçalho
            c.setFont('Helvetica-Bold', 14)
            c.drawCentredString(largura/2, y_pos, municipio_texto)
            y_pos -= 20
            
            if departamento:
                c.setFont('Helvetica', 12)
                c.drawCentredString(largura/2, y_pos, departamento.upper())
                y_pos -= 20
            
            c.setFont('Helvetica', 10)
            c.drawCentredString(largura/2, y_pos, endereco)
            y_pos -= 20
            
            # Linha separadora
            c.setStrokeColor(black)
            c.setLineWidth(1)
            c.line(50, y_pos - 10, largura-50, y_pos - 10)
            y_pos -= 30
            
            # Número do ofício e data
            c.setFont('Helvetica-Bold', 12)
            c.drawString(50, y_pos, f"OFÍCIO Nº {dados_oficio['numero']}")
            
            # Protocolo (se existir)
            if dados_oficio.get('protocolo'):
                c.setFont('Helvetica', 11)
                c.drawString(50, y_pos - 15, f"Protocolo: {dados_oficio['protocolo']}")
                y_pos -= 30
            else:
                y_pos -= 15
            
            # Data
            data_atual = datetime.strptime(dados_oficio['data_criacao'], "%Y-%m-%d %H:%M:%S")
            data_formatada = data_atual.strftime("%d de %B de %Y")
            
            c.setFont('Helvetica', 12)
            c.drawRightString(largura-50, y_pos, f"{self.municipio_usuario_atual}, {data_formatada}")
            y_pos -= 40
            
            # Destinatário
            c.setFont('Helvetica', 12)
            c.drawString(50, y_pos, "A Sua Senhoria o(a) Senhor(a)")
            y_pos -= 15
            c.drawString(50, y_pos, dados_oficio['destinatario'])
            
            if dados_oficio['cargo_destinatario']:
                y_pos -= 15
                c.drawString(50, y_pos, dados_oficio['cargo_destinatario'])
                
            if dados_oficio['orgao_destinatario']:
                y_pos -= 15
                c.drawString(50, y_pos, dados_oficio['orgao_destinatario'])
            
            # Assunto
            y_pos -= 30
            c.setFont('Helvetica-Bold', 12)
            c.drawString(50, y_pos, f"Assunto: {dados_oficio['assunto']}")
            
            # Cumprimentos
            y_pos -= 30
            c.setFont('Helvetica', 12)
            c.drawString(50, y_pos, dados_oficio.get('cumprimentos', 'Prezado(a) Senhor(a),'))
            
            # Conteúdo - usar estilo de parágrafo para texto com quebras automáticas
            y_pos -= 20
            texto_conteudo = dados_oficio['conteudo']
            
            # Substituir quebras de linha por tags HTML <br/>
            texto_formatado = texto_conteudo.replace('\n', '<br/>')
            
            # Criar frame para o conteúdo
            frame = Frame(
                50,  # x
                120,  # y (deixar espaço para assinatura)
                largura-100,  # largura
                y_pos - 120,  # altura
                leftPadding=0,
                bottomPadding=0,
                rightPadding=0,
                topPadding=0,
            )
            
            # Criar parágrafo com o conteúdo
            paragrafo = Paragraph(texto_formatado, estilo_conteudo)
            
            # Adicionar parágrafo ao frame
            frame.addFromList([paragrafo], c)
            
            # Despedida
            c.setFont('Helvetica', 12)
            c.drawString(50, 110, dados_oficio.get('despedida', 'Atenciosamente,'))
            
            # Adicionar assinatura se solicitado
            if dados_oficio.get('tem_assinatura') == 1 and dados_oficio.get('caminho_assinatura'):
                try:
                    assinatura_path = dados_oficio['caminho_assinatura']
                    if os.path.exists(assinatura_path):
                        # Calcular dimensões para a assinatura
                        img = Image.open(assinatura_path)
                        w, h = img.size
                        aspect = w / float(h)
                        max_width = 100
                        width = min(max_width, w)
                        height = width / aspect
                        
                        # Posicionar acima do nome do remetente
                        c.drawImage(assinatura_path, largura/2 - width/2, 70, width=width, height=height)
                        
                        # Nome e cargo do remetente
                        c.setFont('Helvetica-Bold', 12)
                        c.drawCentredString(largura/2, 50, dados_oficio.get('remetente', self.nome_usuario_atual))
                        
                        if dados_oficio.get('cargo_remetente'):
                            c.setFont('Helvetica', 12)
                            c.drawCentredString(largura/2, 35, dados_oficio.get('cargo_remetente', ''))
                    else:
                        print("Arquivo de assinatura não encontrado:", assinatura_path)
                except Exception as e:
                    print(f"Erro ao adicionar assinatura: {str(e)}")
            else:
                # Nome e cargo do remetente sem assinatura digital
                c.setFont('Helvetica-Bold', 12)
                c.drawCentredString(largura/2, 70, dados_oficio.get('remetente', self.nome_usuario_atual))
                
                if dados_oficio.get('cargo_remetente'):
                    c.setFont('Helvetica', 12)
                    c.drawCentredString(largura/2, 55, dados_oficio.get('cargo_remetente', ''))
            
            # Numerar página (nº/total)
            c.setFont('Helvetica', 9)
            c.drawCentredString(largura/2, 20, "Página 1/1")
            
            # Salvar o arquivo PDF
            c.save()
            
            # Atualizar o caminho do arquivo no banco de dados
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE oficios SET caminho_arquivo = ? WHERE id = ?",
                (arquivo_saida, self.id_oficio_atual)
            )
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", f"PDF gerado com sucesso em:\n{arquivo_saida}")
            
            # Perguntar se deseja abrir o arquivo
            if messagebox.askyesno("Abrir PDF", "Deseja abrir o arquivo PDF agora?"):
                # Abrir o PDF com o visualizador padrão do sistema
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(arquivo_saida)
                    else:  # macOS e Linux
                        import subprocess
                        subprocess.call(['open', arquivo_saida] if sys.platform == 'darwin' else ['xdg-open', arquivo_saida])
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível abrir o arquivo: {str(e)}")
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {str(e)}")
            print(f"Detalhes do erro: {e}")  # Log detalhado do erro

    # ================ TELA DE MEUS OFÍCIOS ================
    
    def mostrar_tela_meus_oficios(self):
        self.limpar_frame_conteudo()
        
        # Frame principal
        frame_oficios = tk.Frame(self.frame_conteudo, bg="white", padx=30, pady=20)
        frame_oficios.pack(fill=tk.BOTH, expand=True)
        
        # Título da página
        titulo = tk.Label(frame_oficios, text="Meus Ofícios", 
                         font=("Calibri", 20, "bold"), bg="white", fg=self.cor_texto)
        titulo.pack(anchor=tk.W, pady=(0, 20))
        
        # Frame para filtros e pesquisa
        frame_filtros = tk.Frame(frame_oficios, bg="white")
        frame_filtros.pack(fill=tk.X, pady=10)
        
        # Pesquisa
        tk.Label(frame_filtros, text="Pesquisar:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W)
        
        self.pesquisa_var = tk.StringVar()
        pesquisa_entry = tk.Entry(frame_filtros, textvariable=self.pesquisa_var, 
                                 font=self.fonte_texto, width=40)
        pesquisa_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W)
        
        # Filtro por status
        tk.Label(frame_filtros, text="Status:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=2, sticky=tk.W)
        
        self.filtro_status_var = tk.StringVar()
        self.filtro_status_var.set("Todos")
        
        status_combo = ttk.Combobox(frame_filtros, textvariable=self.filtro_status_var, 
                                   font=self.fonte_texto, width=15, state="readonly")
        status_combo['values'] = ('Todos', 'Pendente', 'Em andamento', 'Finalizado', 'Cancelado')
        status_combo.grid(row=0, column=3, padx=(5, 20), sticky=tk.W)
        
        # Botão pesquisar
        btn_pesquisar = tk.Button(frame_filtros, text="Pesquisar", font=self.fonte_texto,
                                 bg="light gray", fg=self.cor_texto, padx=15, pady=2,
                                 command=self.filtrar_oficios, cursor="hand2")
        btn_pesquisar.grid(row=0, column=4, padx=5)
        
        # Botão novo ofício
        btn_novo = tk.Button(frame_filtros, text="+ Novo Ofício", font=self.fonte_texto,
                            bg="light gray", fg=self.cor_texto, padx=15, pady=2,
                            command=self.mostrar_tela_novo_oficio, cursor="hand2")
        btn_novo.grid(row=0, column=5, padx=5)
        
        # Frame para a tabela
        frame_tabela = tk.Frame(frame_oficios, bg="white")
        frame_tabela.pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Criar tabela usando Treeview
        colunas = ("numero", "assunto", "destinatario", "data_criacao", "status")
        self.tabela_oficios = ttk.Treeview(frame_tabela, columns=colunas, show="headings", 
                                         selectmode="browse", height=15)
        
        # Definir cabeçalhos
        self.tabela_oficios.heading("numero", text="Número")
        self.tabela_oficios.heading("assunto", text="Assunto")
        self.tabela_oficios.heading("destinatario", text="Destinatário")
        self.tabela_oficios.heading("data_criacao", text="Data de Criação")
        self.tabela_oficios.heading("status", text="Status")
        
        # Definir larguras das colunas
        self.tabela_oficios.column("numero", width=150, minwidth=150)
        self.tabela_oficios.column("assunto", width=250, minwidth=200)
        self.tabela_oficios.column("destinatario", width=200, minwidth=150)
        self.tabela_oficios.column("data_criacao", width=150, minwidth=150)
        self.tabela_oficios.column("status", width=100, minwidth=100)
        
        # Scrollbar para a tabela
        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tabela_oficios.yview)
        self.tabela_oficios.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabela_oficios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vincular evento de clique na tabela
        self.tabela_oficios.bind("<Double-1>", self.abrir_oficio_selecionado)
        
        # Carregar dados na tabela
        self.filtrar_oficios()
        
        # Frame para botões de ação
        frame_acoes = tk.Frame(frame_oficios, bg="white")
        frame_acoes.pack(fill=tk.X, pady=10)
        
        # Botões de ação
        btn_editar = tk.Button(frame_acoes, text="Editar", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=self.editar_oficio_selecionado, cursor="hand2")
        btn_editar.pack(side=tk.LEFT, padx=5)
        
        btn_pdf = tk.Button(frame_acoes, text="Gerar PDF", font=self.fonte_texto,
                           bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                           command=self.gerar_pdf_selecionado, cursor="hand2")
        btn_pdf.pack(side=tk.LEFT, padx=5)
        
        btn_excluir = tk.Button(frame_acoes, text="Excluir", font=self.fonte_texto,
                               bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                               command=self.excluir_oficio_selecionado, cursor="hand2")
        btn_excluir.pack(side=tk.LEFT, padx=5)
        
        # Informações
        info_total = tk.Label(frame_oficios, text=f"Total de ofícios: {self.contar_oficios_usuario()}", 
                             font=("Calibri", 11), bg="white", fg=self.cor_texto)
        info_total.pack(side=tk.RIGHT, pady=10)
    
    def filtrar_oficios(self):
        # Limpar tabela
        for item in self.tabela_oficios.get_children():
            self.tabela_oficios.delete(item)
        
        # Obter filtros
        pesquisa = self.pesquisa_var.get().strip().lower()
        status_filtro = self.filtro_status_var.get()
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Construir consulta SQL base
            sql = """
            SELECT id, numero, assunto, destinatario, data_criacao, status 
            FROM oficios 
            WHERE usuario_id = ?
            """
            params = [self.id_usuario_atual]
            
            # Adicionar filtro de status
            if status_filtro != "Todos":
                sql += " AND status = ?"
                params.append(status_filtro)
            
            # Adicionar filtro de pesquisa
            if pesquisa:
                sql += """ AND (
                    lower(numero) LIKE ? OR 
                    lower(assunto) LIKE ? OR 
                    lower(destinatario) LIKE ? OR
                    lower(conteudo) LIKE ?
                )"""
                termo_busca = f"%{pesquisa}%"
                params.extend([termo_busca, termo_busca, termo_busca, termo_busca])
            
            # Ordenar por data de criação (mais recentes primeiro)
            sql += " ORDER BY data_criacao DESC"
            
            cursor.execute(sql, params)
            resultado = cursor.fetchall()
            
            # Preencher a tabela com os resultados
            for row in resultado:
                oficio_id = row[0]
                numero = row[1]
                assunto = row[2]
                destinatario = row[3]
                
                # Formatar data
                data_criacao = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                data_formatada = data_criacao.strftime("%d/%m/%Y %H:%M")
                
                status = row[5]
                
                # Inserir na tabela
                self.tabela_oficios.insert("", tk.END, iid=oficio_id, values=(
                    numero, assunto, destinatario, data_formatada, status
                ))
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar ofícios: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def abrir_oficio_selecionado(self, event):
        # Pegar o item selecionado
        selecionado = self.tabela_oficios.selection()
        if not selecionado:
            return
            
        oficio_id = selecionado[0]
        self.mostrar_tela_novo_oficio(oficio_id=oficio_id)
    
    def editar_oficio_selecionado(self):
        # Pegar o item selecionado
        selecionado = self.tabela_oficios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um ofício para editar.")
            return
            
        oficio_id = selecionado[0]
        self.mostrar_tela_novo_oficio(oficio_id=oficio_id)
    
    def gerar_pdf_selecionado(self):
        # Pegar o item selecionado
        selecionado = self.tabela_oficios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um ofício para gerar o PDF.")
            return
            
        oficio_id = selecionado[0]
        self.id_oficio_atual = oficio_id
        self.gerar_pdf_oficio()
    
    def excluir_oficio_selecionado(self):
        # Pegar o item selecionado
        selecionado = self.tabela_oficios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um ofício para excluir.")
            return
            
        oficio_id = selecionado[0]
        
        # Confirmar exclusão
        if not messagebox.askyesno("Confirmar Exclusão", 
                                  "Tem certeza que deseja excluir este ofício? Esta ação não pode ser desfeita."):
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Excluir ofício
            cursor.execute("DELETE FROM oficios WHERE id = ? AND usuario_id = ?", 
                          (oficio_id, self.id_usuario_atual))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Ofício excluído com sucesso!")
            
            # Atualizar a tabela
            self.filtrar_oficios()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir ofício: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    # ================ TELA DE PERFIL ================
    
    def mostrar_tela_perfil(self):
        self.limpar_frame_conteudo()
        
        # Frame principal
        frame_perfil = tk.Frame(self.frame_conteudo, bg="white", padx=30, pady=20)
        frame_perfil.pack(fill=tk.BOTH, expand=True)
        
        # Título da página
        titulo = tk.Label(frame_perfil, text="Meu Perfil", 
                         font=("Calibri", 20, "bold"), bg="WHITE", fg=self.cor_texto)
        titulo.pack(anchor=tk.W, pady=(0, 20))
        
        # Obter dados do usuário
        dados_usuario = self.obter_dados_usuario()
        
        if not dados_usuario:
            messagebox.showerror("Erro", "Não foi possível carregar os dados do usuário.")
            return
        
        # Frame do formulário
        frame_form = tk.Frame(frame_perfil, bg="white")
        frame_form.pack(fill=tk.X, pady=10)
        
        # Nome
        tk.Label(frame_form, text="Nome:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        self.perfil_nome_var = tk.StringVar()
        self.perfil_nome_var.set(dados_usuario['nome'])
        tk.Entry(frame_form, textvariable=self.perfil_nome_var, 
                font=self.fonte_texto, width=40).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Email (somente leitura)
        tk.Label(frame_form, text="Email:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        tk.Label(frame_form, text=dados_usuario['email'], 
                font=self.fonte_texto, bg="white", fg=self.cor_texto).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Município (somente leitura)
        tk.Label(frame_form, text="Município:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        tk.Label(frame_form, text=dados_usuario['municipio'], 
                font=self.fonte_texto, bg="white", fg=self.cor_texto).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Departamento
        tk.Label(frame_form, text="Departamento:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=3, column=0, sticky=tk.W, pady=10)
        
        self.perfil_dept_var = tk.StringVar()
        self.perfil_dept_var.set(dados_usuario['departamento'] or "")
        tk.Entry(frame_form, textvariable=self.perfil_dept_var, 
                font=self.fonte_texto, width=40).grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # Cargo
        tk.Label(frame_form, text="Cargo:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=4, column=0, sticky=tk.W, pady=10)
        
        self.perfil_cargo_var = tk.StringVar()
        self.perfil_cargo_var.set(dados_usuario['cargo'] or "")
        tk.Entry(frame_form, textvariable=self.perfil_cargo_var, 
                font=self.fonte_texto, width=40).grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        # Perfil (somente leitura)
        tk.Label(frame_form, text="Tipo de Perfil:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=5, column=0, sticky=tk.W, pady=10)
        
        perfil_texto = "Administrador" if dados_usuario['perfil'] == "admin" else "Usuário"
        tk.Label(frame_form, text=perfil_texto, 
                font=self.fonte_texto, bg="white", fg=self.cor_texto).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))
        
        # Data de cadastro (somente leitura)
        tk.Label(frame_form, text="Cadastrado em:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=6, column=0, sticky=tk.W, pady=10)
        
        data_cadastro = datetime.strptime(dados_usuario['data_cadastro'], "%Y-%m-%d %H:%M:%S")
        data_formatada = data_cadastro.strftime("%d/%m/%Y %H:%M")
        
        tk.Label(frame_form, text=data_formatada, 
                font=self.fonte_texto, bg="white", fg=self.cor_texto).grid(row=6, column=1, sticky=tk.W, padx=(10, 0))
        
        # Separador
        separador = tk.Frame(frame_perfil, height=2, bg="light gray")
        separador.pack(fill=tk.X, pady=20)
        
        # Alterar senha
        tk.Label(frame_perfil, text="Alterar Senha", 
                font=("Calibri", 16, "bold"), bg="white", fg=self.cor_primaria).pack(anchor=tk.W, pady=(10, 20))
        
        frame_senha = tk.Frame(frame_perfil, bg="white")
        frame_senha.pack(fill=tk.X, pady=10)
        
        # Senha atual
        tk.Label(frame_senha, text="Senha Atual:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        self.senha_atual_var = tk.StringVar()
        tk.Entry(frame_senha, textvariable=self.senha_atual_var, 
                font=self.fonte_texto, width=30, show="•").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Nova senha
        tk.Label(frame_senha, text="Nova Senha:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.nova_senha_var = tk.StringVar()
        tk.Entry(frame_senha, textvariable=self.nova_senha_var, 
                font=self.fonte_texto, width=30, show="•").grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Confirmar nova senha
        tk.Label(frame_senha, text="Confirmar Nova Senha:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        self.conf_nova_senha_var = tk.StringVar()
        tk.Entry(frame_senha, textvariable=self.conf_nova_senha_var, 
                font=self.fonte_texto, width=30, show="•").grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Frame de botões
        frame_botoes = tk.Frame(frame_perfil, bg="white")
        frame_botoes.pack(fill=tk.X, pady=30)
        
        # Botões
        btn_voltar = tk.Button(frame_botoes, text="Voltar", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=self.mostrar_dashboard, cursor="hand2")
        btn_voltar.pack(side=tk.LEFT, padx=5)
        
        btn_salvar_perfil = tk.Button(frame_botoes, text="Salvar Alterações", font=self.fonte_texto,
                                     bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                                     command=self.salvar_perfil, cursor="hand2")
        btn_salvar_perfil.pack(side=tk.LEFT, padx=5)
        
        btn_alterar_senha = tk.Button(frame_botoes, text="Alterar Senha", font=self.fonte_texto,
                                     bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                                     command=self.alterar_senha, cursor="hand2")
        btn_alterar_senha.pack(side=tk.LEFT, padx=5)
    
    def obter_dados_usuario(self):
        try:
            conn = self.obter_conexao_banco()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
            resultado = cursor.fetchone()
            
            if resultado:
                return dict(resultado)
            return None
            
        except Exception as e:
            print(f"Erro ao obter dados do usuário: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def salvar_perfil(self):
        # Obter dados dos campos
        nome = self.perfil_nome_var.get().strip()
        departamento = self.perfil_dept_var.get().strip()
        cargo = self.perfil_cargo_var.get().strip()
        
        # Validar nome (obrigatório)
        if not nome:
            messagebox.showwarning("Atenção", "O nome é obrigatório.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Atualizar dados do usuário
            cursor.execute("""
            UPDATE usuarios SET nome = ?, departamento = ?, cargo = ?
            WHERE id = ?
            """, (nome, departamento, cargo, self.id_usuario_atual))
            
            conn.commit()
            
            # Atualizar variável de sessão
            self.nome_usuario_atual = nome
            
            messagebox.showinfo("Sucesso", "Perfil atualizado com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar perfil: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def alterar_senha(self):
        # Obter dados dos campos
        senha_atual = self.senha_atual_var.get()
        nova_senha = self.nova_senha_var.get()
        conf_nova_senha = self.conf_nova_senha_var.get()
        
        # Validar campos
        if not senha_atual or not nova_senha or not conf_nova_senha:
            messagebox.showwarning("Atenção", "Todos os campos de senha são obrigatórios.")
            return
        
        if nova_senha != conf_nova_senha:
            messagebox.showwarning("Atenção", "A nova senha e a confirmação não coincidem.")
            return
            
        if len(nova_senha) < 6:
            messagebox.showwarning("Atenção", "A nova senha deve ter pelo menos 6 caracteres.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Verificar senha atual
            cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (self.id_usuario_atual,))
            senha_hash_bd = cursor.fetchone()[0]
            
            if not self.verificar_senha(senha_atual, senha_hash_bd):
                messagebox.showerror("Erro", "Senha atual incorreta.")
                return
            
            # Atualizar a senha
            nova_senha_hash = self.hash_senha(nova_senha)
            cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", 
                          (nova_senha_hash, self.id_usuario_atual))
            
            conn.commit()
            
            # Limpar campos
            self.senha_atual_var.set("")
            self.nova_senha_var.set("")
            self.conf_nova_senha_var.set("")
            
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao alterar senha: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    # ================ TELA DE GERENCIAR USUÁRIOS (ADMIN) ================
    
    def mostrar_tela_gerenciar_usuarios(self):
        if self.perfil_usuario_atual != "admin":
            messagebox.showerror("Acesso Negado", "Você não tem permissão para acessar esta área.")
            return
            
        self.limpar_frame_conteudo()
        
        # Frame principal
        frame_usuarios = tk.Frame(self.frame_conteudo, bg="white", padx=30, pady=20)
        frame_usuarios.pack(fill=tk.BOTH, expand=True)
        
        # Título da página
        titulo = tk.Label(frame_usuarios, text="Gerenciar Usuários", 
                         font=("Calibri", 20, "bold"), bg="white", fg=self.cor_texto)
        titulo.pack(anchor=tk.W, pady=(0, 20))
        
        # Frame para filtros e pesquisa
        frame_filtros = tk.Frame(frame_usuarios, bg="white")
        frame_filtros.pack(fill=tk.X, pady=10)
        
        # Pesquisa
        tk.Label(frame_filtros, text="Pesquisar:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W)
        
        self.pesquisa_usuario_var = tk.StringVar()
        pesquisa_entry = tk.Entry(frame_filtros, textvariable=self.pesquisa_usuario_var, 
                                 font=self.fonte_texto, width=40)
        pesquisa_entry.grid(row=0, column=1, padx=(5, 20), sticky=tk.W)
        
        # Filtro por município
        tk.Label(frame_filtros, text="Município:", font=self.fonte_rotulo, 
                bg="white", fg=self.cor_texto).grid(row=0, column=2, sticky=tk.W)
        
        self.filtro_municipio_var = tk.StringVar()
        self.filtro_municipio_var.set("Todos")
        
        municipio_combo = ttk.Combobox(frame_filtros, textvariable=self.filtro_municipio_var, 
                                      font=self.fonte_texto, width=15, state="readonly")
        municipio_combo['values'] = ('Todos', 'Florianópolis', 'São José', 'Ambos')
        municipio_combo.grid(row=0, column=3, padx=(5, 20), sticky=tk.W)
        
        # Botão pesquisar
        btn_pesquisar = tk.Button(frame_filtros, text="Pesquisar", font=self.fonte_texto,
                                 bg="light gray", fg=self.cor_texto, padx=15, pady=2,
                                 command=self.filtrar_usuarios, cursor="hand2")
        btn_pesquisar.grid(row=0, column=4, padx=5)
        
        # Botão adicionar usuário
        btn_adicionar = tk.Button(frame_filtros, text="+ Adicionar Usuário", font=self.fonte_texto,
                                 bg="light gray", fg=self.cor_texto, padx=15, pady=2,
                                 command=self.mostrar_tela_adicionar_usuario, cursor="hand2")
        btn_adicionar.grid(row=0, column=5, padx=5)
        
        # Frame para a tabela
        frame_tabela = tk.Frame(frame_usuarios, bg="white")
        frame_tabela.pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Criar tabela usando Treeview
        colunas = ("nome", "email", "municipio", "departamento", "perfil", "ultimo_acesso")
        self.tabela_usuarios = ttk.Treeview(frame_tabela, columns=colunas, show="headings", 
                                          selectmode="browse", height=15)
        
        # Definir cabeçalhos
        self.tabela_usuarios.heading("nome", text="Nome")
        self.tabela_usuarios.heading("email", text="Email")
        self.tabela_usuarios.heading("municipio", text="Município")
        self.tabela_usuarios.heading("departamento", text="Departamento")
        self.tabela_usuarios.heading("perfil", text="Perfil")
        self.tabela_usuarios.heading("ultimo_acesso", text="Último Acesso")
        
        # Definir larguras das colunas
        self.tabela_usuarios.column("nome", width=200, minwidth=150)
        self.tabela_usuarios.column("email", width=200, minwidth=150)
        self.tabela_usuarios.column("municipio", width=100, minwidth=100)
        self.tabela_usuarios.column("departamento", width=150, minwidth=120)
        self.tabela_usuarios.column("perfil", width=80, minwidth=80)
        self.tabela_usuarios.column("ultimo_acesso", width=150, minwidth=120)
        
        # Scrollbar para a tabela
        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tabela_usuarios.yview)
        self.tabela_usuarios.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabela_usuarios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vincular evento de clique na tabela
        self.tabela_usuarios.bind("<Double-1>", self.editar_usuario_selecionado)
        
        # Carregar dados na tabela
        self.filtrar_usuarios()
        
        # Frame para botões de ação
        frame_acoes = tk.Frame(frame_usuarios, bg="white")
        frame_acoes.pack(fill=tk.X, pady=10)
        
        # Botões de ação
        btn_editar = tk.Button(frame_acoes, text="Editar", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=lambda: self.editar_usuario_selecionado(None), cursor="hand2")
        btn_editar.pack(side=tk.LEFT, padx=5)
        
        btn_resetar = tk.Button(frame_acoes, text="Resetar Senha", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=self.resetar_senha_usuario, cursor="hand2")
        btn_resetar.pack(side=tk.LEFT, padx=5)
        
        btn_excluir = tk.Button(frame_acoes, text="Excluir", font=self.fonte_texto,
                              bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                              command=self.excluir_usuario_selecionado, cursor="hand2")
        btn_excluir.pack(side=tk.LEFT, padx=5)
        
        # Informações
        info_total = tk.Label(frame_usuarios, text=f"Total de usuários: {self.contar_usuarios()}", 
                             font=("Calibri", 11), bg="white", fg=self.cor_texto)
        info_total.pack(side=tk.RIGHT, pady=10)
    
    def filtrar_usuarios(self):
        # Limpar tabela
        for item in self.tabela_usuarios.get_children():
            self.tabela_usuarios.delete(item)
        
        # Obter filtros
        pesquisa = self.pesquisa_usuario_var.get().strip().lower()
        municipio_filtro = self.filtro_municipio_var.get()
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Construir consulta SQL base
            sql = "SELECT id, nome, email, municipio, departamento, perfil, ultimo_acesso FROM usuarios"
            params = []
            
            # Lista de condições
            condicoes = []
            
            # Adicionar filtro de município
            if municipio_filtro != "Todos":
                condicoes.append("municipio = ?")
                params.append(municipio_filtro)
            
            # Adicionar filtro de pesquisa
            if pesquisa:
                condicoes.append("""(
                    lower(nome) LIKE ? OR 
                    lower(email) LIKE ? OR 
                    lower(departamento) LIKE ?
                )""")
                termo_busca = f"%{pesquisa}%"
                params.extend([termo_busca, termo_busca, termo_busca])
            
            # Adicionar condições à consulta
            if condicoes:
                sql += " WHERE " + " AND ".join(condicoes)
            
            # Ordenar por nome
            sql += " ORDER BY nome"
            
            cursor.execute(sql, params)
            resultado = cursor.fetchall()
            
            # Preencher a tabela com os resultados
            for row in resultado:
                usuario_id = row[0]
                nome = row[1]
                email = row[2]
                municipio = row[3]
                departamento = row[4] or ""
                
                # Formatar o tipo de perfil
                perfil_bd = row[5]
                perfil_texto = "Admin" if perfil_bd == "admin" else "Usuário"
                
                # Formatar data do último acesso
                ultimo_acesso = row[6]
                if ultimo_acesso:
                    data_acesso = datetime.strptime(ultimo_acesso, "%Y-%m-%d %H:%M:%S")
                    ultimo_acesso_formatado = data_acesso.strftime("%d/%m/%Y %H:%M")
                else:
                    ultimo_acesso_formatado = "Nunca acessou"
                
                # Inserir na tabela
                self.tabela_usuarios.insert("", tk.END, iid=usuario_id, values=(
                    nome, email, municipio, departamento, perfil_texto, ultimo_acesso_formatado
                ))
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def contar_usuarios(self):
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            resultado = cursor.fetchone()[0]
            return resultado
        except Exception as e:
            print(f"Erro ao contar usuários: {str(e)}")
            return 0
        finally:
            if 'conn' in locals():
                conn.close()
    
    def mostrar_tela_adicionar_usuario(self, usuario_id=None):
        # Criar uma janela modal
        janela = tk.Toplevel(self.root)
        janela.title("Adicionar Usuário" if not usuario_id else "Editar Usuário")
        janela.geometry("500x500")
        janela.configure(bg=self.cor_bg)
        janela.grab_set()  # Torna a janela modal
        
        # Frame principal
        frame_form = tk.Frame(janela, bg=self.cor_bg, padx=20, pady=20)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(frame_form, text="Adicionar Novo Usuário" if not usuario_id else "Editar Usuário", 
                         font=("Calibri", 16, "bold"), bg=self.cor_bg, fg=self.cor_primaria)
        titulo.pack(pady=(0, 20))
        
        # Dados do usuário para edição
        dados_usuario = None
        if usuario_id:
            dados_usuario = self.obter_dados_usuario_por_id(usuario_id)
            
        # Campos do formulário
        frame_campos = tk.Frame(frame_form, bg=self.cor_bg)
        frame_campos.pack(fill=tk.X, padx=20)
        
        # Nome
        tk.Label(frame_campos, text="Nome completo:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        self.add_nome_var = tk.StringVar()
        if dados_usuario:
            self.add_nome_var.set(dados_usuario['nome'])
            
        tk.Entry(frame_campos, textvariable=self.add_nome_var, 
                font=self.fonte_texto, width=30).grid(row=0, column=1, sticky=tk.W)
        
        # Email
        tk.Label(frame_campos, text="Email:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.add_email_var = tk.StringVar()
        if dados_usuario:
            self.add_email_var.set(dados_usuario['email'])
            
        email_entry = tk.Entry(frame_campos, textvariable=self.add_email_var, 
                             font=self.fonte_texto, width=30)
        email_entry.grid(row=1, column=1, sticky=tk.W)
        
        # Desabilitar email se estiver editando
        if dados_usuario:
            email_entry.configure(state="disabled")
            
        # Município
        tk.Label(frame_campos, text="Município:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        self.add_municipio_var = tk.StringVar()
        if dados_usuario:
            self.add_municipio_var.set(dados_usuario['municipio'])
        else:
            self.add_municipio_var.set("Florianópolis")
            
        municipio_combo = ttk.Combobox(frame_campos, textvariable=self.add_municipio_var, 
                                      font=self.fonte_texto, width=28, state="readonly")
        municipio_combo['values'] = ('Florianópolis', 'São José', 'Ambos')
        municipio_combo.grid(row=2, column=1, sticky=tk.W)
        
        # Departamento
        tk.Label(frame_campos, text="Departamento:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=3, column=0, sticky=tk.W, pady=10)
        
        self.add_departamento_var = tk.StringVar()
        if dados_usuario:
            self.add_departamento_var.set(dados_usuario['departamento'] or "")
            
        tk.Entry(frame_campos, textvariable=self.add_departamento_var, 
                font=self.fonte_texto, width=30).grid(row=3, column=1, sticky=tk.W)
        
        # Cargo
        tk.Label(frame_campos, text="Cargo:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=4, column=0, sticky=tk.W, pady=10)
        
        self.add_cargo_var = tk.StringVar()
        if dados_usuario:
            self.add_cargo_var.set(dados_usuario['cargo'] or "")
            
        tk.Entry(frame_campos, textvariable=self.add_cargo_var, 
                font=self.fonte_texto, width=30).grid(row=4, column=1, sticky=tk.W)
        
        # Perfil
        tk.Label(frame_campos, text="Perfil:", font=self.fonte_rotulo, 
                bg=self.cor_bg, fg=self.cor_texto).grid(row=5, column=0, sticky=tk.W, pady=10)
        
        self.add_perfil_var = tk.StringVar()
        if dados_usuario:
            self.add_perfil_var.set(dados_usuario['perfil'])
        else:
            self.add_perfil_var.set("usuario")
            
        perfil_frame = tk.Frame(frame_campos, bg=self.cor_bg)
        perfil_frame.grid(row=5, column=1, sticky=tk.W)
        
        rb_usuario = tk.Radiobutton(perfil_frame, text="Usuário", variable=self.add_perfil_var, 
                                   value="usuario", bg="light gray", font=self.fonte_texto)
        rb_usuario.pack(side=tk.LEFT, padx=(0, 20))
        
        rb_admin = tk.Radiobutton(perfil_frame, text="Administrador", variable=self.add_perfil_var, 
                                 value="admin", bg="light gray", font=self.fonte_texto)
        rb_admin.pack(side=tk.LEFT)
        
        # Senha (apenas para novo usuário)
        if not dados_usuario:
            tk.Label(frame_campos, text="Senha:", font=self.fonte_rotulo, 
                    bg=self.cor_bg, fg=self.cor_texto).grid(row=6, column=0, sticky=tk.W, pady=10)
            
            self.add_senha_var = tk.StringVar()
            tk.Entry(frame_campos, textvariable=self.add_senha_var, 
                    font=self.fonte_texto, width=30, show="•").grid(row=6, column=1, sticky=tk.W)
            
            tk.Label(frame_campos, text="Confirmar Senha:", font=self.fonte_rotulo, 
                    bg=self.cor_bg, fg=self.cor_texto).grid(row=7, column=0, sticky=tk.W, pady=10)
            
            self.add_conf_senha_var = tk.StringVar()
            tk.Entry(frame_campos, textvariable=self.add_conf_senha_var, 
                    font=self.fonte_texto, width=30, show="•").grid(row=7, column=1, sticky=tk.W)
        
        # Botões
        frame_botoes = tk.Frame(frame_form, bg=self.cor_bg, pady=20)
        frame_botoes.pack(fill=tk.X)
        
        btn_cancelar = tk.Button(frame_botoes, text="Cancelar", font=self.fonte_texto,
                               bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                               command=janela.destroy, cursor="hand2")
        btn_cancelar.pack(side=tk.LEFT, padx=5)
        
        if not dados_usuario:
            btn_salvar = tk.Button(frame_botoes, text="Adicionar Usuário", font=self.fonte_texto,
                                  bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                                  command=lambda: self.adicionar_usuario(janela), cursor="hand2")
        else:
            btn_salvar = tk.Button(frame_botoes, text="Salvar Alterações", font=self.fonte_texto,
                                   bg="light gray", fg=self.cor_texto, padx=15, pady=5,
                                  command=lambda: self.atualizar_usuario(janela, usuario_id), 
                                  cursor="hand2")
            
        btn_salvar.pack(side=tk.LEFT, padx=5)
    
    def obter_dados_usuario_por_id(self, usuario_id):
        try:
            conn = self.obter_conexao_banco()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                return dict(resultado)
            return None
            
        except Exception as e:
            print(f"Erro ao obter dados do usuário: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def adicionar_usuario(self, janela):
        # Obter dados dos campos
        nome = self.add_nome_var.get().strip()
        email = self.add_email_var.get().strip()
        municipio = self.add_municipio_var.get()
        departamento = self.add_departamento_var.get().strip()
        cargo = self.add_cargo_var.get().strip()
        perfil = self.add_perfil_var.get()
        senha = self.add_senha_var.get()
        conf_senha = self.add_conf_senha_var.get()
        
        # Validar campos obrigatórios
        if not nome or not email or not municipio or not senha:
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios.")
            return
        
        # Validar email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Atenção", "Digite um email válido.")
            return
        
        # Validar senhas
        if senha != conf_senha:
            messagebox.showwarning("Atenção", "As senhas não coincidem.")
            return
            
        if len(senha) < 6:
            messagebox.showwarning("Atenção", "A senha deve ter pelo menos 6 caracteres.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Verificar se o email já existe
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning("Atenção", "Este email já está cadastrado.")
                return
            
            # Inserir novo usuário
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            senha_hash = self.hash_senha(senha)
            
            cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, municipio, departamento, cargo, perfil, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, email, senha_hash, municipio, departamento, cargo, perfil, agora))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Usuário adicionado com sucesso!")
            
            janela.destroy()
            self.filtrar_usuarios()  # Atualizar a tabela
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar usuário: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def atualizar_usuario(self, janela, usuario_id):
        # Obter dados dos campos
        nome = self.add_nome_var.get().strip()
        municipio = self.add_municipio_var.get()
        departamento = self.add_departamento_var.get().strip()
        cargo = self.add_cargo_var.get().strip()
        perfil = self.add_perfil_var.get()
        
        # Validar campos obrigatórios
        if not nome or not municipio:
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Atualizar usuário
            cursor.execute('''
            UPDATE usuarios 
            SET nome = ?, municipio = ?, departamento = ?, cargo = ?, perfil = ?
            WHERE id = ?
            ''', (nome, municipio, departamento, cargo, perfil, usuario_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            
            janela.destroy()
            self.filtrar_usuarios()  # Atualizar a tabela
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar usuário: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def editar_usuario_selecionado(self, event):
        # Pegar o item selecionado
        selecionado = self.tabela_usuarios.selection()
        if not selecionado:
            if event:  # Se for chamado por um evento (clique)
                return
            messagebox.showwarning("Aviso", "Selecione um usuário para editar.")
            return
            
        usuario_id = selecionado[0]
        self.mostrar_tela_adicionar_usuario(usuario_id=usuario_id)
    
    def resetar_senha_usuario(self):
        # Pegar o item selecionado
        selecionado = self.tabela_usuarios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um usuário para resetar a senha.")
            return
            
        usuario_id = selecionado[0]
        
        # Confirmar reset
        if not messagebox.askyesno("Confirmar", 
                                  "Tem certeza que deseja resetar a senha deste usuário?"):
            return
        
        # Solicitar nova senha
        nova_senha = simpledialog.askstring("Nova Senha", 
                                         "Digite a nova senha para o usuário:", 
                                         show="*")
        
        if not nova_senha:
            return
            
        if len(nova_senha) < 6:
            messagebox.showwarning("Atenção", "A senha deve ter pelo menos 6 caracteres.")
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Atualizar senha
            senha_hash = self.hash_senha(nova_senha)
            cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", 
                          (senha_hash, usuario_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Senha resetada com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao resetar senha: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def excluir_usuario_selecionado(self):
        # Pegar o item selecionado
        selecionado = self.tabela_usuarios.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um usuário para excluir.")
            return
            
        usuario_id = selecionado[0]
        
        # Verificar se é o próprio usuário
        if int(usuario_id) == self.id_usuario_atual:
            messagebox.showwarning("Aviso", "Você não pode excluir seu próprio usuário.")
            return
        
        # Obter informações do usuário
        dados = self.obter_dados_usuario_por_id(usuario_id)
        if not dados:
            return
            
        # Verificar se é o administrador padrão
        if dados['email'] == "admin@sistema.gov.br":
            messagebox.showwarning("Aviso", "Não é possível excluir o administrador padrão do sistema.")
            return
        
        # Confirmar exclusão
        if not messagebox.askyesno("Confirmar Exclusão", 
                             f"Tem certeza que deseja excluir o usuário {dados['nome']}?\n\n" +
                             "Todos os ofícios criados por este usuário também serão excluídos.\n\n" +
                             "Esta ação não pode ser desfeita!"):
            return
        
        try:
            conn = self.obter_conexao_banco()
            cursor = conn.cursor()
            
            # Excluir ofícios do usuário
            cursor.execute("DELETE FROM oficios WHERE usuario_id = ?", (usuario_id,))
            
            # Excluir usuário
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Usuário {dados['nome']} excluído com sucesso!")
            
            # Atualizar a tabela
            self.filtrar_usuarios()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir usuário: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()


# ================ INICIALIZAÇÃO DA APLICAÇÃO ================

def main():
    try:
        root = tk.Tk()
        app = SistemaGeradorDeOficios(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"Erro fatal na inicialização:\n\n{str(e)}\n\nDetalhes técnicos:\n{traceback.format_exc()}"
        print(error_msg)
        
        # Tentar mostrar o erro em uma janela se possível
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("Erro Fatal", error_msg)
        except:
            pass

if __name__ == "__main__":
    main()

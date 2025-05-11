#!/usr/bin/env python3
"""
DocMaster Pro - Inicializador com Correção de Banco de Dados
Este script inicializa o DocMaster Pro, garantindo que o banco de dados
esteja corretamente configurado antes de iniciar o aplicativo Flask.
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
import socket
from pathlib import Path
import sqlite3
import importlib.util

def print_header(text):
    """Imprime um cabeçalho formatado"""
    print("\n" + "="*70)
    print(f"    {text}")
    print("="*70)

def print_status(message, success=None):
    """Imprime uma mensagem de status com formatação"""
    if success is None:
        print(message)
    elif success:
        print(f"{message} [OK]")
    else:
        print(f"{message} [ERRO]")

def find_available_port(start_port=5000):
    """Encontra uma porta disponível"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    return None

def initialize_database():
    """
    Inicializa o banco de dados diretamente usando SQLite,
    criando as tabelas necessárias pelo aplicativo.
    """
    print_status("Inicializando banco de dados...", None)
    
    # Determina o caminho do banco de dados
    instance_dir = Path("instance")
    db_path = instance_dir / "app.sqlite"
    
    # Cria o diretório instance se não existir
    instance_dir.mkdir(exist_ok=True)
    print_status("Diretório instance verificado", True)
    
    # Verifica se o banco de dados já existe
    if db_path.exists():
        try:
            # Tenta verificar se o banco já tem a tabela document
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document';")
            if cursor.fetchone():
                print_status("Tabela 'document' já existe no banco de dados", True)
                conn.close()
                return True
            conn.close()
            
            # Se chegou aqui, a tabela não existe, renomeia o banco existente
            backup_path = db_path.with_suffix('.sqlite.bak')
            os.rename(db_path, backup_path)
            print_status(f"Banco de dados atual movido para {backup_path}", True)
        except Exception as e:
            print_status(f"Erro ao verificar banco de dados: {e}", False)
            print_status("Tentando recriar o banco de dados...", None)
    
    # Cria o banco de dados e as tabelas
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Cria a tabela document
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            tags TEXT,
            processed BOOLEAN DEFAULT 0,
            file_hash TEXT,
            user_id INTEGER
        )
        ''')
        
        # Cria a tabela user
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP
        )
        ''')
        
        # Cria a tabela processed_document
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_document (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            text_content TEXT,
            metadata TEXT,
            processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES document (id)
        )
        ''')
        
        # Insere um usuário de teste para garantir que o sistema funcione
        try:
            cursor.execute('''
            INSERT INTO user (username, password, email, active)
            VALUES (?, ?, ?, ?)
            ''', ('admin', 'pbkdf2:sha256:150000$tOZ9akr7$d9de0e1c258f41fd0ad5a3a1162fb3538d4c3d6450412080bb41ed69da15a87c', 'admin@example.com', 1))
            print_status("Usuário de teste 'admin' criado (senha: 'admin')", True)
        except sqlite3.IntegrityError:
            print_status("Usuário 'admin' já existe", True)
        
        # Commit e fecha a conexão
        conn.commit()
        conn.close()
        
        print_status("Banco de dados inicializado", True)
        return True
    except Exception as e:
        print_status(f"Erro ao criar banco de dados: {e}", False)
        return False

def create_directories():
    """Cria os diretórios necessários para o aplicativo"""
    for dirname in ['uploads', 'processed', 'backups', 'logs', 'quarantine', 'instance']:
        os.makedirs(dirname, exist_ok=True)
        print_status(f"Diretório {dirname} verificado", True)

def setup_env_file():
    """Configura o arquivo .env se necessário"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        try:
            with open(env_example, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
            
            with open(env_file, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
            
            print_status("Arquivo .env criado a partir do .env.example", True)
        except Exception as e:
            print_status(f"Erro ao criar arquivo .env: {e}", False)

def run_flask_app():
    """Executa o aplicativo Flask"""
    # Configura o ambiente
    create_directories()
    setup_env_file()
    
    # Inicializa o banco de dados
    if not initialize_database():
        print_status("Falha ao inicializar o banco de dados. O aplicativo pode não funcionar corretamente.", False)
        cont = input("Deseja continuar mesmo assim? (s/n): ").lower()
        if cont != 's':
            return
    
    # Encontra uma porta disponível
    port = find_available_port()
    if not port:
        print_status("Nenhuma porta disponível encontrada!", False)
        input("Pressione Enter para sair...")
        return
    
    # URL da aplicação
    url = f"http://127.0.0.1:{port}"
    print_status(f"Iniciando DocMaster Pro em {url}", None)
    
    # Abre o navegador
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Configura variáveis de ambiente
    os.environ['FLASK_APP'] = 'app.py'
    
    # Tenta importar e executar o aplicativo Flask
    try:
        # Importa o módulo app
        import app as app_module
        
        # Tenta encontrar o aplicativo Flask
        if hasattr(app_module, 'app'):
            # Caso comum: app é uma variável global
            app = getattr(app_module, 'app')
            print_status("Aplicativo Flask encontrado como 'app'", True)
            app.run(host='127.0.0.1', port=port)
        elif hasattr(app_module, 'create_app'):
            # Caso factory: há uma função create_app()
            print_status("Encontrada função create_app()", True)
            app = app_module.create_app()
            app.run(host='127.0.0.1', port=port)
        else:
            # Não encontrou o aplicativo de forma conhecida
            print_status("Estrutura de aplicativo Flask não reconhecida", False)
            # Vamos criar um aplicativo Flask básico para mostrar um erro informativo
            from flask import Flask, render_template_string
            app = Flask(__name__)
            @app.route('/')
            def home():
                return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>DocMaster Pro - Erro</title>
                    <style>
                        body { font-family: Arial; margin: 40px; line-height: 1.6; }
                        h1 { color: #d9534f; }
                        .error { background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; }
                    </style>
                </head>
                <body>
                    <h1>DocMaster Pro - Erro de Inicialização</h1>
                    <div class="error">
                        <p>Não foi possível encontrar o aplicativo Flask no módulo app.py</p>
                        <p>O aplicativo deve estar disponível como uma variável global 'app' ou através de uma função 'create_app()'</p>
                    </div>
                </body>
                </html>
                """)
            app.run(host='127.0.0.1', port=port)
    except Exception as e:
        print_status(f"Erro ao executar aplicação: {e}", False)
        input("Pressione Enter para sair...")

def fix_and_run():
    """
    Função especial para resolver problemas comuns 
    antes de executar o aplicativo
    """
    print_header("REPARAÇÃO E EXECUÇÃO DO DOCMASTER PRO")
    
    # Verifica se o aplicativo está presente
    if not os.path.exists('app.py'):
        print_status("O arquivo app.py não foi encontrado!", False)
        print("Este arquivo é essencial para o funcionamento do DocMaster Pro.")
        input("\nPressione Enter para sair...")
        return
    
    # Verifica estrutura do banco de dados
    instance_dir = Path("instance")
    db_path = instance_dir / "app.sqlite"
    
    if db_path.exists():
        print_status(f"Banco de dados encontrado em {db_path}", True)
        
        # Verifica se o banco tem problemas
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verifica se a tabela document existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document';")
            if not cursor.fetchone():
                print_status("A tabela 'document' não existe no banco de dados", False)
                conn.close()
                
                # Perguntar se deve recriar o banco
                recreate = input("Deseja recriar o banco de dados? (s/n): ").lower()
                if recreate == 's':
                    # Faz backup e recria
                    backup_path = db_path.with_suffix('.sqlite.bak')
                    os.rename(db_path, backup_path)
                    print_status(f"Backup do banco de dados criado em {backup_path}", True)
                    
                    # Inicializa o banco
                    initialize_database()
                else:
                    print_status("Operação cancelada. O aplicativo pode não funcionar corretamente.", False)
            else:
                print_status("Estrutura do banco de dados verificada", True)
                conn.close()
        except Exception as e:
            print_status(f"Erro ao verificar banco de dados: {e}", False)
            
            # Perguntar se deve recriar o banco
            recreate = input("Deseja recriar o banco de dados? (s/n): ").lower()
            if recreate == 's':
                # Faz backup se possível
                try:
                    backup_path = db_path.with_suffix('.sqlite.bak')
                    os.rename(db_path, backup_path)
                    print_status(f"Backup do banco de dados criado em {backup_path}", True)
                except:
                    pass
                
                # Inicializa o banco
                initialize_database()
            else:
                print_status("Operação cancelada. O aplicativo pode não funcionar corretamente.", False)
    else:
        print_status("Banco de dados não encontrado, será criado automaticamente", True)
        # Inicializa o banco
        initialize_database()
    
    # Executa o aplicativo
    print("\nIniciando o aplicativo...")
    run_flask_app()

def main():
    """Função principal"""
    print_header("DOCMASTER PRO - UTILITÁRIO DE MANUTENÇÃO")
    
    print("Escolha uma opção:")
    print("1. Executar o aplicativo normalmente")
    print("2. Corrigir problemas e executar")
    print("3. Reinicializar o banco de dados")
    print("0. Sair")
    
    try:
        option = input("\nDigite o número da opção desejada: ")
        
        if option == '1':
            run_flask_app()
        elif option == '2':
            fix_and_run()
        elif option == '3':
            initialize_database()
            input("\nBanco de dados inicializado. Pressione Enter para sair...")
        else:
            print("\nSaindo. Até mais!")
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
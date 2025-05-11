#!/usr/bin/env python3
"""
DocMaster Pro - Instalador e Executor com Inicialização de Banco de Dados
Este script automatiza a instalação de dependências, configuração do ambiente,
inicialização do banco de dados e execução do sistema DocMaster Pro.
"""

import os
import sys
import subprocess
import platform
import shutil
import webbrowser
import time
import socket
from pathlib import Path
import tempfile
import importlib
import sqlite3

# Marca para verificar se estamos executando como executável
IS_FROZEN = getattr(sys, 'frozen', False)

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
    Inicializa o banco de dados SQLite, criando as tabelas necessárias.
    Isso resolve o erro 'no such table: document'
    """
    print_status("Inicializando banco de dados...", None)
    
    # Determina o caminho do banco de dados
    db_path = os.path.join("instance", "app.sqlite")
    
    # Cria o diretório instance se não existir
    os.makedirs("instance", exist_ok=True)
    
    # Backup do banco existente (se houver)
    if os.path.exists(db_path):
        backup_path = f"{db_path}.bak"
        shutil.copy2(db_path, backup_path)
        print_status(f"Backup do banco de dados criado em {backup_path}", True)
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela document se não existir
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
    
    # Cria a tabela user se não existir
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
    
    # Cria outras tabelas necessárias
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
    
    # Commit e fecha a conexão
    conn.commit()
    conn.close()
    
    print_status("Banco de dados inicializado", True)

def run_flask_app():
    """
    Executa o aplicativo Flask diretamente, usado quando estamos
    rodando como executável ou para testes.
    """
    # Adiciona o diretório atual ao PATH
    base_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(base_dir))
    
    # Configura variáveis de ambiente para Flask
    os.environ['FLASK_APP'] = 'app.py'
    
    # Cria diretórios necessários
    for dirname in ['uploads', 'processed', 'backups', 'logs', 'quarantine', 'instance']:
        os.makedirs(dirname, exist_ok=True)
    
    # Se tiver um .env.example, mas não tiver .env, cria .env
    env_file = Path('.env')
    env_example = Path('.env.example')
    if not env_file.exists() and env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print_status("Arquivo .env criado a partir do .env.example", True)
        except Exception as e:
            print_status(f"Não foi possível criar o arquivo .env: {e}", False)
    
    # Inicializa o banco de dados
    initialize_database()
    
    # Encontra uma porta disponível
    port = find_available_port()
    if not port:
        print_status("Nenhuma porta disponível encontrada!", False)
        input("Pressione Enter para sair...")
        return
    
    # URL da aplicação
    url = f"http://127.0.0.1:{port}"
    print_status(f"Iniciando DocMaster Pro em {url}")
    
    # Abre o navegador
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
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
            from flask import Flask
            app = Flask(__name__)
            @app.route('/')
            def home():
                return """
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
                """
            app.run(host='127.0.0.1', port=port)
    except Exception as e:
        print_status(f"Erro ao executar aplicação: {e}", False)
        input("Pressione Enter para sair...")

def create_executable():
    """
    Cria um executável standalone a partir do app.py usando PyInstaller.
    Não requer nenhum outro script além deste run.py.
    """
    print_header("CRIADOR DE EXECUTÁVEL DOCMASTER PRO")
    
    print("Este script irá criar um executável standalone do DocMaster Pro.")
    print("O executável incluirá o Python e todas as dependências necessárias.")
    print("Não é necessário que o usuário final tenha o Python instalado.\n")
    
    # Verifica requisitos
    print("Verificando requisitos...")
    
    # Verifica se app.py existe
    if not os.path.exists("app.py"):
        print_status("O arquivo app.py não foi encontrado!", False)
        print("Este arquivo é essencial para o funcionamento do DocMaster Pro.")
        input("\nPressione Enter para sair...")
        return
    
    print_status("app.py encontrado", True)
    
    # Verifica diretórios importantes
    missing = []
    for dir_name in ["templates", "static"]:
        if not os.path.exists(dir_name):
            missing.append(dir_name)
    
    if missing:
        print_status(f"As seguintes pastas estão faltando: {', '.join(missing)}", False)
        print("Estas pastas são importantes para o funcionamento adequado da aplicação.")
        cont = input("Deseja continuar mesmo assim? (s/n): ").lower()
        if cont != 's':
            print("Operação cancelada.")
            return
    else:
        print_status("Diretórios templates e static encontrados", True)
    
    # Tenta reconhecer a estrutura do app.py
    try:
        import app as app_module
        
        flask_app_found = False
        
        # Verifica se o aplicativo Flask está presente e em que formato
        if hasattr(app_module, 'app'):
            from flask import Flask
            if isinstance(getattr(app_module, 'app'), Flask):
                print_status("Detectado aplicativo Flask como variável 'app'", True)
                flask_app_found = True
        
        if hasattr(app_module, 'create_app') and not flask_app_found:
            print_status("Detectada função 'create_app()' para criação do aplicativo", True)
            flask_app_found = True
        
        if not flask_app_found:
            print_status("AVISO: Estrutura do aplicativo Flask não reconhecida automaticamente", False)
            print("O executável tentará detectar a estrutura durante a execução.")
            cont = input("Deseja continuar mesmo assim? (s/n): ").lower()
            if cont != 's':
                print("Operação cancelada.")
                return
    except Exception as e:
        print_status(f"AVISO: Não foi possível analisar o app.py: {e}", False)
        cont = input("Deseja continuar mesmo assim? (s/n): ").lower()
        if cont != 's':
            print("Operação cancelada.")
            return
    
    # Pergunta ao usuário se deseja continuar
    print("\nTudo pronto para criar o executável.")
    print("Este processo pode levar alguns minutos dependendo do seu sistema.")
    cont = input("Deseja continuar? (s/n): ").lower()
    
    if cont != 's':
        print("Operação cancelada.")
        return
    
    # Instala o PyInstaller se necessário
    try:
        importlib.import_module('PyInstaller')
        print_status("PyInstaller já instalado", True)
    except ImportError:
        print_status("Instalando PyInstaller...", None)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print_status("PyInstaller instalado", True)
        except Exception as e:
            print_status(f"Erro ao instalar PyInstaller: {e}", False)
            input("\nPressione Enter para sair...")
            return
    
    print("\nIniciando criação do executável standalone...")
    print("Este processo pode levar alguns minutos...\n")
    
    # Cria um script para o bootstrap que será o ponto de entrada do executável
    # Este script será gerado temporariamente e utilizado pelo PyInstaller
    bootstrap_code = """
# Script de bootstrap para o DocMaster Pro
import os
import sys
import time
import webbrowser
import socket
import threading
import sqlite3
import shutil
from pathlib import Path

def find_available_port(start_port=5000):
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    return None

def initialize_database():
    \"\"\"
    Inicializa o banco de dados SQLite, criando as tabelas necessárias.
    Isso resolve o erro 'no such table: document'
    \"\"\"
    print("Inicializando banco de dados...")
    
    # Determina o caminho do banco de dados
    db_path = os.path.join("instance", "app.sqlite")
    
    # Cria o diretório instance se não existir
    os.makedirs("instance", exist_ok=True)
    
    # Backup do banco existente (se houver)
    if os.path.exists(db_path):
        backup_path = f"{db_path}.bak"
        shutil.copy2(db_path, backup_path)
        print(f"Backup do banco de dados criado em {backup_path} [OK]")
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela document se não existir
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
    
    # Cria a tabela user se não existir
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
    
    # Cria outras tabelas necessárias
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
    
    # Commit e fecha a conexão
    conn.commit()
    conn.close()
    
    print("Banco de dados inicializado [OK]")

def main():
    # Adiciona o diretório atual ao PATH
    base_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(base_dir))
    
    # Cria diretórios necessários
    for dirname in ['uploads', 'processed', 'backups', 'logs', 'quarantine', 'instance']:
        os.makedirs(os.path.join(base_dir, dirname), exist_ok=True)
        print(f"Diretório {dirname} verificado [OK]")
    
    # Se tiver um .env.example, mas não tiver .env, cria .env
    env_file = os.path.join(base_dir, ".env")
    env_example = os.path.join(base_dir, ".env.example")
    if not os.path.exists(env_file) and os.path.exists(env_example):
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("Arquivo .env criado a partir do .env.example [OK]")
        except Exception as e:
            print(f"Não foi possível criar o arquivo .env: {e}")
    
    # Inicializa o banco de dados
    initialize_database()
    
    # Porta para o servidor
    port = find_available_port()
    if not port:
        print("Erro: Nenhuma porta disponível encontrada!")
        input("Pressione Enter para sair...")
        return
    
    # URL da aplicação
    url = f"http://127.0.0.1:{port}"
    print(f"\\nIniciando DocMaster Pro em {url}")
    
    # Abre o navegador
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Configura variáveis de ambiente
    os.environ['FLASK_APP'] = 'app.py'
    
    # Tenta importar e executar o aplicativo Flask
    try:
        import app as app_module
        
        # Tenta encontrar o aplicativo Flask
        if hasattr(app_module, 'app'):
            # Caso comum: app é uma variável global
            app = getattr(app_module, 'app')
            print("Aplicativo Flask encontrado como 'app' [OK]")
            app.run(host='127.0.0.1', port=port)
        elif hasattr(app_module, 'create_app'):
            # Caso factory: há uma função create_app()
            print("Encontrada função create_app() [OK]")
            app = app_module.create_app()
            app.run(host='127.0.0.1', port=port)
        else:
            # Não encontrou o aplicativo de forma conhecida
            print("Estrutura de aplicativo Flask não reconhecida [ERRO]")
            # Vamos criar um aplicativo Flask básico para mostrar um erro informativo
            from flask import Flask
            app = Flask(__name__)
            @app.route('/')
            def home():
                return \"\"\"
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
                \"\"\"
            app.run(host='127.0.0.1', port=port)
    except Exception as e:
        print(f"Erro ao executar aplicação: {e}")
        
        # Em caso de erro, tenta criar um app de emergência
        try:
            from flask import Flask
            app = Flask(__name__)
            @app.route('/')
            def home():
                return f\"\"\"
                <!DOCTYPE html>
                <html>
                <head>
                    <title>DocMaster Pro - Erro</title>
                    <style>
                        body {{ font-family: Arial; margin: 40px; line-height: 1.6; }}
                        h1 {{ color: #d9534f; }}
                        .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; }}
                        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; }}
                    </style>
                </head>
                <body>
                    <h1>DocMaster Pro - Erro de Inicialização</h1>
                    <div class="error">
                        <p>Ocorreu um erro ao iniciar o aplicativo:</p>
                        <pre>{e}</pre>
                    </div>
                </body>
                </html>
                \"\"\"
            app.run(host='127.0.0.1', port=port)
        except Exception as e2:
            print(f"Erro fatal: {e2}")
            input("Pressione Enter para sair...")

if __name__ == "__main__":
    print("\\n" + "="*50)
    print("       DOCMASTER PRO")
    print("="*50 + "\\n")
    try:
        main()
    except Exception as e:
        print(f"Erro não tratado: {e}")
        input("\\nOcorreu um erro inesperado. Pressione Enter para sair...")
"""
    
    # Cria o arquivo bootstrap temporário
    bootstrap_file = os.path.join(tempfile.gettempdir(), "docmaster_bootstrap.py")
    with open(bootstrap_file, 'w', encoding='utf-8') as f:
        f.write(bootstrap_code)
    
    print_status(f"Script bootstrap criado em {bootstrap_file}", True)
    
    # Lista de recursos para incluir no executável
    data_files = []
    
    # Adiciona diretórios e arquivos importantes
    if os.path.exists('templates'):
        data_files.append(('templates', 'templates'))
    if os.path.exists('static'):
        data_files.append(('static', 'static'))
    if os.path.exists('utils'):
        data_files.append(('utils', 'utils'))
    if os.path.exists('.env.example'):
        data_files.append(('.env.example', '.'))
    if os.path.exists('app.py'):
        data_files.append(('app.py', '.'))
    
    # Adiciona outros arquivos Python ao executável
    for file in os.listdir('.'):
        if file.endswith('.py') and file != 'run.py' and not os.path.basename(bootstrap_file).startswith(file):
            if file not in [f[0] for f in data_files]:
                data_files.append((file, '.'))
    
    # Prepara os argumentos do PyInstaller
    pyinstaller_args = [
        '--name=DocMaster',
        '--onefile',
        '--console',
    ]
    
    # Adiciona o ícone, se existir
    icon_path = os.path.join('static', 'images', 'icon.ico')
    if os.path.exists(icon_path):
        pyinstaller_args.append(f'--icon={icon_path}')
    
    # Adiciona os arquivos de dados
    for src, dst in data_files:
        if os.name == 'nt':  # Windows
            pyinstaller_args.append(f'--add-data={src};{dst}')
        else:  # Linux/Mac
            pyinstaller_args.append(f'--add-data={src}:{dst}')
    
    # Adiciona módulos escondidos importantes
    hidden_imports = [
        'flask',
        'werkzeug',
        'jinja2',
        'itsdangerous',
        'click',
        'importlib',
        'sqlite3',
    ]
    
    try:
        # Se o usuário tiver flask_sqlalchemy instalado, adiciona como hidden import
        importlib.import_module('flask_sqlalchemy')
        hidden_imports.append('flask_sqlalchemy')
    except ImportError:
        pass
    
    # Adiciona outros módulos comuns
    for module in ['PIL', 'email', 'json', 'urllib', 'datetime', 'flask_cors', 'flask_limiter']:
        try:
            importlib.import_module(module)
            hidden_imports.append(module)
        except ImportError:
            pass
    
    # Adiciona os módulos escondidos aos argumentos
    for module in hidden_imports:
        pyinstaller_args.append(f'--hidden-import={module}')
    
    # Adiciona o arquivo bootstrap como ponto de entrada
    pyinstaller_args.append(bootstrap_file)
    
    # Exibe os argumentos
    print("\nExecutando PyInstaller com os seguintes argumentos:")
    for arg in pyinstaller_args:
        print(f"  {arg}")
    
    # Executa o PyInstaller
    try:
        from PyInstaller.__main__ import run as pyinstaller_run
        pyinstaller_run(pyinstaller_args)
        print("\n" + "="*50)
        print("Executável standalone criado com sucesso!")
        print("O arquivo está disponível em: dist/DocMaster.exe")
        print("="*50)
    except Exception as e:
        print_status(f"Erro ao executar PyInstaller: {e}", False)
        print("Tentando método alternativo...")
        
        # Método alternativo: usar subprocess
        try:
            cmd = [sys.executable, "-m", "PyInstaller"] + pyinstaller_args
            subprocess.run(cmd, check=True)
            print("\n" + "="*50)
            print("Executável standalone criado com sucesso!")
            print("O arquivo está disponível em: dist/DocMaster.exe")
            print("="*50)
        except Exception as e2:
            print_status(f"Erro ao criar executável: {e2}", False)
            input("\nPressione Enter para sair...")
            return
    
    # Limpa arquivos temporários
    try:
        os.remove(bootstrap_file)
    except:
        pass
    
    # Pergunta se o usuário quer executar o programa
    exe_path = os.path.join("dist", "DocMaster.exe")
    if not os.path.exists(exe_path) and os.name != 'nt':
        exe_path = os.path.join("dist", "DocMaster")
    
    if os.path.exists(exe_path):
        run_now = input("\nDeseja executar o DocMaster Pro agora? (s/n): ").lower()
        if run_now == 's':
            print_status("Iniciando DocMaster Pro...", None)
            try:
                if os.name == 'nt':  # Windows
                    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # Linux/Mac
                    subprocess.Popen([exe_path])
                print_status("DocMaster Pro iniciado!", True)
            except Exception as e:
                print_status(f"Erro ao iniciar o DocMaster Pro: {e}", False)
    else:
        print_status(f"AVISO: Executável não encontrado em {exe_path}", False)
        print("Verifique o diretório dist para localizar o executável.")
    
    print("\nProcesso concluído.")
    input("Pressione Enter para sair...")

def main():
    """Função principal do script"""
    if IS_FROZEN:
        # Se estamos rodando como um executável, inicia o aplicativo diretamente
        run_flask_app()
    else:
        # Caso contrário, oferece a opção de criar o executável ou executar o aplicativo
        print_header("DOCMASTER PRO - INSTALADOR E GERADOR DE EXECUTÁVEL")
        
        print("Escolha uma opção:")
        print("1. Criar executável standalone")
        print("2. Executar o aplicativo")
        print("3. Inicializar banco de dados")
        print("0. Sair")
        
        option = input("\nDigite o número da opção desejada: ")
        
        if option == '1':
            create_executable()
        elif option == '2':
            run_flask_app()
        elif option == '3':
            initialize_database()
            print("Banco de dados inicializado. Pressione Enter para sair...")
            input()
        else:
            print("\nSaindo. Até mais!")

if __name__ == "__main__":
    main()
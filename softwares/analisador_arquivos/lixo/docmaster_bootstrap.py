# Script bootstrap para DocMaster Pro
import os
import sys
import time
import webbrowser
import socket
import threading
import importlib.util
from pathlib import Path
import shutil

def find_available_port(start_port=5000):
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    return None

def main():
    # Adiciona o diretório atual ao PATH
    base_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(base_dir))
    
    # Configura variáveis de ambiente
    os.environ['FLASK_APP'] = 'app.py'
    
    # Se tiver um .env.example, mas não tiver .env, cria .env
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print("Arquivo .env criado a partir do .env.example [OK]")
        except Exception as e:
            print(f"Aviso: Não foi possível criar o arquivo .env: {e}")
    
    # Cria diretórios necessários
    for dirname in ['uploads', 'processed', 'backups', 'logs', 'quarantine']:
        os.makedirs(os.path.join(base_dir, dirname), exist_ok=True)
        print(f"Diretório {dirname} verificado [OK]")
    
    # Encontra uma porta disponível
    port = find_available_port()
    if not port:
        print("Erro: Nenhuma porta disponível encontrada!")
        input("Pressione Enter para sair...")
        return
    
    # Abre o navegador
    url = f"http://127.0.0.1:{port}"
    print(f"\nIniciando DocMaster Pro em {url}")
    
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Verifica se app.py existe
    app_path = os.path.join(base_dir, "app.py")
    if not os.path.exists(app_path):
        print(f"Erro: Arquivo app.py não encontrado")
        print(f"Procurando em: {app_path}")
        print("Verificando diretório atual...")
        
        # Lista todos os arquivos .py no diretório atual
        py_files = list(base_dir.glob("*.py"))
        if py_files:
            print(f"Arquivos Python encontrados: {', '.join(str(f.name) for f in py_files)}")
        else:
            print("Nenhum arquivo Python encontrado no diretório.")
            
        input("Pressione Enter para sair...")
        return
    
    # Importa e executa a aplicação Flask
    try:
        print("Tentando importar o módulo app...")
        
        # Método 1: Importação direta
        try:
            sys.path.append(str(base_dir))
            import app
            print("Módulo app importado com sucesso.")
            print("Iniciando servidor Flask...")
            app.create_app().run(port=port)
        except ImportError as e:
            print(f"Importação direta falhou: {e}")
            
            # Método 2: Importação via spec
            print("Tentando método alternativo de importação...")
            try:
                spec = importlib.util.spec_from_file_location("app", app_path)
                app_module = importlib.util.module_from_spec(spec)
                sys.modules["app"] = app_module
                spec.loader.exec_module(app_module)
                print("Módulo app carregado via importlib.")
                print("Iniciando servidor Flask...")
                app_module.create_app().run(port=port)
            except Exception as e2:
                print(f"Falha na importação alternativa: {e2}")
                
                # Método 3: Fallback para execução direta
                print("Tentando executar Flask diretamente...")
                try:
                    from flask import Flask
                    app = Flask(__name__)
                    
                    app.run(port=port)
                except Exception as e3:
                    print(f"Falha ao executar Flask diretamente: {e3}")
    except Exception as e:
        print(f"Erro ao iniciar a aplicação: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    try:
        print("\n" + "="*50)
        print("       DOCMASTER PRO")
        print("="*50 + "\n")
        main()
    except Exception as e:
        print(f"Erro não tratado: {e}")
        input("Pressione Enter para sair...")

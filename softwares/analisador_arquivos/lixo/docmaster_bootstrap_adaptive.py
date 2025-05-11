#!/usr/bin/env python3
"""
DocMaster Pro - Script de Inicialização Adaptativo
Este script serve como ponto de entrada para o executável do DocMaster Pro.
Ele detecta automaticamente a estrutura do aplicativo Flask e o inicia.
"""

import os
import sys
import time
import webbrowser
import socket
import threading
import importlib.util
from pathlib import Path
import inspect
import shutil

def find_available_port(start_port=5000):
    """Encontra uma porta disponível começando da porta especificada"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    return None

def print_status(message, status="INFO"):
    """Imprime mensagem de status com formatação apropriada"""
    status_colors = {
        "INFO": "",
        "OK": "[OK]",
        "ERROR": "[ERRO]",
        "WARNING": "[AVISO]"
    }
    print(f"{message} {status_colors.get(status, '')}")

def setup_environment():
    """Configura o ambiente para a aplicação"""
    # Adiciona o diretório atual ao PATH
    base_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(base_dir))
    
    # Configura variáveis de ambiente para Flask
    os.environ['FLASK_APP'] = 'app.py'
    
    # Se tiver um .env.example, mas não tiver .env, cria .env
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print_status("Arquivo .env criado a partir do .env.example", "OK")
        except Exception as e:
            print_status(f"Não foi possível criar o arquivo .env: {e}", "WARNING")
    
    # Cria diretórios necessários
    for dirname in ['uploads', 'processed', 'backups', 'logs', 'quarantine']:
        os.makedirs(os.path.join(base_dir, dirname), exist_ok=True)
        print_status(f"Diretório {dirname} verificado", "OK")
    
    return base_dir

def detect_flask_app(module):
    """Detecta automaticamente a estrutura do aplicativo Flask"""
    # Procura por uma instância de Flask no módulo
    from flask import Flask
    
    # Caso 1: app = Flask(__name__)
    for name, obj in inspect.getmembers(module):
        if isinstance(obj, Flask):
            print_status(f"Aplicativo Flask encontrado como variável '{name}'", "OK")
            return obj
    
    # Caso 2: create_app() ou similar
    app_factory_names = ['create_app', 'make_app', 'get_app', 'setup_app', 'init_app']
    for factory_name in app_factory_names:
        if hasattr(module, factory_name):
            factory_func = getattr(module, factory_name)
            if callable(factory_func):
                print_status(f"Função de criação do aplicativo '{factory_name}()' encontrada", "OK")
                try:
                    # Tenta chamar sem argumentos
                    return factory_func()
                except TypeError:
                    # Pode precisar de argumentos, tenta com valores padrão comuns
                    try:
                        return factory_func('development')
                    except:
                        print_status(f"Não foi possível chamar {factory_name}() com argumentos padrão", "WARNING")
    
    # Caso 3: app está em um submódulo
    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj):
            submodule = obj
            for subname, subobj in inspect.getmembers(submodule):
                if isinstance(subobj, Flask):
                    print_status(f"Aplicativo Flask encontrado em submódulo: {name}.{subname}", "OK")
                    return subobj
    
    # Nenhum app encontrado
    return None

def fallback_app(error_message):
    """Cria um aplicativo Flask básico para fallback"""
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>DocMaster Pro - Modo de Emergência</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2563eb; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DocMaster Pro - Modo de Emergência</h1>
        <div class="error">
            <p><strong>Erro ao iniciar a aplicação:</strong> {error_message}</p>
        </div>
        <h3>Possíveis soluções:</h3>
        <ol>
            <li>Certifique-se de que o aplicativo Flask está configurado corretamente em app.py</li>
            <li>Verifique se o aplicativo é acessível como uma variável global 'app' ou através de uma função 'create_app()'</li>
            <li>Tente executar o aplicativo diretamente com 'python app.py' para verificar erros</li>
        </ol>
        <h3>Estrutura esperada do app.py:</h3>
        <pre>
from flask import Flask

# Opção 1: App como variável global
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, world!"

# Opção 2: Função factory
def create_app():
    app = Flask(__name__)
    return app
    
if __name__ == '__main__':
    app.run()
        </pre>
    </div>
</body>
</html>"""
    
    return app

def main():
    """Função principal que inicia a aplicação"""
    print("\n" + "="*50)
    print("       DOCMASTER PRO")
    print("="*50 + "\n")
    
    # Configura o ambiente
    base_dir = setup_environment()
    
    # Encontra uma porta disponível
    port = find_available_port()
    if not port:
        print_status("Nenhuma porta disponível encontrada!", "ERROR")
        input("Pressione Enter para sair...")
        return
    
    # URL da aplicação
    url = f"http://127.0.0.1:{port}"
    print_status(f"\nIniciando DocMaster Pro em {url}")
    
    # Abre o navegador após um pequeno delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Verifica se app.py existe
    app_path = base_dir / "app.py"
    if not app_path.exists():
        print_status(f"Arquivo app.py não encontrado em {base_dir}", "ERROR")
        from flask import Flask
        app = fallback_app("Arquivo app.py não encontrado")
        app.run(port=port, host='127.0.0.1')
        return
    
    # Tenta importar e executar o aplicativo Flask
    try:
        print_status("Tentando importar o módulo app...")
        
        # Método 1: Importação direta
        try:
            import app as app_module
            print_status("Módulo app importado com sucesso.", "OK")
            
            # Detecta a estrutura do aplicativo
            flask_app = detect_flask_app(app_module)
            
            if flask_app:
                print_status("Iniciando servidor Flask...", "OK")
                flask_app.run(port=port, host='127.0.0.1')
            else:
                # Tenta ver se há uma variável app no módulo
                if hasattr(app_module, 'app'):
                    app = getattr(app_module, 'app')
                    print_status("Aplicativo Flask encontrado como 'app'", "OK")
                    print_status("Iniciando servidor Flask...", "OK")
                    app.run(port=port, host='127.0.0.1')
                else:
                    # Último recurso: examina o módulo diretamente
                    print_status("Estrutura de aplicativo Flask não reconhecida", "WARNING")
                    print_status("Criando aplicativo de emergência...", "WARNING")
                    
                    # Mostra os membros do módulo para diagnóstico
                    print("\nMembros encontrados no módulo app:")
                    for name, obj in inspect.getmembers(app_module):
                        if not name.startswith('__'):
                            print(f" - {name}: {type(obj).__name__}")
                    
                    # Cria app de fallback
                    fallback = fallback_app("Estrutura de aplicativo Flask não reconhecida em app.py")
                    fallback.run(port=port, host='127.0.0.1')
        except ImportError as e:
            print_status(f"Erro ao importar o módulo app: {e}", "ERROR")
            
            # Método 2: Importação via spec
            try:
                print_status("Tentando método alternativo de importação...", "INFO")
                spec = importlib.util.spec_from_file_location("app", str(app_path))
                app_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_module)
                
                # Detecta a estrutura do aplicativo
                flask_app = detect_flask_app(app_module)
                
                if flask_app:
                    print_status("Iniciando servidor Flask...", "OK")
                    flask_app.run(port=port, host='127.0.0.1')
                else:
                    print_status("Não foi possível encontrar o aplicativo Flask no módulo", "ERROR")
                    fallback = fallback_app("Aplicativo Flask não encontrado no módulo importado")
                    fallback.run(port=port, host='127.0.0.1')
            except Exception as e2:
                print_status(f"Falha na importação alternativa: {e2}", "ERROR")
                fallback = fallback_app(f"Falha ao importar o módulo app: {e}\nFalha alternativa: {e2}")
                fallback.run(port=port, host='127.0.0.1')
    except Exception as e:
        print_status(f"Erro ao iniciar a aplicação: {e}", "ERROR")
        
        try:
            fallback = fallback_app(f"Erro ao iniciar a aplicação: {e}")
            fallback.run(port=port, host='127.0.0.1')
        except Exception as e_fallback:
            print_status(f"Falha ao iniciar aplicativo de emergência: {e_fallback}", "ERROR")
            input("Pressione Enter para sair...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro não tratado: {e}")
        input("\nOcorreu um erro inesperado. Pressione Enter para sair...")
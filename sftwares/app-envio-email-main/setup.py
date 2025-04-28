"""
Script para preparar o ambiente e criar um executável do Sistema de E-mails para Prefeituras.
Autor: LTD
Data: Abril 2025
"""

import os
import sys
import subprocess
import shutil
import platform

def print_header(message):
    """Imprime uma mensagem de cabeçalho formatada."""
    print("\n" + "=" * 60)
    print(message.center(60))
    print("=" * 60 + "\n")

def check_python():
    """Verifica se o Python está instalado corretamente."""
    print("Verificando instalação do Python...")
    try:
        python_version = platform.python_version()
        print(f"Python versão {python_version} encontrado.")
        
        # Verifica se a versão é adequada (>= 3.7)
        major, minor, _ = python_version.split('.')
        if int(major) < 3 or (int(major) == 3 and int(minor) < 7):
            print("AVISO: Recomendamos Python 3.7 ou superior.")
            return False
        return True
    except Exception as e:
        print(f"ERRO ao verificar Python: {e}")
        return False

def create_virtual_env():
    """Cria um ambiente virtual para o projeto."""
    print("Criando ambiente virtual...")
    if os.path.exists("venv"):
        print("Ambiente virtual já existe. Deseja recriá-lo? (s/n)")
        choice = input().lower()
        if choice == 's':
            try:
                shutil.rmtree("venv")
            except Exception as e:
                print(f"ERRO ao remover ambiente virtual existente: {e}")
                return False
        else:
            print("Usando ambiente virtual existente.")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Ambiente virtual criado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao criar ambiente virtual: {e}")
        return False

def activate_venv():
    """Ativa o ambiente virtual para os próximos comandos."""
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "python.exe")
    else:  # Unix/Linux/Mac
        return os.path.join("venv", "bin", "python")

def install_dependencies(venv_python):
    """Instala as dependências necessárias."""
    print("Instalando dependências...")
    try:
        # Atualizando pip
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Instalando pacotes do requirements.txt
        if os.path.exists("requirements.txt"):
            subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Dependências instaladas com sucesso.")
        else:
            print("Arquivo requirements.txt não encontrado. Criando...")
            with open("requirements.txt", "w") as f:
                f.write("""# Requirements para o Sistema de Envio de E-mails para Prefeituras
pillow>=9.0.0
pandas>=1.3.0
openpyxl>=3.0.9
tkcalendar>=1.6.1
schedule>=1.1.0
python-dateutil>=2.8.2
pytz>=2021.3
email-validator>=1.1.3
""")
            subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Dependências instaladas com sucesso.")
        
        # Instalando PyInstaller
        subprocess.run([venv_python, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller instalado com sucesso.")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao instalar dependências: {e}")
        return False

def create_directories():
    """Cria os diretórios necessários para o projeto."""
    print("Criando diretórios do projeto...")
    directories = ["resources", "templates", "config", "backups"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Diretório '{directory}' criado.")
        else:
            print(f"Diretório '{directory}' já existe.")
    
    # Cria um arquivo icon.ico vazio caso não exista
    if not os.path.exists(os.path.join("resources", "icon.ico")):
        try:
            from PIL import Image
            img = Image.new('RGB', (256, 256), color=(73, 109, 137))
            img.save(os.path.join("resources", "icon.ico"))
            print("Arquivo icon.ico criado como placeholder.")
        except Exception as e:
            print(f"AVISO: Não foi possível criar o arquivo icon.ico: {e}")
    
    return True

def create_run_file():
    """Cria o arquivo app.py para executar o sistema."""
    print("Criando arquivo app.py...")
    
    run_content = """#!/usr/bin/env python
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(run_content)
    
    print("Arquivo app.py criado com sucesso.")"""
    return True

def create_executable(venv_python):
    """Cria o executável usando PyInstaller."""
    print_header("Criando Executável com PyInstaller")
    
    try:
        cmd = [
            venv_python, "-m", "PyInstaller",
            "--name", "Sistema_Email_Prefeituras",
            "--onefile",
            "--windowed",
            "--icon=resources/icon.ico",
            "--add-data", f"resources{os.pathsep}resources",
            "--add-data", f"templates{os.pathsep}templates",
            "--add-data", f"config{os.pathsep}config",
            "app.py"
        ]
        
        subprocess.run(cmd, check=True)
        print("\nExecutável criado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nERRO ao criar executável: {e}")
        return False

def main():
    """Função principal do script de configuração."""
    print_header("Configuração do Sistema de E-mails para Prefeituras")
    
    # Verifica Python
    if not check_python():
        print("ERRO: Problemas com a instalação do Python.")
        return False
    
    # Cria ambiente virtual
    if not create_virtual_env():
        print("ERRO: Falha ao criar ambiente virtual.")
        return False
    
    # Obtém o caminho para o Python do ambiente virtual
    venv_python = activate_venv()
    
    # Instala dependências
    if not install_dependencies(venv_python):
        print("ERRO: Falha ao instalar dependências.")
        return False
    
    # Cria diretórios
    if not create_directories():
        print("ERRO: Falha ao criar diretórios.")
        return False
    
    # Cria arquivo app.py
    if not create_run_file():
        print("ERRO: Falha ao criar arquivo app.py.")
        return False
    
    # Cria executável
    if not create_executable(venv_python):
        print("ERRO: Falha ao criar executável.")
        return False
    
    print_header("Processo Concluído com Sucesso!")
    print("""
O executável foi criado em: dist/Sistema_Email_Prefeituras.exe

Para distribuir o programa:
1. Copie o arquivo 'Sistema_Email_Prefeituras.exe' da pasta 'dist'
2. Crie as pastas 'resources', 'templates', 'config' e 'backups' no mesmo
   diretório onde você colocar o executável.

Se preferir testar antes de criar o executável, você pode executar:
- venv\\Scripts\\python app.py (no Windows)
- venv/bin/python app.py (no Linux/Mac)
""")
    
    return True

if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...")
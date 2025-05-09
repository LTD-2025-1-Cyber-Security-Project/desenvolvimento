#!/usr/bin/env python3
"""
Script de inicialização do Sistema Gerador de Ofícios.
Este script configura o ambiente virtual, instala as dependências necessárias
e executa a aplicação automaticamente.
"""

import os
import sys
import platform
import subprocess
import time

# Cores para mensagens no terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    """Imprime uma mensagem de etapa formatada no terminal."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}==>{Colors.ENDC} {message}")

def print_error(message):
    """Imprime uma mensagem de erro formatada no terminal."""
    print(f"\n{Colors.FAIL}{Colors.BOLD}ERRO:{Colors.ENDC} {message}")

def print_success(message):
    """Imprime uma mensagem de sucesso formatada no terminal."""
    print(f"\n{Colors.GREEN}{Colors.BOLD}SUCESSO:{Colors.ENDC} {message}")

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    required_version = (3, 8)
    current_version = sys.version_info

    if current_version < required_version:
        print_error(f"Python {required_version[0]}.{required_version[1]} ou superior é necessário.")
        print(f"Sua versão atual é {current_version[0]}.{current_version[1]}.{current_version[2]}")
        sys.exit(1)

def run_command(command, shell=False):
    """Executa um comando de shell e exibe o resultado."""
    try:
        if shell:
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        else:
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        
        # Captura saída em tempo real
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Captura erros
        stderr = process.stderr.read()
        if stderr:
            print(stderr)
        
        # Retorna o código de saída do processo
        return process.poll()
    except Exception as e:
        print_error(f"Erro ao executar o comando: {e}")
        return 1

def create_virtual_env():
    """Cria e ativa o ambiente virtual."""
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    
    # Verificar se o ambiente virtual já existe
    if os.path.exists(venv_path):
        print_step("Ambiente virtual já existe. Verificando dependências...")
        return venv_path
    
    print_step("Criando ambiente virtual...")
    
    # Criar ambiente virtual
    result = run_command([sys.executable, "-m", "venv", "venv"])
    if result != 0:
        print_error("Falha ao criar ambiente virtual.")
        sys.exit(1)
    
    return venv_path

def get_venv_paths(venv_path):
    """Obtém os caminhos do ambiente virtual de acordo com o sistema operacional."""
    system = platform.system()
    
    if system == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        activate_path = os.path.join(venv_path, "Scripts", "activate")
    else:  # Linux/MacOS
        python_path = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")
        activate_path = os.path.join(venv_path, "bin", "activate")
    
    return python_path, pip_path, activate_path

def install_dependencies(pip_path):
    """Instala as dependências do projeto."""
    print_step("Instalando dependências...")
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print_error("Arquivo requirements.txt não encontrado.")
        sys.exit(1)
    
    # Atualizar pip primeiro
    run_command([pip_path, "install", "--upgrade", "pip"])
    
    # Instalar dependências
    result = run_command([pip_path, "install", "-r", requirements_path])
    if result != 0:
        print_error("Falha ao instalar dependências.")
        sys.exit(1)

def run_application(python_path):
    """Executa a aplicação principal."""
    print_step("Iniciando o Sistema Gerador de Ofícios...")
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    if not os.path.exists(app_path):
        print_error("Arquivo app.py não encontrado.")
        sys.exit(1)
    
    # Executar a aplicação
    print("\n" + "="*60)
    print(f"{Colors.GREEN}{Colors.BOLD}SISTEMA GERADOR DE OFÍCIOS - INICIANDO{Colors.ENDC}")
    print("="*60 + "\n")
    
    time.sleep(1)  # Pequena pausa para melhor visualização
    
    # No Windows, é melhor executar um comando direto
    # Em sistemas Unix, usamos o activate para garantir que estamos no ambiente certo
    system = platform.system()
    if system == "Windows":
        run_command([python_path, app_path])
    else:
        run_command(f'source "{os.path.dirname(python_path)}/activate" && "{python_path}" "{app_path}"', shell=True)

def check_dependencies():
    """Verifica se há dependências do sistema que precisam ser instaladas."""
    system = platform.system()
    
    if system == "Linux":
        # Verificar se o Tk está instalado no Linux
        print_step("Verificando dependências do sistema...")
        try:
            import tkinter
        except ImportError:
            print_error("O Tkinter não está instalado no seu sistema.")
            print("\nEm distribuições baseadas em Debian/Ubuntu, instale com:")
            print("  sudo apt-get install python3-tk")
            print("\nEm distribuições baseadas em Red Hat/Fedora, instale com:")
            print("  sudo dnf install python3-tkinter")
            sys.exit(1)
    
    elif system == "Darwin":  # MacOS
        # No MacOS, verificamos se o Python tem o Tkinter disponível
        try:
            import tkinter
        except ImportError:
            print_error("O Tkinter não está disponível na sua instalação do Python.")
            print("\nInstale o Python com Tkinter usando Homebrew:")
            print("  brew install python-tk")
            sys.exit(1)

def main():
    """Função principal que coordena todo o processo."""
    # Exibir banner
    print("\n" + "="*60)
    print(f"{Colors.HEADER}{Colors.BOLD}SISTEMA GERADOR DE OFÍCIOS - CONFIGURAÇÃO{Colors.ENDC}")
    print("="*60)
    
    # Verificar versão do Python
    print_step("Verificando versão do Python...")
    check_python_version()
    
    # Verificar dependências do sistema
    check_dependencies()
    
    # Criar ambiente virtual
    venv_path = create_virtual_env()
    python_path, pip_path, activate_path = get_venv_paths(venv_path)
    
    # Instalar dependências
    install_dependencies(pip_path)
    
    # Executar aplicação
    print_success("Configuração concluída com sucesso!")
    run_application(python_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Um erro inesperado ocorreu: {e}")
        sys.exit(1)
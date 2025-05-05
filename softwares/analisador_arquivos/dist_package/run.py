#!/usr/bin/env python3
"""
DocMaster Pro - Instalador e Executor Automático
Este script automatiza a instalação de dependências, configuração do ambiente
e execução do sistema DocMaster Pro.
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
import json
import venv
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('installation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DocMasterInstaller:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.base_dir / "venv"
        self.requirements_file = self.base_dir / "requirements.txt"
        self.env_file = self.base_dir / ".env"
        self.env_example = self.base_dir / ".env.example"
        self.app_file = self.base_dir / "app.py"
        self.os_type = platform.system().lower()
        self.python_cmd = sys.executable
        
    def print_banner(self):
        """Exibe o banner do instalador"""
        banner = """
        ╔══════════════════════════════════════════════════════════╗
        ║                    DocMaster Pro                         ║
        ║        Sistema Inteligente de Processamento              ║
        ║                  de Documentos                           ║
        ╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
        logging.info("Iniciando instalação do DocMaster Pro")

    def check_python_version(self):
        """Verifica se a versão do Python é compatível"""
        logging.info("Verificando versão do Python...")
        if sys.version_info < (3, 9):
            logging.error("Python 3.9 ou superior é necessário!")
            sys.exit(1)
        logging.info(f"Python {sys.version} detectado ✓")

    def create_virtual_environment(self):
        """Cria um ambiente virtual"""
        if not self.venv_dir.exists():
            logging.info("Criando ambiente virtual...")
            venv.create(self.venv_dir, with_pip=True)
            logging.info("Ambiente virtual criado ✓")
        else:
            logging.info("Ambiente virtual já existe ✓")

    def get_pip_executable(self):
        """Retorna o caminho do pip no ambiente virtual"""
        if self.os_type == "windows":
            return self.venv_dir / "Scripts" / "pip.exe"
        return self.venv_dir / "bin" / "pip"

    def get_python_executable(self):
        """Retorna o caminho do python no ambiente virtual"""
        if self.os_type == "windows":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def install_dependencies(self):
        """Instala as dependências do projeto"""
        logging.info("Instalando dependências...")
        pip_exe = self.get_pip_executable()
        
        # Atualiza o pip
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], check=True)
        
        # Instala as dependências
        if self.requirements_file.exists():
            subprocess.run([str(pip_exe), "install", "-r", str(self.requirements_file)], check=True)
            logging.info("Dependências instaladas ✓")
        else:
            logging.error("Arquivo requirements.txt não encontrado!")
            sys.exit(1)

    def install_system_dependencies(self):
        """Instala dependências do sistema operacional"""
        logging.info("Verificando dependências do sistema...")
        
        if self.os_type == "darwin":  # macOS
            if shutil.which("brew"):
                logging.info("Instalando dependências via Homebrew...")
                subprocess.run(["brew", "install", "tesseract"], check=False)
                subprocess.run(["brew", "install", "poppler"], check=False)
            else:
                logging.warning("Homebrew não encontrado. Por favor, instale Tesseract manualmente.")
                
        elif self.os_type == "linux":
            if shutil.which("apt-get"):
                logging.info("Instalando dependências via apt-get...")
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-por", "poppler-utils"], check=False)
            else:
                logging.warning("apt-get não encontrado. Por favor, instale Tesseract manualmente.")
                
        elif self.os_type == "windows":
            logging.warning("""
            Por favor, instale manualmente:
            1. Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
            2. Poppler: https://github.com/oschwartz10612/poppler-windows
            """)

    def setup_environment(self):
        """Configura o arquivo .env"""
        if not self.env_file.exists() and self.env_example.exists():
            logging.info("Configurando arquivo .env...")
            shutil.copy(self.env_example, self.env_file)
            logging.info("Arquivo .env criado ✓")
            
            # Solicita a API key do Google
            print("\n" + "="*50)
            print("CONFIGURAÇÃO DA API DO GOOGLE GEMINI")
            print("="*50)
            print("Para usar a análise com IA, você precisa de uma API key do Google Gemini.")
            print("1. Acesse: https://makersuite.google.com/app/apikey")
            print("2. Crie uma nova API key")
            print("3. Cole a chave abaixo ou deixe em branco para configurar depois")
            print("="*50)
            
            api_key = input("Digite sua API key do Google Gemini (opcional): ").strip()
            
            if api_key:
                with open(self.env_file, 'r') as f:
                    content = f.read()
                
                content = content.replace('your-google-ai-api-key-here', api_key)
                
                with open(self.env_file, 'w') as f:
                    f.write(content)
                
                logging.info("API key configurada ✓")
            else:
                logging.warning("API key não configurada. Análise com IA não estará disponível.")

    def create_directories(self):
        """Cria diretórios necessários"""
        directories = ['uploads', 'processed', 'backups', 'logs', 'quarantine']
        for directory in directories:
            dir_path = self.base_dir / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Diretório {directory} criado ✓")

    def initialize_database(self):
        """Inicializa o banco de dados"""
        logging.info("Inicializando banco de dados...")
        python_exe = self.get_python_executable()
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        
        result = subprocess.run(
            [str(python_exe), "-m", "flask", "init-db"],
            env=env,
            cwd=str(self.base_dir),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Banco de dados inicializado ✓")
        else:
            logging.error(f"Erro ao inicializar banco de dados: {result.stderr}")

    def check_port_availability(self, port=5000):
        """Verifica se a porta está disponível"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except socket.error:
                return False

    def find_available_port(self, start_port=5000):
        """Encontra uma porta disponível"""
        for port in range(start_port, start_port + 100):
            if self.check_port_availability(port):
                return port
        return None

    def run_application(self):
        """Executa a aplicação Flask"""
        port = self.find_available_port()
        if not port:
            logging.error("Nenhuma porta disponível encontrada!")
            sys.exit(1)
            
        logging.info(f"Iniciando aplicação na porta {port}...")
        
        python_exe = self.get_python_executable()
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        
        # Abre o navegador após um pequeno delay
        url = f"http://127.0.0.1:{port}"
        logging.info(f"Abrindo navegador em {url}")
        
        # Abre o navegador em uma thread separada
        import threading
        def open_browser():
            time.sleep(3)  # Aguarda o servidor iniciar
            webbrowser.open(url)
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Executa o Flask
        try:
            subprocess.run(
                [str(python_exe), "-m", "flask", "run", "--port", str(port)],
                env=env,
                cwd=str(self.base_dir)
            )
        except KeyboardInterrupt:
            logging.info("Aplicação encerrada pelo usuário")
        except Exception as e:
            logging.error(f"Erro ao executar aplicação: {e}")

    def create_executable(self):
        """Cria um executável com PyInstaller"""
        logging.info("Criando executável...")
        pip_exe = self.get_pip_executable()
        python_exe = self.get_python_executable()
        
        # Instala PyInstaller
        subprocess.run([str(pip_exe), "install", "pyinstaller"], check=True)
        
        # Cria o executável
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('utils', 'utils'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'flask_sqlalchemy',
        'flask_limiter',
        'werkzeug',
        'PyPDF2',
        'pdfminer',
        'docx',
        'openpyxl',
        'PIL',
        'pytesseract',
        'google.generativeai',
        'nltk',
        'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DocMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/images/icon.ico' if os.path.exists('static/images/icon.ico') else None
)
"""
        
        spec_file = self.base_dir / "DocMaster.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        # Executa o PyInstaller
        subprocess.run([
            str(python_exe), "-m", "PyInstaller",
            "--clean",
            str(spec_file)
        ], cwd=str(self.base_dir))
        
        logging.info("Executável criado em dist/DocMaster ✓")

    def create_shortcuts(self):
        """Cria atalhos para o sistema"""
        if self.os_type == "windows":
            # Cria um arquivo .bat para Windows
            bat_content = f"""@echo off
cd /d "%~dp0"
call venv\\Scripts\\activate
python run.py
pause
"""
            bat_file = self.base_dir / "DocMaster.bat"
            with open(bat_file, 'w') as f:
                f.write(bat_content)
            logging.info("Atalho Windows criado: DocMaster.bat ✓")
            
        else:
            # Cria um script shell para Unix
            sh_content = f"""#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python run.py
"""
            sh_file = self.base_dir / "docmaster.sh"
            with open(sh_file, 'w') as f:
                f.write(sh_content)
            os.chmod(sh_file, 0o755)
            logging.info("Atalho Unix criado: docmaster.sh ✓")

    def install_and_run(self):
        """Executa o processo completo de instalação e execução"""
        try:
            self.print_banner()
            self.check_python_version()
            self.create_virtual_environment()
            self.install_dependencies()
            self.install_system_dependencies()
            self.setup_environment()
            self.create_directories()
            self.initialize_database()
            self.create_shortcuts()
            
            print("\n" + "="*50)
            print("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*50)
            print("Iniciando DocMaster Pro...")
            print("="*50)
            
            self.run_application()
            
        except Exception as e:
            logging.error(f"Erro durante a instalação: {e}")
            sys.exit(1)

    def create_package(self):
        """Cria um pacote distribuível"""
        logging.info("Criando pacote distribuível...")
        
        # Cria diretório dist
        dist_dir = self.base_dir / "dist_package"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        dist_dir.mkdir()
        
        # Copia arquivos necessários
        files_to_copy = [
            'app.py',
            'config.py',
            'run.py',
            'requirements.txt',
            '.env.example',
            'README.md',
            'LICENSE'
        ]
        
        for file in files_to_copy:
            src = self.base_dir / file
            if src.exists():
                shutil.copy2(src, dist_dir)
        
        # Copia diretórios
        dirs_to_copy = ['templates', 'static', 'utils']
        for dir_name in dirs_to_copy:
            src_dir = self.base_dir / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, dist_dir / dir_name)
        
        # Cria arquivo ZIP
        shutil.make_archive(
            str(self.base_dir / 'DocMaster_Package'),
            'zip',
            dist_dir
        )
        
        logging.info("Pacote criado: DocMaster_Package.zip ✓")

def main():
    installer = DocMasterInstaller()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-exe":
            installer.create_executable()
        elif sys.argv[1] == "--package":
            installer.create_package()
        elif sys.argv[1] == "--help":
            print("""
DocMaster Pro - Instalador

Uso:
    python run.py              # Instala e executa o sistema
    python run.py --create-exe # Cria executável
    python run.py --package    # Cria pacote distribuível
    python run.py --help       # Mostra esta ajuda
            """)
        else:
            print(f"Comando desconhecido: {sys.argv[1]}")
    else:
        installer.install_and_run()

if __name__ == "__main__":
    main()
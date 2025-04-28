@echo off
echo ===================================================
echo Configuracao do Sistema de Emails para Prefeituras
echo ===================================================
echo.

echo Verificando ambiente Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado. Por favor, instale o Python 3.7 ou superior.
    echo Voce pode baixar o Python em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Criando ambiente virtual...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao criar ambiente virtual.
    pause
    exit /b 1
)

echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Instalando PyInstaller...
pip install pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao instalar PyInstaller.
    pause
    exit /b 1
)

echo.
echo Criando diretorios de recursos...
mkdir resources
mkdir templates
mkdir config
mkdir backups

echo.
echo Criando arquivo run.py...
echo import os > run.py
echo import sys >> run.py
echo from sistema_email import SistemaEmail >> run.py
echo import tkinter as tk >> run.py
echo. >> run.py
echo def resource_path(relative_path): >> run.py
echo     """ Obtém o caminho absoluto para recursos quando executando como executável """ >> run.py
echo     try: >> run.py
echo         # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS >> run.py
echo         base_path = sys._MEIPASS >> run.py
echo     except Exception: >> run.py
echo         base_path = os.path.abspath(".") >> run.py
echo     return os.path.join(base_path, relative_path) >> run.py
echo. >> run.py
echo if __name__ == "__main__": >> run.py
echo     root = tk.Tk() >> run.py
echo     app = SistemaEmail(root) >> run.py
echo     root.mainloop() >> run.py

echo.
echo Compilando o executavel...
pyinstaller --name "Sistema_Email_Prefeituras" --onefile --windowed --icon=resources/icon.ico --add-data "resources;resources" --add-data "templates;templates" --add-data "config;config" run.py
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao criar o executavel.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo Processo concluido com sucesso!
echo.
echo O executavel foi criado em: dist\Sistema_Email_Prefeituras.exe
echo.
echo Certifique-se de copiar as pastas 'resources', 'templates', 
echo 'config' e 'backups' para o mesmo diretorio do executavel 
echo se deseja executar o programa em outra maquina.
echo =======================================================
echo.

pause
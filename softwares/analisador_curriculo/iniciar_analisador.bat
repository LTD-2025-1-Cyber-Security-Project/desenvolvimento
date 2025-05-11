@echo off
echo Iniciando Analisador de Curriculos...
echo.

:: Verificar se o Python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Por favor, instale o Python 3.x.
    echo Visite https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

:: Verificar se o ambiente virtual existe, se não, criar
if not exist venv (
    echo Criando ambiente virtual...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

:: Ativar ambiente virtual
call venv\Scripts\activate.bat

:: Verificar se os pacotes estão instalados
if not exist venv\Lib\site-packages\flask (
    echo Instalando pacotes necessários...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao instalar pacotes.
        pause
        exit /b 1
    )
)

:: Iniciar a aplicação
echo Iniciando servidor...
python app.py

:: Desativar ambiente virtual ao sair
call venv\Scripts\deactivate.bat
pause

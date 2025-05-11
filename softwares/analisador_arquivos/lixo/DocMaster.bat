@echo off
echo ==========================================
echo       INICIANDO DOCMASTER PRO
echo ==========================================
echo.

:: Verifica se Python está instalado
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.9 ou superior.
    echo Visite: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Verifica a versão do Python
python --version | findstr /R "3\.[9-9]\|3\.1[0-9]" >nul
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Versao do Python pode ser incompativel.
    echo Recomendamos Python 3.9 ou superior.
    echo.
    set /p continue=Deseja continuar mesmo assim? (s/n): 
    if /i "%continue%" NEQ "s" exit /b 1
)

:: Executa o script principal
python run.py

:: Se ocorrer um erro
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Ocorreu um problema ao executar o DocMaster.
    echo Verifique o arquivo de log para mais detalhes.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
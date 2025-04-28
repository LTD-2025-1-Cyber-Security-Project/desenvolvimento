@echo off
echo ====================================
echo Configurando repositorio Git
echo ====================================
echo.

REM Verifica se o Git está instalado
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Git nao encontrado. Por favor, instale o Git.
    echo Voce pode baixar o Git em: https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Verifica se já está em um repositório git
if exist .git (
    echo Repositorio Git ja inicializado.
) else (
    echo Inicializando repositorio Git...
    git init
    if %ERRORLEVEL% NEQ 0 (
        echo ERRO: Falha ao inicializar repositorio Git.
        pause
        exit /b 1
    )
)

REM Verifica se o arquivo .gitignore existe
if not exist .gitignore (
    echo Arquivo .gitignore nao encontrado. Criando...
    echo # Ambiente virtual > .gitignore
    echo venv/ >> .gitignore
    echo env/ >> .gitignore
    echo ENV/ >> .gitignore
    echo # Arquivos compilados do Python >> .gitignore
    echo __pycache__/ >> .gitignore
    echo *.py[cod] >> .gitignore
    echo *$py.class >> .gitignore
    echo *.so >> .gitignore
    echo .Python >> .gitignore
    echo build/ >> .gitignore
    echo develop-eggs/ >> .gitignore
    echo dist/ >> .gitignore
    echo downloads/ >> .gitignore
    echo eggs/ >> .gitignore
    echo .eggs/ >> .gitignore
    echo lib/ >> .gitignore
    echo lib64/ >> .gitignore
    echo parts/ >> .gitignore
    echo sdist/ >> .gitignore
    echo var/ >> .gitignore
    echo wheels/ >> .gitignore
    echo *.egg-info/ >> .gitignore
    echo .installed.cfg >> .gitignore
    echo *.egg >> .gitignore
    echo # Diretórios de dados gerados pelo sistema >> .gitignore
    echo backups/ >> .gitignore
    echo config/ >> .gitignore
    echo *.db >> .gitignore
    echo *.sqlite3 >> .gitignore
    echo # Arquivos de log >> .gitignore
    echo *.log >> .gitignore
    echo # Arquivos temporários >> .gitignore
    echo temp/ >> .gitignore
    echo tmp/ >> .gitignore
    echo # Pasta do PyInstaller >> .gitignore
    echo dist/ >> .gitignore
    echo build/ >> .gitignore
    echo # Arquivos específicos do PyInstaller >> .gitignore
    echo *.spec >> .gitignore
    echo # Arquivos específicos do IDE >> .gitignore
    echo .idea/ >> .gitignore
    echo .vscode/ >> .gitignore
    echo *.swp >> .gitignore
    echo *.swo >> .gitignore
    echo .DS_Store >> .gitignore
    echo # Arquivos de ambiente >> .gitignore
    echo .env >> .gitignore
    echo .venv >> .gitignore
)

echo.
echo Adicionando arquivos ao Git (excluindo venv e outros arquivos ignorados)...
git add .

echo.
echo Verificando o status do repositorio...
git status

echo.
echo ====================================
echo Configuracao Git concluida!
echo ====================================
echo.
echo Agora voce pode fazer o commit com:
echo git commit -m "Mensagem de commit"
echo.
echo E depois configurar o repositorio remoto com:
echo git remote add origin [URL_DO_REPOSITORIO]
echo git push -u origin master
echo ====================================
echo.

pause
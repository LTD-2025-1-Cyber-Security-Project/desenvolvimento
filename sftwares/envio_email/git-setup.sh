#!/bin/bash

echo "===================================="
echo "Configurando repositório Git"
echo "===================================="
echo

# Verifica se o Git está instalado
if ! command -v git &> /dev/null; then
    echo "ERRO: Git não encontrado. Por favor, instale o Git."
    echo "Em sistemas baseados em Debian/Ubuntu: sudo apt-get install git"
    echo "Em sistemas baseados em Fedora: sudo dnf install git"
    echo "Em macOS com Homebrew: brew install git"
    echo "Ou visite: https://git-scm.com/downloads"
    exit 1
fi

# Verifica se já está em um repositório git
if [ -d .git ]; then
    echo "Repositório Git já inicializado."
else
    echo "Inicializando repositório Git..."
    git init
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao inicializar repositório Git."
        exit 1
    fi
fi

# Verifica se o arquivo .gitignore existe
if [ ! -f .gitignore ]; then
    echo "Arquivo .gitignore não encontrado. Criando..."
    cat > .gitignore << 'EOF'
# Ambiente virtual
venv/
env/
ENV/

# Arquivos compilados do Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Diretórios de dados gerados pelo sistema
backups/
config/
*.db
*.sqlite3

# Arquivos de log
*.log

# Arquivos temporários
temp/
tmp/

# Pasta do PyInstaller
dist/
build/

# Arquivos específicos do PyInstaller
*.spec

# Arquivos específicos do IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Arquivos de ambiente
.env
.venv
EOF
fi

echo
echo "Adicionando arquivos ao Git (excluindo venv e outros arquivos ignorados)..."
git add .

echo
echo "Verificando o status do repositório..."
git status

echo
echo "===================================="
echo "Configuração Git concluída!"
echo "===================================="
echo
echo "Agora você pode fazer o commit com:"
echo "git commit -m \"Mensagem de commit\""
echo
echo "E depois configurar o repositório remoto com:"
echo "git remote add origin [URL_DO_REPOSITORIO]"
echo "git push -u origin master"
echo "===================================="
echo

# Torna o script executável
chmod +x git-setup.sh
#!/usr/bin/env python3
"""
Script para preparar o Analisador de Currículos para execução no Windows.
Este script prepara o ambiente de desenvolvimento, os arquivos necessários e 
as instruções para instalar e executar no Windows.
"""
import os
import sys
import subprocess
import platform
import shutil
import zipfile
from pathlib import Path
import time

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.BLUE, is_header=False):
    """Imprime mensagem colorida no terminal."""
    if is_header:
        print(f"\n{color}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{color}{Colors.BOLD} {message} {Colors.END}")
        print(f"{color}{Colors.BOLD}{'='*80}{Colors.END}\n")
    else:
        print(f"{color}{message}{Colors.END}")

def run_command(command, verbose=True):
    """Executa um comando e retorna o código de saída."""
    if verbose:
        print_colored(f"Executando: {command}", Colors.YELLOW)
    
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True
    )
    
    # Captura a saída em tempo real
    output = []
    for line in iter(process.stdout.readline, ''):
        if not line:
            break
        if verbose:
            print(line.strip())
        output.append(line)
    
    process.stdout.close()
    return_code = process.wait()
    
    return return_code, ''.join(output)

def check_requirements():
    """Verifica se os requisitos básicos estão instalados."""
    print_colored("Verificando requisitos", Colors.BLUE, True)
    
    # Verificar versão do Python
    python_version = platform.python_version()
    print_colored(f"Versão do Python: {python_version}")
    if int(python_version.split('.')[0]) < 3:
        print_colored("ERRO: É necessário Python 3.x para continuar.", Colors.RED)
        sys.exit(1)
    
    # Verificar pip
    try:
        result, output = run_command("pip --version", verbose=False)
        if result == 0:
            print_colored(f"Pip instalado: {output.strip()}")
        else:
            raise Exception("Pip não encontrado")
    except:
        print_colored("ERRO: pip não encontrado. Instale o pip para continuar.", Colors.RED)
        sys.exit(1)
    
    # Criar diretório uploads se não existir
    os.makedirs("uploads", exist_ok=True)
    print_colored("Diretório 'uploads' verificado/criado.")
    
    # Verificar se o app.py existe
    if not os.path.exists("app.py"):
        print_colored("ERRO: arquivo app.py não encontrado no diretório atual!", Colors.RED)
        sys.exit(1)
    else:
        print_colored("Arquivo app.py encontrado.")
    
    print_colored("Todos os requisitos básicos verificados com sucesso!", Colors.GREEN)

def create_requirements_file():
    """Cria o arquivo requirements.txt."""
    print_colored("Criando arquivo requirements.txt", Colors.BLUE, True)
    
    requirements = """flask==2.2.3
python-dotenv==1.0.0
werkzeug==2.2.3
PyPDF2==3.0.1
google-generativeai>=0.1.0
langchain>=0.0.267
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print_colored("Arquivo requirements.txt criado com sucesso.", Colors.GREEN)

def create_windows_batch_file():
    """Cria um arquivo .bat para iniciar a aplicação no Windows."""
    print_colored("Criando arquivo de inicialização para Windows", Colors.BLUE, True)
    
    batch_content = """@echo off
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
call venv\\Scripts\\activate.bat

:: Verificar se os pacotes estão instalados
if not exist venv\\Lib\\site-packages\\flask (
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
call venv\\Scripts\\deactivate.bat
pause
"""
    
    with open("iniciar_analisador.bat", "w") as f:
        f.write(batch_content)
    
    print_colored("Arquivo iniciar_analisador.bat criado com sucesso.", Colors.GREEN)

def create_utility_files():
    """Cria os arquivos utilitários necessários."""
    print_colored("Criando arquivos utilitários", Colors.BLUE, True)
    
    # Criar diretório utils se não existir
    os.makedirs("utils", exist_ok=True)
    
    # Criar arquivo pdf_extractor.py
    pdf_extractor_code = """import PyPDF2

def extract_text_from_pdf(pdf_path):
    text = ""
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")
    
    return text
"""
    
    with open("utils/pdf_extractor.py", "w") as f:
        f.write(pdf_extractor_code)
    
    # Criar arquivo resume_analyzer.py
    resume_analyzer_code = """import os
import google.generativeai as genai
from datetime import datetime

def analyze_resume(resume_text, tipo_analise='geral', nivel='junior', stack_area='desenvolvimento web'):
    
    # Configurar API do Google
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("Chave de API do Google Gemini não configurada")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # Construir prompt para o Gemini
    prompt = f'''
    Analise este currículo para uma vaga de {nivel} em {stack_area}.
    Tipo de análise: {tipo_analise}
    
    Currículo:
    {resume_text}
    
    Forneça uma análise estruturada nos seguintes tópicos:
    1. Resumo de habilidades e experiência
    2. Pontos fortes
    3. Áreas para desenvolvimento
    4. Adequação para a vaga de {nivel} em {stack_area}
    5. Recomendações para melhorar o currículo
    '''
    
    try:
        # Gerar resposta
        response = model.generate_content(prompt)
        result = response.text
        
        # Formatar resultado
        analysis = {
            'resumo': result,
            'tipo_analise': tipo_analise,
            'nivel': nivel,
            'stack_area': stack_area,
            'data_analise': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        return analysis
        
    except Exception as e:
        raise Exception(f"Erro na análise com Gemini API: {str(e)}")
"""
    
    with open("utils/resume_analyzer.py", "w") as f:
        f.write(resume_analyzer_code)
    
    # Criar arquivo __init__.py para o pacote utils
    with open("utils/__init__.py", "w") as f:
        f.write("# Pacote de utilitários do Analisador de Currículos")
    
    print_colored("Arquivos utilitários criados com sucesso.", Colors.GREEN)

def create_templates():
    """Cria os arquivos de templates HTML."""
    print_colored("Criando templates HTML", Colors.BLUE, True)
    
    # Criar diretório de templates
    os.makedirs("templates", exist_ok=True)
    
    # Template index.html
    index_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisador de Currículos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .container {
            max-width: 800px;
        }
        .upload-form {
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
        }
        .footer {
            margin-top: 50px;
            color: #6c757d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">Analisador de Currículos com IA</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category if category != 'error' else 'danger' }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="upload-form">
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="mb-3">
                    <label for="resume" class="form-label">Selecione seu currículo (PDF)</label>
                    <input class="form-control" type="file" id="resume" name="resume" accept=".pdf" required>
                </div>
                
                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label for="tipo_analise" class="form-label">Tipo de Análise</label>
                        <select class="form-select" id="tipo_analise" name="tipo_analise">
                            <option value="geral">Análise Geral</option>
                            <option value="tecnica">Foco em Habilidades Técnicas</option>
                            <option value="soft_skills">Foco em Soft Skills</option>
                            <option value="melhorias">Sugestões de Melhorias</option>
                        </select>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label for="nivel" class="form-label">Nível Pretendido</label>
                        <select class="form-select" id="nivel" name="nivel">
                            <option value="estagio">Estágio</option>
                            <option value="junior" selected>Júnior</option>
                            <option value="pleno">Pleno</option>
                            <option value="senior">Sênior</option>
                            <option value="tech_lead">Tech Lead</option>
                        </select>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label for="stack_area" class="form-label">Área/Stack</label>
                        <select class="form-select" id="stack_area" name="stack_area">
                            <option value="desenvolvimento web" selected>Desenvolvimento Web</option>
                            <option value="mobile">Desenvolvimento Mobile</option>
                            <option value="data science">Ciência de Dados</option>
                            <option value="devops">DevOps</option>
                            <option value="fullstack">Fullstack</option>
                            <option value="frontend">Frontend</option>
                            <option value="backend">Backend</option>
                            <option value="ia">Inteligência Artificial</option>
                        </select>
                    </div>
                </div>
                
                <div class="d-grid gap-2">
                    <button class="btn btn-primary" type="submit">Analisar Currículo</button>
                </div>
            </form>
        </div>
        
        <div class="footer text-center">
            <p>© {{ now.year }} Analisador de Currículos com IA | Todos os direitos reservados</p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    # Template result.html
    result_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultado da Análise - Analisador de Currículos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .container {
            max-width: 800px;
        }
        .result-card {
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
        }
        .footer {
            margin-top: 50px;
            color: #6c757d;
            font-size: 14px;
        }
        .analysis-meta {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 20px;
        }
        .analysis-content {
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">Resultado da Análise</h1>
        
        <div class="result-card">
            <div class="analysis-meta">
                <p><strong>Tipo de Análise:</strong> {{ analysis.tipo_analise | capitalize }}</p>
                <p><strong>Nível Pretendido:</strong> {{ analysis.nivel | capitalize }}</p>
                <p><strong>Área/Stack:</strong> {{ analysis.stack_area | capitalize }}</p>
                <p><strong>Data da Análise:</strong> {{ analysis.data_analise }}</p>
            </div>
            
            <div class="analysis-content">
                {{ analysis.resumo | safe }}
            </div>
            
            <div class="d-grid gap-2 mt-4">
                <a href="/" class="btn btn-primary">Nova Análise</a>
            </div>
        </div>
        
        <div class="footer text-center">
            <p>© {{ now.year }} Analisador de Currículos com IA | Todos os direitos reservados</p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    # Gravar os templates
    with open("templates/index.html", "w") as f:
        f.write(index_html)
    
    with open("templates/result.html", "w") as f:
        f.write(result_html)
    
    print_colored("Templates HTML criados com sucesso.", Colors.GREEN)

def create_env_file():
    """Cria o arquivo .env para configurações."""
    print_colored("Criando arquivo .env", Colors.BLUE, True)
    
    env_content = """# Chave da API do Google Gemini
GOOGLE_API_KEY=sua_chave_api_aqui

# Chave secreta para a aplicação Flask
SECRET_KEY=chave_secreta_para_flask

# Porta para a aplicação (opcional, padrão é 5000)
# PORT=5000
"""
    
    # Criar .env.example para documentação
    with open(".env.example", "w") as f:
        f.write(env_content)
    
    # Criar .env real se não existir
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print_colored("Arquivo .env criado. IMPORTANTE: Edite este arquivo para adicionar suas chaves de API!", Colors.YELLOW)
    else:
        print_colored("Arquivo .env já existe. Não foi sobrescrito.", Colors.YELLOW)

def create_readme():
    """Cria um arquivo README.md com instruções."""
    print_colored("Criando arquivo README.md", Colors.BLUE, True)
    
    readme_content = """# Analisador de Currículos com IA

Este aplicativo web permite analisar currículos em PDF usando a API do Google Gemini.

## Requisitos

- Python 3.6+
- Conexão com a Internet
- Chave de API do Google Gemini

## Instalação no Windows

### Método 1: Instalação Automatizada
1. Simplesmente execute o arquivo `iniciar_analisador.bat` e siga as instruções.
2. O script irá configurar automaticamente o ambiente virtual e instalar as dependências.

### Método 2: Instalação Manual
1. Certifique-se de ter o Python 3.6+ instalado. [Download Python](https://www.python.org/downloads/windows/)
2. Abra um Prompt de Comando e navegue até o diretório do aplicativo.
3. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```
4. Ative o ambiente virtual:
   ```
   venv\\Scripts\\activate
   ```
5. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
6. Configure a API do Google:
   - Edite o arquivo `.env` e adicione sua chave da API do Google Gemini.
7. Inicie o aplicativo:
   ```
   python app.py
   ```
8. Acesse no navegador: `http://localhost:5000`

## Funcionalidades

- Upload de currículos em formato PDF
- Análise do currículo com diferentes focos:
  - Análise Geral
  - Foco em Habilidades Técnicas
  - Foco em Soft Skills
  - Sugestões de Melhorias
- Personalização por nível (Estágio, Júnior, Pleno, Sênior, etc.)
- Personalização por área (Web, Mobile, Data Science, DevOps, etc.)

## Solução de Problemas

- **Erro de API do Google**: Verifique se a chave no arquivo `.env` está correta.
- **Problemas na inicialização**: Verifique se todas as dependências estão instaladas corretamente.
- **Erros de arquivo**: Certifique-se de que o PDF está em um formato válido.

## Licença

Todos os direitos reservados.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print_colored("Arquivo README.md criado com sucesso.", Colors.GREEN)

def create_windows_package():
    """Cria um pacote ZIP para transferência para Windows."""
    print_colored("Criando pacote para Windows", Colors.BLUE, True)
    
    # Lista de arquivos/diretórios a incluir
    files_to_include = [
        "app.py",
        "iniciar_analisador.bat",
        "requirements.txt",
        "README.md",
        ".env",
        ".env.example",
        "templates",
        "utils",
        "uploads"
    ]
    
    # Nome do arquivo ZIP
    zip_filename = "AnalisadorCurriculos_Windows.zip"
    
    # Remover ZIP anterior se existir
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    
    # Criar novo ZIP
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_to_include:
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(os.path.basename(item), file_path[len(item)+1:])
                        zipf.write(file_path, arcname)
            else:
                if os.path.exists(item):
                    zipf.write(item)
                else:
                    print_colored(f"Aviso: Arquivo {item} não encontrado, não será incluído no ZIP.", Colors.YELLOW)
    
    print_colored(f"Pacote {zip_filename} criado com sucesso.", Colors.GREEN)
    return zip_filename

def main():
    """Função principal."""
    print_colored("Preparação do Analisador de Currículos para Windows", Colors.GREEN, True)
    
    # Verificar requisitos
    check_requirements()
    
    # Criar arquivos necessários
    create_requirements_file()
    create_utility_files()
    create_templates()
    create_env_file()
    create_windows_batch_file()
    create_readme()
    
    # Criar pacote para Windows
    zip_file = create_windows_package()
    
    # Instruções finais
    print_colored("\nPROCESSO CONCLUÍDO COM SUCESSO!", Colors.GREEN, True)
    print_colored(f"""
Para utilizar no Windows:

1. Transfira o arquivo '{zip_file}' para o computador Windows
2. Extraia o conteúdo do arquivo ZIP
3. Edite o arquivo '.env' e adicione sua chave da API do Google Gemini
4. Execute o arquivo 'iniciar_analisador.bat'
5. Acesse o aplicativo no navegador: http://localhost:5000

IMPORTANTE: O aplicativo requer Python 3.6+ instalado no Windows.
Download Python: https://www.python.org/downloads/windows/
""", Colors.BLUE)

if __name__ == "__main__":
    main()
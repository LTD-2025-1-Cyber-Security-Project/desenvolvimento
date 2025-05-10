#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import time

def print_status(message):
    """Imprime uma mensagem de status formatada."""
    print(f"\n{'='*80}\n{message}\n{'='*80}")

def run_command(command, shell=False):
    """Executa um comando e imprime a saída em tempo real."""
    print(f"Executando: {command if isinstance(command, str) else ' '.join(command)}")
    
    if shell:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Imprime a saída em tempo real
    for line in iter(process.stdout.readline, ''):
        print(line.strip())
        if not line:
            break
    
    process.stdout.close()
    return_code = process.wait()
    
    if return_code != 0:
        print(f"AVISO: O comando retornou código de erro {return_code}")
    
    return return_code

def check_system():
    """Verifica se o sistema é macOS e os requisitos estão instalados."""
    print_status("Verificando sistema")
    
    if platform.system() != "Darwin":
        print("Este script foi projetado para ser executado no macOS.")
        sys.exit(1)
    
    # Verificar se o Python está instalado
    try:
        python_version = subprocess.check_output(["python3", "--version"]).decode().strip()
        print(f"Python detectado: {python_version}")
    except:
        print("Python 3 não encontrado. Instale o Python 3 antes de continuar.")
        sys.exit(1)
    
    # Verificar se o pip está instalado
    try:
        pip_version = subprocess.check_output(["pip3", "--version"]).decode().strip()
        print(f"Pip detectado: {pip_version}")
    except:
        print("Pip não encontrado. Instale o pip antes de continuar.")
        sys.exit(1)
    
    # Verificar se o virtualenv está instalado
    try:
        venv_version = subprocess.check_output(["virtualenv", "--version"]).decode().strip()
        print(f"Virtualenv detectado: {venv_version}")
    except:
        print("Virtualenv não encontrado. Instalando...")
        run_command(["pip3", "install", "virtualenv"])

def setup_virtualenv():
    """Configura o ambiente virtual."""
    print_status("Configurando ambiente virtual")
    
    # Remover ambiente virtual anterior, se existir
    if os.path.exists("venv"):
        print("Removendo ambiente virtual anterior...")
        shutil.rmtree("venv")
    
    # Criar novo ambiente virtual
    print("Criando novo ambiente virtual...")
    run_command(["virtualenv", "venv"])
    
    # Determinar o comando de ativação (diferente para diferentes shells)
    if platform.system() == "Darwin":
        activate_cmd = "source venv/bin/activate"
    else:
        activate_cmd = r"venv\Scripts\activate"
    
    print(f"Para ativar manualmente o ambiente virtual: {activate_cmd}")
    return activate_cmd

def install_packages(activate_cmd):
    """Instala os pacotes necessários no ambiente virtual."""
    print_status("Instalando pacotes necessários")
    
    # Criar arquivo requirements.txt
    with open("requirements.txt", "w") as f:
        f.write("""
flask==2.2.3
python-dotenv==1.0.0
werkzeug==2.2.3
PyPDF2==3.0.1
pyinstaller==5.13.0
google-generativeai>=0.1.0
langchain>=0.0.267
        """.strip())
    
    print("Arquivo requirements.txt criado.")
    
    # Instalar pacotes usando pip no ambiente virtual
    if platform.system() == "Darwin":
        run_command(f"{activate_cmd} && pip install -r requirements.txt", shell=True)
    else:
        run_command(f"{activate_cmd} && pip install -r requirements.txt", shell=True)

def create_utility_files():
    """Cria os arquivos utilitários necessários que não estão no código principal."""
    print_status("Criando arquivos de utilitários")
    
    # Criar diretório utils se não existir
    os.makedirs("utils", exist_ok=True)
    
    # Criar pdf_extractor.py
    with open("utils/pdf_extractor.py", "w") as f:
        f.write("""
import PyPDF2

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
""".strip())
    
    # Criar resume_analyzer.py
    with open("utils/resume_analyzer.py", "w") as f:
        f.write("""
import os
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
""".strip())
    
    print("Arquivos utilitários criados com sucesso.")

def create_templates():
    """Cria os arquivos de templates HTML necessários."""
    print_status("Criando templates HTML")
    
    # Criar diretório templates se não existir
    os.makedirs("templates", exist_ok=True)
    
    # Criar index.html
    with open("templates/index.html", "w") as f:
        f.write("""
<!DOCTYPE html>
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
</html>
""".strip())
    
    # Criar result.html
    with open("templates/result.html", "w") as f:
        f.write("""
<!DOCTYPE html>
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
</html>
""".strip())
    
    print("Templates HTML criados com sucesso.")

def create_dotenv_file():
    """Cria um arquivo .env de exemplo."""
    print_status("Criando arquivo .env de exemplo")
    
    with open(".env.example", "w") as f:
        f.write("""
# Chave da API do Google Gemini
GOOGLE_API_KEY=sua_chave_api_aqui

# Chave secreta para a aplicação Flask
SECRET_KEY=chave_secreta_para_flask

# Porta para a aplicação (opcional, padrão é 5000)
# PORT=5000
""".strip())
    
    # Criar .env real se não existir
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("Arquivo .env criado. IMPORTANTE: Edite este arquivo para adicionar suas chaves de API!")
    else:
        print("Arquivo .env já existe. Não sobrescrito.")

def build_executable(activate_cmd):
    """Constrói o executável para Windows usando PyInstaller."""
    print_status("Construindo executável para Windows")
    
    # Verificar se app.py existe
    if not os.path.exists("app.py"):
        print("ERRO: arquivo app.py não encontrado!")
        return False
    
    # Criar especificação do PyInstaller
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('.env', '.'), ('uploads', 'uploads')],
    hiddenimports=['werkzeug.middleware.proxy_fix'],
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
    [],
    exclude_binaries=True,
    name='AnalisadorCurriculos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AnalisadorCurriculos',
)
"""
    
    with open("analisador.spec", "w") as f:
        f.write(spec_content)
    
    print("Arquivo de especificação do PyInstaller criado.")
    
    # Executar PyInstaller
    print("Executando PyInstaller (isso pode levar alguns minutos)...")
    run_command(f"{activate_cmd} && pyinstaller --clean analisador.spec --distpath=dist_win", shell=True)
    
    # Verificar se o executável foi criado
    if os.path.exists("dist_win/AnalisadorCurriculos"):
        print("\nExecutável criado com sucesso em dist_win/AnalisadorCurriculos/")
        
        # Criar arquivo README para instruções de instalação
        with open("dist_win/README.txt", "w") as f:
            f.write("""
ANALISADOR DE CURRÍCULOS COM IA
==============================

INSTRUÇÕES DE INSTALAÇÃO PARA WINDOWS
-------------------------------------

1. Copie a pasta 'AnalisadorCurriculos' para o computador Windows.
2. Edite o arquivo '.env' dentro da pasta para adicionar sua chave da API do Google Gemini.
3. Execute o arquivo 'AnalisadorCurriculos.exe' para iniciar a aplicação.
4. Acesse a aplicação pelo navegador em: http://localhost:5000

REQUISITOS:
- Windows 10 ou superior
- Conexão com a internet para acessar a API do Google Gemini

RESOLUÇÃO DE PROBLEMAS:
- Se ocorrer um erro ao iniciar, verifique se a chave da API do Google está correta no arquivo .env.
- Certifique-se de que o firewall não esteja bloqueando a aplicação.
""")
        
        print("Arquivo README.txt criado com instruções de instalação.")
        return True
    else:
        print("ERRO: Falha ao criar o executável!")
        return False

def main():
    print_status("Iniciando criação de executável para Windows")
    
    # Verificar sistema
    check_system()
    
    # Configurar ambiente virtual
    activate_cmd = setup_virtualenv()
    
    # Instalar pacotes
    install_packages(activate_cmd)
    
    # Criar arquivos utilitários
    create_utility_files()
    
    # Criar templates
    create_templates()
    
    # Criar arquivo .env
    create_dotenv_file()
    
    # Construir executável
    success = build_executable(activate_cmd)
    
    if success:
        print_status("PROCESSO CONCLUÍDO COM SUCESSO!")
        print("""
Para transferir para o Windows:
1. Copie a pasta 'dist_win/AnalisadorCurriculos' para o computador Windows.
2. Edite o arquivo '.env' dentro da pasta para adicionar sua chave da API do Google.
3. Execute 'AnalisadorCurriculos.exe' no Windows.

Obrigado por usar este script!
""")
    else:
        print_status("PROCESSO CONCLUÍDO COM ERROS")
        print("Verifique as mensagens de erro acima.")

if __name__ == "__main__":
    main()
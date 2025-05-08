from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from markupsafe import Markup  # Importação corrigida
import os
import json
import requests
import time
import uuid
import re
import markdown
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Importações específicas para cada IA
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument

# Chave API padrão do Gemini (pré-configurada)
DEFAULT_GEMINI_API_KEY = "AIzaSyCY5JQRIAZlq7Re-GNDtwn8b1Hmza_hk8Y"

# Em produção, use um banco de dados real
try:
    with open('data/ai_models.json', 'r') as f:
        AI_MODELS = json.load(f)
except:
    AI_MODELS = {
        "google-gemini": {
            "name": "Google Gemini 1.5 Pro",
            "api_key": DEFAULT_GEMINI_API_KEY,  # Chave padrão configurada
            "endpoint": "gemini-1.5-pro",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 1,
            "enabled": True,
            "api_type": "google",
            "default": True
        },
        "google-gemini-flash": {
            "name": "Google Gemini 1.5 Flash",
            "api_key": DEFAULT_GEMINI_API_KEY,  # Chave padrão configurada
            "endpoint": "gemini-1.5-flash",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 2,
            "enabled": True,
            "api_type": "google",
            "default": False
        },
        "openai-gpt4": {
            "name": "OpenAI GPT-4",
            "api_key": "",
            "endpoint": "gpt-4",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 3,
            "enabled": False,
            "api_type": "openai",
            "default": False
        },
        "openai-gpt35": {
            "name": "OpenAI GPT-3.5 Turbo",
            "api_key": "",
            "endpoint": "gpt-3.5-turbo",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 4,
            "enabled": False,
            "api_type": "openai",
            "default": False
        },
        "anthropic-claude": {
            "name": "Anthropic Claude 3",
            "api_key": "",
            "endpoint": "claude-3-opus-20240229",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 5,
            "enabled": False,
            "api_type": "anthropic",
            "default": False
        },
        "perplexity": {
            "name": "Perplexity AI",
            "api_key": "",
            "endpoint": "sonar-medium-online",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 6,
            "enabled": False,
            "api_type": "perplexity",
            "default": False
        },
        "deepseek": {
            "name": "DeepSeek AI",
            "api_key": "",
            "endpoint": "deepseek-coder",
            "max_tokens": 4096, 
            "temperature": 0.7,
            "priority": 7,
            "enabled": False,
            "api_type": "deepseek",
            "default": False
        },
        "blackbox": {
            "name": "Blackbox AI",
            "api_key": "",
            "endpoint": "blackbox-standard",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 8,
            "enabled": False,
            "api_type": "blackbox",
            "default": False
        },
        "xai-grok": {
            "name": "xAI Grok",
            "api_key": "",
            "endpoint": "grok-1",
            "max_tokens": 4096,
            "temperature": 0.7,
            "priority": 9,
            "enabled": False,
            "api_type": "xai",
            "default": False
        }
    }

# Configurações
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'prefeitura_ia_secret_key')
MAX_RETRIES = 2
RETRY_DELAY = 5  # segundos

# Criar diretórios de dados se não existirem
os.makedirs('data', exist_ok=True)

# Simulação de banco de dados de usuários (em produção, usar banco de dados real)
try:
    with open('data/users.json', 'r') as f:
        users_db = json.load(f)
except:
    users_db = {
        "admin": {
            "password": generate_password_hash("admin123"),
            "role": "admin",
            "department": "TI",
            "preferred_model": "google-gemini" 
        }
    }

# Histórico de prompts (em produção, usar banco de dados real)
try:
    with open('data/prompts_history.json', 'r') as f:
        prompts_history = json.load(f)
except:
    prompts_history = []

# Salvar dados em arquivos
def save_data():
    # Dados de usuários
    with open('data/users.json', 'w') as f:
        json.dump(users_db, f, indent=4)
    
    # Dados de histórico
    with open('data/prompts_history.json', 'w') as f:
        json.dump(prompts_history, f, indent=4)
        
    # Configurações de modelos de IA
    with open('data/ai_models.json', 'w') as f:
        json.dump(AI_MODELS, f, indent=4)

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar permissão de admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página', 'danger')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Funções para diferentes modelos de IA
def generate_with_google_gemini(prompt, model_info):
    # Usar a chave padrão se não houver uma configurada
    api_key = model_info["api_key"] if model_info["api_key"] else DEFAULT_GEMINI_API_KEY
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_info["endpoint"])
    
    generation_config = {
        "temperature": model_info["temperature"],
        "max_output_tokens": model_info["max_tokens"],
    }
    
    response = model.generate_content(prompt, generation_config=generation_config)
    return response.text

def generate_with_openai(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['api_key']}"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API OpenAI: {response.text}")

def generate_with_anthropic(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": model_info["api_key"],
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    else:
        raise Exception(f"Erro na API Anthropic: {response.text}")

def generate_with_perplexity(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['api_key']}"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API Perplexity: {response.text}")

def generate_with_deepseek(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['api_key']}"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API DeepSeek: {response.text}")

def generate_with_blackbox(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['api_key']}"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.blackbox.ai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API Blackbox: {response.text}")

def generate_with_xai(prompt, model_info):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['api_key']}"
    }
    
    payload = {
        "model": model_info["endpoint"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": model_info["temperature"],
        "max_tokens": model_info["max_tokens"]
    }
    
    response = requests.post(
        "https://api.grok.x/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API xAI: {response.text}")

# Função para gerar conteúdo com o modelo escolhido
def generate_content(prompt, model_id=None, user_id=None):
    if not model_id and user_id in users_db:
        model_id = users_db[user_id].get("preferred_model")
    
    # Se ainda não tiver um modelo, use o padrão
    if not model_id:
        for m_id, model in AI_MODELS.items():
            if model["default"] and model["enabled"]:
                model_id = m_id
                break
    
    # Se nenhum modelo estiver disponível
    if not model_id or model_id not in AI_MODELS or not AI_MODELS[model_id]["enabled"]:
        enabled_models = [m_id for m_id, m in AI_MODELS.items() if m["enabled"]]
        if enabled_models:
            model_id = min(enabled_models, key=lambda x: AI_MODELS[x]["priority"])
        else:
            raise Exception("Nenhum modelo de IA está habilitado. Por favor, configure pelo menos um modelo.")
    
    model_info = AI_MODELS[model_id]
    
    # Verificar se tem chave API para modelos que não são Gemini
    if model_info["api_type"] != "google" and not model_info["api_key"]:
        raise Exception(f"API Key não configurada para o modelo {model_info['name']}. Por favor, configure a chave nas configurações.")
    
    # Tenta gerar com o modelo escolhido
    for attempt in range(MAX_RETRIES):
        try:
            if model_info["api_type"] == "google":
                return generate_with_google_gemini(prompt, model_info)
            elif model_info["api_type"] == "openai":
                return generate_with_openai(prompt, model_info)
            elif model_info["api_type"] == "anthropic":
                return generate_with_anthropic(prompt, model_info)
            elif model_info["api_type"] == "perplexity":
                return generate_with_perplexity(prompt, model_info)
            elif model_info["api_type"] == "deepseek":
                return generate_with_deepseek(prompt, model_info)
            elif model_info["api_type"] == "blackbox":
                return generate_with_blackbox(prompt, model_info)
            elif model_info["api_type"] == "xai":
                return generate_with_xai(prompt, model_info)
            else:
                raise Exception(f"Tipo de API desconhecido: {model_info['api_type']}")
        except (ResourceExhausted, Exception) as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY
                if hasattr(e, 'retry_delay') and hasattr(e.retry_delay, 'seconds'):
                    wait_time = e.retry_delay.seconds
                
                # Tenta com o próximo modelo disponível
                current_priority = model_info["priority"]
                next_model = None
                
                for m_id, m in sorted(AI_MODELS.items(), key=lambda x: x[1]["priority"]):
                    if m["enabled"] and m["priority"] > current_priority:
                        next_model = m_id
                        break
                
                if next_model:
                    model_id = next_model
                    model_info = AI_MODELS[model_id]
                    continue
                
                # Se não houver próximo modelo, aguarda e tenta novamente
                time.sleep(wait_time)
            else:
                # Último retry falhou, retorna mensagem de erro
                raise

# Rotas
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users_db and check_password_hash(users_db[username]['password'], password):
            session['user_id'] = username
            session['role'] = users_db[username]['role']
            session['department'] = users_db[username].get('department', 'N/A')
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas', 'danger')
    
    return render_template('login.html')

# Função para renderizar markdown com suporte a syntax highlighting
def render_markdown(text):
    # Configuração do markdown com várias extensões
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br'
    ])
    
    # Converter markdown para HTML
    html = md.convert(text)
    
    # Retornar como Markup para evitar escape automático no template
    return Markup(html)

# Modificação na rota generate_prompt para incluir renderização markdown
@app.route('/generate-prompt', methods=['GET', 'POST'])
@login_required
def generate_prompt():
    # Lista de modelos habilitados para seleção
    enabled_models = {model_id: model for model_id, model in AI_MODELS.items() if model["enabled"]}
    
    if request.method == 'POST':
        # Capturar dados do formulário
        document_type = request.form.get('document_type')
        context = request.form.get('context')
        legal_restrictions = request.form.get('legal_restrictions')
        deadline = request.form.get('deadline')
        detail_level = request.form.get('detail_level')
        selected_model = request.form.get('ai_model')
        
        # Verificar se o modelo selecionado está habilitado
        if selected_model not in enabled_models:
            # Usar modelo preferido do usuário ou modelo padrão
            if session['user_id'] in users_db and "preferred_model" in users_db[session['user_id']]:
                selected_model = users_db[session['user_id']]["preferred_model"]
            else:
                # Encontrar modelo padrão
                for model_id, model in AI_MODELS.items():
                    if model["default"] and model["enabled"]:
                        selected_model = model_id
                        break
        
        # Criar prompt para a IA
        ai_prompt = f"""
        Como especialista em administração pública municipal, crie um {document_type} considerando:
        
        CONTEXTO MUNICIPAL: {context}
        
        RESTRIÇÕES LEGAIS: {legal_restrictions}
        
        PRAZO: {deadline}
        
        DETALHAMENTO: {detail_level}
        
        Forneça uma resposta estruturada, profissional e aplicável ao contexto de gestão municipal.
        """
        
        # Chamar API de IA com tratamento de erros e retry
        response_text = ""
        response_html = ""
        success = False
        used_model = ""
        error_message = ""
        
        try:
            response_text = generate_content(ai_prompt, selected_model, session['user_id'])
            success = True
            used_model = selected_model
            
            # Renderizar markdown para HTML
            response_html = render_markdown(response_text)
            
        except ResourceExhausted as e:
            error_message = f"Limite de requisições atingido: {str(e)}"
            flash('Limite de requisições da API atingido. Tente outro modelo de IA ou aguarde.', 'warning')
        except Exception as e:
            error_message = str(e)
            flash(f'Erro ao gerar conteúdo: {str(e)}', 'danger')
        
        if not success:
            response_text = f"""
            **ERRO: Não foi possível gerar o conteúdo**
            
            {error_message}
            
            Por favor, tente novamente mais tarde ou selecione outro modelo de IA.
            """
            response_html = render_markdown(response_text)
        
        # Salvar no histórico
        prompt_id = str(uuid.uuid4())
        prompt_record = {
            'id': prompt_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user': session['user_id'],
            'prompt': ai_prompt,
            'response': response_text,
            'success': success,
            'model_used': used_model if success else selected_model,
            'error': error_message if not success else "",
            'metadata': {
                'document_type': document_type,
                'context': context,
                'legal_restrictions': legal_restrictions,
                'deadline': deadline,
                'detail_level': detail_level
            }
        }
        prompts_history.append(prompt_record)
        save_data()  # Salvar no arquivo
        
        return render_template('result.html', 
                              response=response_text,
                              response_html=response_html,
                              prompt=ai_prompt,
                              timestamp=prompt_record['timestamp'],
                              success=success,
                              model_used=AI_MODELS[used_model]["name"] if used_model in AI_MODELS else selected_model,
                              prompt_id=prompt_id)
    
    return render_template('generate_prompt.html', models=enabled_models)

# Modificação na rota export_result para incluir renderização markdown
@app.route('/export/<prompt_id>')
@login_required
def export_result(prompt_id):
    # Encontrar o prompt pelo ID
    prompt = next((p for p in prompts_history if p.get('id') == prompt_id), None)
    
    if prompt:
        # Verificar se o usuário tem permissão (próprio prompt ou admin)
        if prompt['user'] == session['user_id'] or session['role'] == 'admin':
            # Adicionar HTML renderizado
            prompt_copy = prompt.copy()
            prompt_copy['response_html'] = render_markdown(prompt['response'])
            return jsonify(prompt_copy)
        
    flash('Resultado não encontrado ou permissão negada', 'danger')
    return redirect(url_for('view_history'))

# Modificação na rota view_history para incluir renderização markdown ao abrir detalhes
@app.route('/view-prompt/<prompt_id>')
@login_required
def view_prompt(prompt_id):
    # Encontrar o prompt pelo ID
    prompt = next((p for p in prompts_history if p.get('id') == prompt_id), None)
    
    if not prompt:
        flash('Prompt não encontrado', 'danger')
        return redirect(url_for('view_history'))
    
    # Verificar permissão (próprio prompt ou admin)
    if prompt['user'] != session['user_id'] and session['role'] != 'admin':
        flash('Você não tem permissão para visualizar este prompt', 'danger')
        return redirect(url_for('view_history'))
    
    # Obter nome do modelo
    model_id = prompt.get('model_used', '')
    model_name = AI_MODELS[model_id]['name'] if model_id in AI_MODELS else "Modelo não disponível"
    
    # Renderizar markdown para HTML
    response_html = render_markdown(prompt['response'])
    
    return render_template('view_prompt.html',
                          prompt=prompt,
                          response_html=response_html,
                          model_name=model_name)

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Verificar se há pelo menos um modelo habilitado
    has_enabled_model = any(model["enabled"] for model in AI_MODELS.values())
    
    # Obter informações sobre o modelo preferido do usuário
    preferred_model = "Nenhum"
    if session['user_id'] in users_db and "preferred_model" in users_db[session['user_id']]:
        model_id = users_db[session['user_id']]["preferred_model"]
        if model_id in AI_MODELS:
            preferred_model = AI_MODELS[model_id]["name"]
    
    return render_template(
        'dashboard.html', 
        username=session['user_id'],
        has_enabled_model=has_enabled_model,
        preferred_model=preferred_model,
        active_models=[m for m_id, m in AI_MODELS.items() if m["enabled"]]
    )


@app.route('/history')
@login_required
def view_history():
    # Filtrar histórico por usuário, exceto para admins que veem tudo
    if session.get('role') == 'admin':
        user_history = prompts_history
    else:
        user_history = [p for p in prompts_history if p['user'] == session['user_id']]
    
    # Adicionar nomes de modelos
    for prompt in user_history:
        model_id = prompt.get('model_used', '')
        if model_id in AI_MODELS:
            prompt['model_name'] = AI_MODELS[model_id]['name']
        else:
            prompt['model_name'] = "Modelo não disponível"
    
    return render_template('history.html', history=user_history)

@app.route('/templates')
@login_required
def templates():
    # Em produção, carregar de um banco de dados
    try:
        with open('data/templates.json', 'r') as f:
            saved_templates = json.load(f)
    except:
        saved_templates = []
    
    # Filtrar templates por usuário, exceto para admins que veem todos
    if session.get('role') != 'admin':
        saved_templates = [t for t in saved_templates if t.get('created_by') == session['user_id'] or t.get('is_public', False)]
    
    return render_template('templates.html', templates=saved_templates)

@app.route('/save-template', methods=['POST'])
@login_required
def save_template():
    if request.method == 'POST':
        template_data = request.form.to_dict()
        template_data['created_by'] = session['user_id']
        template_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        template_data['id'] = str(uuid.uuid4())
        template_data['is_public'] = bool(request.form.get('is_public', False))
        
        # Em produção, salvar em um banco de dados
        try:
            with open('data/templates.json', 'r') as f:
                templates = json.load(f)
        except:
            templates = []
        
        templates.append(template_data)
        
        with open('data/templates.json', 'w') as f:
            json.dump(templates, f, indent=4)
        
        flash('Template salvo com sucesso!', 'success')
        return redirect(url_for('templates'))

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        department = request.form.get('department', '')
        
        if username in users_db:
            flash('Nome de usuário já existe', 'danger')
        else:
            users_db[username] = {
                'password': generate_password_hash(password),
                'role': role,
                'department': department
            }
            save_data()
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/ai-settings', methods=['GET', 'POST'])
@admin_required
def ai_settings():
    if request.method == 'POST':
        # Atualizar configurações de cada modelo
        for model_id in AI_MODELS:
            if f"enabled_{model_id}" in request.form:
                AI_MODELS[model_id]["enabled"] = True
            else:
                AI_MODELS[model_id]["enabled"] = False
                
            # Verificar se tem nova chave API
            new_api_key = request.form.get(f"api_key_{model_id}")
            if new_api_key:
                AI_MODELS[model_id]["api_key"] = new_api_key
            elif model_id.startswith("google-gemini") and not AI_MODELS[model_id]["api_key"]:
                # Garantir que os modelos Gemini sempre tenham pelo menos a chave padrão
                AI_MODELS[model_id]["api_key"] = DEFAULT_GEMINI_API_KEY
            
            # Atualizar outras configurações
            if f"temperature_{model_id}" in request.form:
                try:
                    temp = float(request.form.get(f"temperature_{model_id}"))
                    if 0 <= temp <= 1:
                        AI_MODELS[model_id]["temperature"] = temp
                except ValueError:
                    pass
                
            if f"max_tokens_{model_id}" in request.form:
                try:
                    tokens = int(request.form.get(f"max_tokens_{model_id}"))
                    if tokens > 0:
                        AI_MODELS[model_id]["max_tokens"] = tokens
                except ValueError:
                    pass
            
            # Atualizar modelo padrão
            if request.form.get("default_model") == model_id:
                for m_id in AI_MODELS:
                    AI_MODELS[m_id]["default"] = (m_id == model_id)
        
        save_data()
        flash('Configurações de IA atualizadas com sucesso!', 'success')
        return redirect(url_for('ai_settings'))
    
    return render_template('ai_settings.html', models=AI_MODELS)

@app.route('/user-settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Atualizar preferências do usuário
        preferred_model = request.form.get('preferred_model')
        
        if preferred_model in AI_MODELS and AI_MODELS[preferred_model]["enabled"]:
            users_db[user_id]["preferred_model"] = preferred_model
            
            # Atualizar senha se fornecida
            new_password = request.form.get('new_password')
            if new_password and len(new_password) >= 6:
                users_db[user_id]["password"] = generate_password_hash(new_password)
                flash('Senha atualizada com sucesso!', 'success')
            
            save_data()
            flash('Preferências atualizadas com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Modelo de IA selecionado não está disponível', 'danger')
    
    enabled_models = {k: v for k, v in AI_MODELS.items() if v["enabled"]}
    user_preferred_model = users_db[user_id].get("preferred_model", "")
    
    return render_template(
        'user_settings.html', 
        models=enabled_models,
        preferred_model=user_preferred_model
    )

@app.errorhandler(429)
def too_many_requests(e):
    return render_template('error.html', 
                          error_code=429,
                          error_message="Limite de requisições excedido. Por favor, tente novamente mais tarde ou use outro modelo de IA."), 429

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                          error_code=404,
                          error_message="Página não encontrada."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                          error_code=500,
                          error_message="Erro interno do servidor."), 500

if __name__ == '__main__':
    app.run(debug=True)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções de segurança.
Este módulo contém funções relacionadas à segurança, como geração e verificação de tokens.
"""

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import secrets
import string
import re


def generate_confirmation_token(email):
    """
    Gera um token seguro para confirmação de email.
    
    Args:
        email: Email a ser codificado no token
        
    Returns:
        Token seguro para confirmação
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'email-confirmation'))


def confirm_token(token, expiration=86400):
    """
    Confirma um token e retorna o email codificado.
    
    Args:
        token: Token a ser verificado
        expiration: Tempo de expiração em segundos (padrão: 24 horas)
        
    Returns:
        Email codificado no token ou None em caso de erro
        
    Raises:
        SignatureExpired: Se o token expirou
        BadSignature: Se o token é inválido
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'email-confirmation'),
            max_age=expiration
        )
        return email
    except (SignatureExpired, BadSignature):
        return None


def generate_random_password(length=12):
    """
    Gera uma senha aleatória segura.
    
    Args:
        length: Comprimento da senha (padrão: 12)
        
    Returns:
        Senha aleatória segura
    """
    # Define os caracteres permitidos
    alphabet = string.ascii_letters + string.digits + string.punctuation
    
    # Gera a senha
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Verifica se a senha atende aos critérios de segurança
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            break
    
    return password


def generate_unique_token():
    """
    Gera um token único para identificação.
    
    Returns:
        Token único
    """
    return secrets.token_urlsafe(32)


def sanitize_html(html_content):
    """
    Remove tags HTML maliciosos de um conteúdo.
    
    Args:
        html_content: Conteúdo HTML a ser sanitizado
        
    Returns:
        Conteúdo HTML sanitizado
    """
    from bleach import clean
    
    # Define as tags permitidas
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 
        'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i',
        'img', 'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 
        'tbody', 'td', 'th', 'thead', 'tr', 'ul'
    ]
    
    # Define os atributos permitidos
    allowed_attrs = {
        'a': ['href', 'title', 'target'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['border', 'cellpadding', 'cellspacing'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan', 'scope'],
        '*': ['class']  # Permite o atributo class em todas as tags
    }
    
    # Sanitiza o conteúdo
    return clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)


def validate_recaptcha(recaptcha_response):
    """
    Valida um token reCAPTCHA v3.
    
    Args:
        recaptcha_response: Token reCAPTCHA a ser validado
        
    Returns:
        True se o token for válido, False caso contrário
    """
    import requests
    
    # Verifica se o token é None ou vazio
    if not recaptcha_response:
        return False
    
    # Obtém a chave secreta do reCAPTCHA
    recaptcha_secret_key = current_app.config.get('RECAPTCHA_SECRET_KEY')
    if not recaptcha_secret_key:
        # Se a chave não estiver configurada, retorna True em desenvolvimento
        return current_app.config.get('ENV') == 'development'
    
    # Faz a requisição de verificação
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': recaptcha_secret_key,
                'response': recaptcha_response
            }
        )
        
        # Verifica a resposta
        result = response.json()
        return result.get('success', False) and result.get('score', 0) >= 0.5
    except Exception:
        return False


def mask_sensitive_data(data, fields_to_mask=None):
    """
    Mascara dados sensíveis em um dicionário ou string.
    
    Args:
        data: Dados a serem mascarados (string ou dicionário)
        fields_to_mask: Lista de campos a serem mascarados (para dicionários)
        
    Returns:
        Dados com informações sensíveis mascaradas
    """
    # Define campos padrão a serem mascarados
    default_fields = {
        'password': True,
        'senha': True,
        'credit_card': True,
        'cartao_credito': True,
        'cpf': True,
        'rg': True,
        'secret': True,
        'token': True
    }
    
    fields = fields_to_mask or default_fields
    
    if isinstance(data, str):
        # Mascara CPF/CNPJ
        data = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', 'XXX.XXX.XXX-XX', data)
        data = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', 'XX.XXX.XXX/XXXX-XX', data)
        
        # Mascara cartão de crédito
        data = re.sub(r'\b(?:\d[ -]*?){13,16}\b', 'XXXX-XXXX-XXXX-XXXX', data)
        
        # Mascara emails
        data = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email@mascarado.com', data)
        
        return data
    
    elif isinstance(data, dict):
        masked_data = data.copy()
        
        for key in data:
            # Verifica se o campo deve ser mascarado
            should_mask = False
            for field in fields:
                if field.lower() in key.lower():
                    should_mask = True
                    break
            
            if should_mask:
                if isinstance(data[key], str):
                    if key.lower() in ['password', 'senha']:
                        masked_data[key] = '********'
                    else:
                        masked_data[key] = 'XXXXXXXX'
            elif isinstance(data[key], dict):
                masked_data[key] = mask_sensitive_data(data[key], fields)
        
        return masked_data
    
    return data


def check_password_breach(password):
    """
    Verifica se uma senha foi comprometida em vazamentos conhecidos usando a API HaveIBeenPwned.
    
    Args:
        password: Senha a ser verificada
        
    Returns:
        Número de vezes que a senha apareceu em vazamentos, 0 se não foi comprometida
    """
    import hashlib
    import requests
    
    # Calcula o hash SHA-1 da senha
    password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    # Divide o hash para usar o modelo k-anonimato
    prefix, suffix = password_hash[:5], password_hash[5:]
    
    try:
        # Consulta a API
        response = requests.get(f'https://api.pwnedpasswords.com/range/{prefix}')
        
        if response.status_code != 200:
            return 0
        
        # Verifica se o sufixo está presente na resposta
        for line in response.text.splitlines():
            line_suffix, count = line.split(':')
            if line_suffix == suffix:
                return int(count)
        
        return 0
    except Exception:
        # Em caso de erro, assume que a senha não foi vazada
        return 0
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções de validação.
Este módulo contém funções para validação de dados em diversos contextos.
"""

import re
from email_validator import validate_email as validate_email_format, EmailNotValidError

def validate_email(email):
    """
    Valida se um email está em formato válido.
    
    Args:
        email: String com email a ser validado
        
    Returns:
        True se o email for válido, False caso contrário
    """
    # Verifica se o email é None ou vazio
    if not email:
        return False
    
    # Verifica se o email tem um formato válido usando email_validator
    try:
        validate_email_format(email)
        return True
    except EmailNotValidError:
        return False


def validate_password(password):
    """
    Valida a força de uma senha.
    
    Args:
        password: String com senha a ser validada
        
    Returns:
        Lista de erros encontrados ou lista vazia se a senha for válida
    """
    errors = []
    
    # Verifica se a senha é None ou vazia
    if not password:
        errors.append('A senha é obrigatória.')
        return errors
    
    # Verifica o comprimento mínimo
    if len(password) < 8:
        errors.append('A senha deve ter pelo menos 8 caracteres.')
    
    # Verifica a presença de letras maiúsculas
    if not re.search(r'[A-Z]', password):
        errors.append('A senha deve conter pelo menos uma letra maiúscula.')
    
    # Verifica a presença de letras minúsculas
    if not re.search(r'[a-z]', password):
        errors.append('A senha deve conter pelo menos uma letra minúscula.')
    
    # Verifica a presença de números
    if not re.search(r'[0-9]', password):
        errors.append('A senha deve conter pelo menos um número.')
    
    # Verifica a presença de caracteres especiais
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('A senha deve conter pelo menos um caractere especial.')
    
    return errors


def validate_slug(slug):
    """
    Valida se um slug está em formato válido.
    
    Args:
        slug: String com slug a ser validado
        
    Returns:
        True se o slug for válido, False caso contrário
    """
    # Verifica se o slug é None ou vazio
    if not slug:
        return False
    
    # Verifica o formato do slug
    return bool(re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug))


def validate_name(name):
    """
    Valida se um nome está em formato válido.
    
    Args:
        name: String com nome a ser validado
        
    Returns:
        True se o nome for válido, False caso contrário
    """
    # Verifica se o nome é None ou vazio
    if not name:
        return False
    
    # Verifica se o comprimento é razoável
    if len(name) < 2 or len(name) > 50:
        return False
    
    # Verifica se contém apenas letras, espaços e alguns caracteres especiais
    return bool(re.match(r'^[a-zA-ZÀ-ÿ\s\-\'\.]+$', name))


def validate_cpf(cpf):
    """
    Valida se um CPF está em formato válido e se o dígito verificador está correto.
    
    Args:
        cpf: String com CPF a ser validado
        
    Returns:
        True se o CPF for válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se o CPF tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Verifica o primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    if resto in [10, 11]:
        resto = 0
    if resto != int(cpf[9]):
        return False
    
    # Verifica o segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    if resto in [10, 11]:
        resto = 0
    if resto != int(cpf[10]):
        return False
    
    return True


def validate_phone(phone):
    """
    Valida se um número de telefone está em formato válido.
    
    Args:
        phone: String com telefone a ser validado
        
    Returns:
        True se o telefone for válido, False caso contrário
    """
    # Remove caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Verifica se o telefone tem entre 10 e 11 dígitos (com DDD)
    if len(phone) < 10 or len(phone) > 11:
        return False
    
    # Verifica se o DDD é válido (códigos de área do Brasil)
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    # Se tiver 11 dígitos, o primeiro dígito após o DDD deve ser 9 (celular)
    if len(phone) == 11 and phone[2] != '9':
        return False
    
    return True


def validate_date(date_str, format='%Y-%m-%d'):
    """
    Valida se uma string de data está em formato válido.
    
    Args:
        date_str: String com data a ser validada
        format: Formato esperado da data (padrão: YYYY-MM-DD)
        
    Returns:
        True se a data for válida, False caso contrário
    """
    from datetime import datetime
    
    # Verifica se a data é None ou vazia
    if not date_str:
        return False
    
    # Tenta converter a string para data
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_url(url):
    """
    Valida se uma URL está em formato válido.
    
    Args:
        url: String com URL a ser validada
        
    Returns:
        True se a URL for válida, False caso contrário
    """
    # Verifica se a URL é None ou vazia
    if not url:
        return False
    
    # Verifica o formato da URL
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domínio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ou endereço IP
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def validate_file_extension(filename, allowed_extensions):
    """
    Valida se a extensão de um arquivo é permitida.
    
    Args:
        filename: Nome do arquivo
        allowed_extensions: Lista de extensões permitidas
        
    Returns:
        True se a extensão for permitida, False caso contrário
    """
    # Verifica se o nome do arquivo é None ou vazio
    if not filename:
        return False
    
    # Obtém a extensão do arquivo
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Verifica se a extensão está na lista de extensões permitidas
    return extension in allowed_extensions
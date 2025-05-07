#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções auxiliares gerais.
Este módulo contém funções de utilidade geral para uso em toda a aplicação.
"""

import os
import re
import unicodedata
from flask import flash, current_app
from datetime import datetime, timedelta
import json
import uuid


def flash_errors(form):
    """
    Flash de todos os erros de um formulário WTForms.
    
    Args:
        form: Formulário WTForms
    """
    for field, errors in form.errors.items():
        for error in errors:
            field_name = getattr(form, field).label.text
            flash(f'Erro no campo "{field_name}": {error}', 'danger')


def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """
    Formata um objeto datetime para string.
    
    Args:
        dt: Objeto datetime a ser formatado
        format: Formato desejado (padrão: DD/MM/YYYY HH:MM)
        
    Returns:
        String formatada ou string vazia se dt for None
    """
    if dt is None:
        return ''
    return dt.strftime(format)


def parse_datetime(dt_str, format='%d/%m/%Y %H:%M'):
    """
    Converte uma string para objeto datetime.
    
    Args:
        dt_str: String com data e hora
        format: Formato da string (padrão: DD/MM/YYYY HH:MM)
        
    Returns:
        Objeto datetime ou None em caso de erro
    """
    try:
        return datetime.strptime(dt_str, format)
    except (ValueError, TypeError):
        return None


def slugify(text):
    """
    Converte um texto para formato de slug (URL amigável).
    
    Args:
        text: Texto a ser convertido
        
    Returns:
        Slug gerado
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove non-word characters (everything except numbers and letters)
    text = re.sub(r'[^\w\-]', '', text)
    
    # Replace multiple hyphens with a single hyphen
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text


def format_bytes(size, decimal_places=2):
    """
    Formata um tamanho em bytes para formato legível (KB, MB, GB, etc).
    
    Args:
        size: Tamanho em bytes
        decimal_places: Número de casas decimais (padrão: 2)
        
    Returns:
        String formatada
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def date_range(start_date, end_date, delta=timedelta(days=1)):
    """
    Gera um intervalo de datas.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        delta: Intervalo entre datas (padrão: 1 dia)
        
    Returns:
        Gerador de datas
    """
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += delta


def get_file_extension(filename):
    """
    Obtém a extensão de um arquivo.
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Extensão do arquivo (sem o ponto) ou string vazia
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def allowed_file(filename, allowed_extensions):
    """
    Verifica se a extensão de um arquivo é permitida.
    
    Args:
        filename: Nome do arquivo
        allowed_extensions: Lista de extensões permitidas
        
    Returns:
        True se permitido, False caso contrário
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def secure_filename(filename):
    """
    Torna um nome de arquivo seguro para armazenamento.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome de arquivo seguro
    """
    # Obtém a extensão
    ext = get_file_extension(filename)
    
    # Gera um nome aleatório
    random_name = str(uuid.uuid4())
    
    # Retorna o nome seguro com a extensão original
    return f"{random_name}.{ext}" if ext else random_name


def save_uploaded_file(file, upload_folder, allowed_extensions=None):
    """
    Salva um arquivo enviado pelo usuário.
    
    Args:
        file: Objeto de arquivo (request.files)
        upload_folder: Pasta onde o arquivo será salvo
        allowed_extensions: Lista de extensões permitidas
        
    Returns:
        Caminho do arquivo salvo ou None em caso de erro
    """
    # Verifica se o arquivo existe
    if not file or file.filename == '':
        return None
    
    # Verifica se a extensão é permitida
    if allowed_extensions and not allowed_file(file.filename, allowed_extensions):
        return None
    
    # Torna o nome do arquivo seguro
    filename = secure_filename(file.filename)
    
    # Cria a pasta de destino se não existir
    os.makedirs(upload_folder, exist_ok=True)
    
    # Define o caminho completo
    filepath = os.path.join(upload_folder, filename)
    
    # Salva o arquivo
    file.save(filepath)
    
    return filepath


def json_serial(obj):
    """
    Função auxiliar para serialização JSON de objetos datetime e outros tipos complexos.
    
    Args:
        obj: Objeto a ser serializado
        
    Returns:
        Representação serializável do objeto
    """
    if isinstance(obj, (datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Tipo {type(obj)} não é serializável")


def to_json(data):
    """
    Converte dados para formato JSON.
    
    Args:
        data: Dados a serem convertidos
        
    Returns:
        String JSON
    """
    return json.dumps(data, default=json_serial, ensure_ascii=False)


def from_json(json_str):
    """
    Converte string JSON para dados Python.
    
    Args:
        json_str: String JSON
        
    Returns:
        Dados Python ou None em caso de erro
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def truncate_text(text, max_length=100, suffix='...'):
    """
    Trunca um texto para o tamanho máximo.
    
    Args:
        text: Texto a ser truncado
        max_length: Tamanho máximo (padrão: 100)
        suffix: Sufixo a ser adicionado em caso de truncamento (padrão: '...')
        
    Returns:
        Texto truncado
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + suffix


def strip_html_tags(html):
    """
    Remove tags HTML de um texto.
    
    Args:
        html: Texto HTML
        
    Returns:
        Texto sem tags HTML
    """
    import re
    
    # Remove tags HTML
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)


def is_valid_uuid(val):
    """
    Verifica se uma string é um UUID válido.
    
    Args:
        val: String a ser verificada
        
    Returns:
        True se for um UUID válido, False caso contrário
    """
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def get_pagination_info(page, per_page, total_count):
    """
    Obtém informações para paginação.
    
    Args:
        page: Página atual
        per_page: Itens por página
        total_count: Contagem total de itens
        
    Returns:
        Dicionário com informações de paginação
    """
    # Calcula o total de páginas
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
    
    # Calcula o offset (índice do primeiro item na página)
    offset = (page - 1) * per_page
    
    # Verifica se há página anterior/próxima
    has_prev = page > 1
    has_next = page < total_pages
    
    # Calcula intervalos de exibição
    start_item = offset + 1 if total_count > 0 else 0
    end_item = min(offset + per_page, total_count)
    
    return {
        'page': page,
        'per_page': per_page,
        'total_count': total_count,
        'total_pages': total_pages,
        'offset': offset,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_page': page - 1 if has_prev else None,
        'next_page': page + 1 if has_next else None,
        'start_item': start_item,
        'end_item': end_item
    }


def time_since(dt, default="agora mesmo"):
    """
    Retorna uma string descrevendo quanto tempo passou desde a data fornecida.
    
    Args:
        dt: Data de referência
        default: Texto a ser retornado se o tempo for muito pequeno
        
    Returns:
        String descritiva
    """
    now = datetime.now()
    
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    
    if dt is None:
        return default
    
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 10:
        return default
    elif seconds < 60:
        return f"{int(seconds)} segundos atrás"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minuto{'s' if minutes > 1 else ''} atrás"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hora{'s' if hours > 1 else ''} atrás"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} dia{'s' if days > 1 else ''} atrás"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} semana{'s' if weeks > 1 else ''} atrás"
    else:
        return format_datetime(dt, format='%d/%m/%Y')


def get_client_ip():
    """
    Obtém o endereço IP do cliente.
    
    Returns:
        String com o endereço IP
    """
    from flask import request
    
    # Tenta obter o IP do cabeçalho X-Forwarded-For
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        # Caso contrário, usa o IP remoto
        ip = request.remote_addr
    
    return ip


def get_random_color():
    """
    Gera uma cor aleatória em formato hexadecimal.
    
    Returns:
        String com código de cor hexadecimal
    """
    import random
    
    # Gera uma cor aleatória
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_color_palette(n=5):
    """
    Gera uma paleta de cores.
    
    Args:
        n: Número de cores a serem geradas (padrão: 5)
        
    Returns:
        Lista com n cores em formato hexadecimal
    """
    import random
    
    colors = []
    for _ in range(n):
        # Gera uma cor aleatória
        h = random.random()  # Matiz (0-1)
        s = 0.5 + random.random() * 0.5  # Saturação (0.5-1)
        l = 0.4 + random.random() * 0.2  # Luminosidade (0.4-0.6)
        
        # Converte de HSL para RGB
        colors.append(hsl_to_hex(h, s, l))
    
    return colors


def hsl_to_hex(h, s, l):
    """
    Converte cores de formato HSL para hexadecimal.
    
    Args:
        h: Matiz (0-1)
        s: Saturação (0-1)
        l: Luminosidade (0-1)
        
    Returns:
        String com código de cor hexadecimal
    """
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p
    
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    # Converte para hexadecimal
    r_hex = round(r * 255)
    g_hex = round(g * 255)
    b_hex = round(b * 255)
    
    return f"#{r_hex:02x}{g_hex:02x}{b_hex:02x}"
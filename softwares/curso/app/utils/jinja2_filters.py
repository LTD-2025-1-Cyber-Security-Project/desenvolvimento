#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filtros personalizados para templating Jinja2.
Este módulo define filtros personalizados que podem ser usados nos templates.
"""

from datetime import datetime


def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """
    Formata um objeto datetime ou string ISO para exibição.
    
    Args:
        value: O valor de datetime a ser formatado (objeto datetime ou string ISO)
        format: Formato de saída (padrão: DD/MM/YYYY HH:MM)
        
    Returns:
        String formatada ou string vazia se value for None
    """
    if value is None:
        return ''
        
    # Se for uma string ISO, converte para datetime
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return value
            
    # Formata o datetime
    if isinstance(value, datetime):
        return value.strftime(format)
        
    return value


def register_filters(app):
    """
    Registra filtros personalizados no aplicativo Flask.
    
    Args:
        app: Instância do aplicativo Flask
    """
    app.jinja_env.filters['datetime'] = format_datetime
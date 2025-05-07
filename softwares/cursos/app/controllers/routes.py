#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rotas principais da aplicação.
Este módulo contém as rotas básicas do sistema, como a página inicial.
"""

from flask import Blueprint, redirect, url_for
from flask_login import current_user

# Criação do Blueprint de rotas principais
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota para a página inicial.
    
    Redireciona para o dashboard se o usuário estiver autenticado,
    ou para a página de login caso contrário.
    """
    if current_user.is_authenticated:
        return redirect(url_for('courses.dashboard'))
    else:
        return redirect(url_for('auth.login'))


@main_bp.route('/sobre')
def about():
    """Rota para a página Sobre."""
    return redirect(url_for('main.index'))


@main_bp.route('/contato')
def contact():
    """Rota para a página de Contato."""
    return redirect(url_for('main.index'))
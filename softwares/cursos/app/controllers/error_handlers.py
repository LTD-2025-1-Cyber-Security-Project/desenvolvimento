#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manipuladores de erro.
Este módulo contém funções para tratar diversos erros HTTP.
"""

from flask import render_template, request, jsonify
import traceback
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Registra manipuladores de erro na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Manipulador para erro 400 Bad Request."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Requisição inválida',
                'message': str(error),
                'status_code': 400
            }), 400
        return render_template('errors/400.html', error=error), 400
    
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Manipulador para erro 401 Unauthorized."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Não autorizado',
                'message': 'Você não está autorizado a acessar este recurso',
                'status_code': 401
            }), 401
        return render_template('errors/401.html', error=error), 401
    
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Manipulador para erro 403 Forbidden."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Acesso proibido',
                'message': 'Você não tem permissão para acessar este recurso',
                'status_code': 403
            }), 403
        return render_template('errors/403.html', error=error), 403
    
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Manipulador para erro 404 Not Found."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Não encontrado',
                'message': 'O recurso solicitado não foi encontrado',
                'status_code': 404
            }), 404
        return render_template('errors/404.html', error=error), 404
    
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Manipulador para erro 405 Method Not Allowed."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Método não permitido',
                'message': f'O método {request.method} não é permitido para este recurso',
                'status_code': 405
            }), 405
        return render_template('errors/405.html', error=error), 405
    
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        """Manipulador para erro 429 Too Many Requests."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Muitas requisições',
                'message': 'Você enviou muitas requisições. Por favor, tente novamente mais tarde.',
                'status_code': 429
            }), 429
        return render_template('errors/429.html', error=error), 429
    
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Manipulador para erro 500 Internal Server Error."""
        # Registra o erro no log
        logger.error(f"Erro 500: {str(error)}")
        logger.error(traceback.format_exc())
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Erro interno do servidor',
                'message': 'Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde.',
                'status_code': 500
            }), 500
        return render_template('errors/500.html', error=error), 500
    
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        """Manipulador para erro 503 Service Unavailable."""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Serviço indisponível',
                'message': 'O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde.',
                'status_code': 503
            }), 503
        return render_template('errors/503.html', error=error), 503
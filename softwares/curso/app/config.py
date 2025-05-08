#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurações da aplicação.
Este módulo define as configurações para diferentes ambientes
(desenvolvimento, teste, produção).
"""

import os
from datetime import timedelta

class Config:
    """Configuração base para todos os ambientes."""
    
    # Configurações gerais
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao-alterar-em-producao'
    APP_NAME = 'EdTech IA & Cyber'
    APP_VERSION = '1.0.0'
    
    # Configurações de banco de dados
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-chave-secreta-padrao-alterar-em-producao'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Configurações de e-mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@edtech-ia-cyber.gov.br')
    
    # Configurações de cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de APIs externas
    GOOGLE_GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY', 'AIzaSyCY5JQRIAZlq7Re-GNDtwn8b1Hmza_hk8Y')
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
    
    # Configurações de upload de arquivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}
    
    @staticmethod
    def init_app(app):
        """Inicializa a aplicação com esta configuração."""
        # Cria diretório de upload se não existir
        os.makedirs(os.path.join(os.getcwd(), 'app/static/uploads'), exist_ok=True)


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    
    DEBUG = True
    ENV = 'development'
    # Alterado para SQLite para facilitar o desenvolvimento
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:////' + os.path.join(os.getcwd(), 'edtech_dev.db')
    
    # Cache para desenvolvimento
    CACHE_TYPE = 'SimpleCache'


class TestingConfig(Config):
    """Configuração para ambiente de teste."""
    
    TESTING = True
    ENV = 'testing'
    # Alterado para SQLite em memória para testes
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Para testes mais rápidos
    BCRYPT_LOG_ROUNDS = 4
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=10)
    

class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    
    DEBUG = False
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Configurações de segurança para produção
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Cache para produção (recomendado Redis em produção)
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    @staticmethod
    def init_app(app):
        """Inicializa a aplicação para o ambiente de produção."""
        Config.init_app(app)
        
        # Configuração de log para produção
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Cria diretório de logs se não existir
        os.makedirs('logs', exist_ok=True)
        
        file_handler = RotatingFileHandler('logs/edtech.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('EdTech IA & Cyber inicializado')


# Mapeamento de configurações
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
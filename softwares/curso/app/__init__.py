#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inicialização da aplicação Flask.
Este módulo configura a aplicação Flask, incluindo todas as extensões e blueprints.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS
from flask_caching import Cache
import os
from dotenv import load_dotenv
from app.utils import jinja2_filters

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa as extensões Flask
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
cache = Cache()

def create_app(config_name='default'):
    """Função de fábrica da aplicação Flask."""
    # Cria a aplicação - vamos usar a estrutura padrão de diretórios do Flask
    app = Flask(__name__)
    
    # Configurações
    from app.config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # Inicializa as extensões com a aplicação
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    bcrypt.init_app(app)
    mail.init_app(app)
    CORS(app)
    cache.init_app(app)
    
    # Configuração do carregador de usuário para o Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Registra blueprints
    from app.controllers.routes import main_bp
    from app.controllers.auth import auth_bp
    from app.controllers.courses import courses_bp
    from app.controllers.quizzes import quizzes_bp
    from app.controllers.admin import admin_bp
    from app.controllers.api import api_bp
    
    app.register_blueprint(main_bp)  # Registra o blueprint principal com as rotas básicas
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Registra manipuladores de erro
    from app.controllers import error_handlers
    error_handlers.register_error_handlers(app)
    
    # Registra comandos CLI
    from app.utils import cli_commands
    cli_commands.register_commands(app)
    
    # Registra filtros Jinja2 personalizados
    from app.utils import jinja2_filters
    jinja2_filters.register_filters(app)
    
    # Cria todas as tabelas do banco de dados se estiver em modo de desenvolvimento
    with app.app_context():
        if app.config['ENV'] == 'development':
            db.create_all()
    
    return app
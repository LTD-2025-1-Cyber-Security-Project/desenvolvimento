#!/usr/bin/env python3
"""
Módulo de gerenciamento de autenticação para o sistema NexusInfo.
Responsável por registro, login e gerenciamento de usuários.
"""

import os
import uuid
import hashlib
import datetime
import json
from pathlib import Path

# Classe de usuário
class User:
    """Classe que representa um usuário do sistema"""
    
    def __init__(self, username, email=None, fullname=None, user_id=None, created_at=None):
        """Inicializa um objeto de usuário"""
        self.username = username
        self.email = email or ""
        self.fullname = fullname or username
        self.user_id = user_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    def __str__(self):
        """Representação em string do usuário"""
        return f"User({self.username}, {self.email})"
    
    def to_dict(self):
        """Converte o usuário para um dicionário"""
        return {
            "username": self.username,
            "email": self.email,
            "fullname": self.fullname,
            "user_id": self.user_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria um usuário a partir de um dicionário"""
        return cls(
            username=data.get("username"),
            email=data.get("email"),
            fullname=data.get("fullname"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at")
        )

# Classe de gerenciamento de autenticação
class AuthManager:
    """Gerencia autenticação de usuários"""
    
    def __init__(self, db_manager):
        """Inicializa o gerenciador de autenticação"""
        self.db_manager = db_manager
        
        # Garantir que as tabelas existam
        self.db_manager.ensure_tables()
    
    def register(self, username, password, email=None, fullname=None):
        """Registra um novo usuário"""
        # Verificar se o usuário já existe
        if self.db_manager.user_exists(username):
            raise ValueError(f"Usuário '{username}' já existe")
        
        # Criar hash da senha
        password_hash = self._hash_password(password)
        
        # Criar usuário
        user = User(username, email, fullname)
        
        # Salvar no banco de dados
        self.db_manager.add_user(user, password_hash)
        
        return user
    
    def login(self, username, password):
        """Realiza login de um usuário"""
        # Verificar se o usuário existe
        if not self.db_manager.user_exists(username):
            return None
        
        # Verificar senha
        if not self.verify_password(username, password):
            return None
        
        # Obter dados do usuário
        user_data = self.db_manager.get_user(username)
        
        # Criar objeto de usuário
        user = User.from_dict(user_data)
        
        return user
    
    def verify_password(self, username, password):
        """Verifica se a senha está correta"""
        # Obter hash da senha armazenada
        stored_hash = self.db_manager.get_password_hash(username)
        
        if not stored_hash:
            return False
        
        # Verificar hash
        password_hash = self._hash_password(password)
        
        return password_hash == stored_hash
    
    def update_password(self, username, new_password):
        """Atualiza a senha de um usuário"""
        # Verificar se o usuário existe
        if not self.db_manager.user_exists(username):
            return False
        
        # Criar hash da nova senha
        password_hash = self._hash_password(new_password)
        
        # Atualizar no banco de dados
        return self.db_manager.update_password(username, password_hash)
    
    def get_user_email(self, username):
        """Obtém o email de um usuário pelo username"""
        user_data = self.db_manager.get_user(username)
        if user_data:
            return user_data.get("email", "")
        return None
    
    def _hash_password(self, password):
        """Cria um hash da senha"""
        # Em uma aplicação real, usaríamos algo como bcrypt
        # Aqui vamos usar o hashlib para simplificar
        salt = "nexusinfo_salt"  # Em uma aplicação real, seria um valor único por usuário
        password_with_salt = password + salt
        return hashlib.sha256(password_with_salt.encode('utf-8')).hexdigest()
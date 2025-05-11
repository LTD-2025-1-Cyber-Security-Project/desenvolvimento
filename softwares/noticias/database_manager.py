#!/usr/bin/env python3
"""
Módulo de gerenciamento de banco de dados para o sistema NexusInfo.
Responsável por armazenar e recuperar dados de usuários e notícias.
"""

import os
import json
import sqlite3
import datetime
from pathlib import Path

# Diretório base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "nexusinfo.db"

# Garantir que o diretório de dados exista
DATA_DIR.mkdir(exist_ok=True)

class DatabaseManager:
    """Gerencia a conexão e operações com o banco de dados"""
    
    def __init__(self, db_file=DB_FILE):
        """Inicializa o gerenciador de banco de dados"""
        self.db_file = db_file
        
        # Garantir que o banco de dados exista
        self.ensure_tables()
    
    def get_connection(self):
        """Obtém uma conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Para obter resultados como dicionários
        return conn
    
    def ensure_tables(self):
        """Garante que as tabelas necessárias existam"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            fullname TEXT,
            created_at TEXT
        )
        ''')
        
        # Tabela de notícias salvas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_news (
            news_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            category TEXT,
            source TEXT,
            date TEXT,
            content TEXT,
            url TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Tabela de histórico de pesquisas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            search_id TEXT PRIMARY KEY,
            user_id TEXT,
            query TEXT NOT NULL,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            setting_id TEXT PRIMARY KEY,
            user_id TEXT,
            theme TEXT,
            notifications BOOLEAN,
            sounds BOOLEAN,
            api_key TEXT,
            last_updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    # === Operações de usuário ===
    
    def user_exists(self, username):
        """Verifica se um usuário existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def add_user(self, user, password_hash):
        """Adiciona um novo usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (user_id, username, password_hash, email, fullname, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user.user_id, user.username, password_hash, user.email, user.fullname, user.created_at)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user(self, username):
        """Obtém dados de um usuário pelo username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    def get_password_hash(self, username):
        """Obtém o hash da senha de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result['password_hash']
        return None
    
    def update_password(self, username, password_hash):
        """Atualiza a senha de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_user_profile(self, username, email=None, fullname=None):
        """Atualiza o perfil de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        
        if fullname is not None:
            updates.append("fullname = ?")
            params.append(fullname)
        
        if not updates:
            return False
        
        params.append(username)
        
        try:
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE username = ?",
                tuple(params)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # === Operações de notícias ===
    
    def save_news(self, user_id, title, category, source=None, date=None, content=None, url=None):
        """Salva uma notícia para um usuário"""
        news_id = os.urandom(16).hex()
        created_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO saved_news 
                (news_id, user_id, title, category, source, date, content, url, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (news_id, user_id, title, category, source, date, content, url, created_at)
            )
            conn.commit()
            return news_id
        except sqlite3.Error:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_saved_news(self, user_id):
        """Obtém as notícias salvas de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM saved_news WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        results = cursor.fetchall()
        
        conn.close()
        
        if results:
            return [dict(row) for row in results]
        return []
    
    def delete_saved_news(self, news_id, user_id):
        """Exclui uma notícia salva"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM saved_news WHERE news_id = ? AND user_id = ?",
                (news_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_news_details(self, news_id):
        """Obtém detalhes de uma notícia pelo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM saved_news WHERE news_id = ?", (news_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    # === Operações de histórico de pesquisa ===
    
    def add_search_history(self, user_id, query):
        """Adiciona uma pesquisa ao histórico"""
        search_id = os.urandom(16).hex()
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO search_history (search_id, user_id, query, timestamp) VALUES (?, ?, ?, ?)",
                (search_id, user_id, query, timestamp)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_search_history(self, user_id, limit=10):
        """Obtém o histórico de pesquisas de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM search_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", 
            (user_id, limit)
        )
        results = cursor.fetchall()
        
        conn.close()
        
        if results:
            return [dict(row) for row in results]
        return []
    
    def clear_search_history(self, user_id):
        """Limpa o histórico de pesquisas de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM search_history WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # === Operações de configurações ===
    
    def save_settings(self, user_id, theme=None, notifications=None, sounds=None, api_key=None):
        """Salva configurações do usuário"""
        last_updated = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        setting_id = user_id  # Usar o ID do usuário como ID das configurações
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem configurações para este usuário
        cursor.execute("SELECT 1 FROM settings WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone() is not None
        
        try:
            if exists:
                # Construir a query de atualização
                updates = []
                params = []
                
                if theme is not None:
                    updates.append("theme = ?")
                    params.append(theme)
                
                if notifications is not None:
                    updates.append("notifications = ?")
                    params.append(1 if notifications else 0)
                
                if sounds is not None:
                    updates.append("sounds = ?")
                    params.append(1 if sounds else 0)
                
                if api_key is not None:
                    updates.append("api_key = ?")
                    params.append(api_key)
                
                updates.append("last_updated = ?")
                params.append(last_updated)
                
                params.append(user_id)
                
                cursor.execute(
                    f"UPDATE settings SET {', '.join(updates)} WHERE user_id = ?",
                    tuple(params)
                )
            else:
                # Inserir novas configurações
                cursor.execute(
                    """
                    INSERT INTO settings 
                    (setting_id, user_id, theme, notifications, sounds, api_key, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        setting_id, 
                        user_id, 
                        theme or "dark", 
                        1 if notifications is None else (1 if notifications else 0), 
                        1 if sounds is None else (1 if sounds else 0), 
                        api_key, 
                        last_updated
                    )
                )
            
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_settings(self, user_id):
        """Obtém as configurações de um usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            # Converter os valores booleanos
            settings = dict(result)
            settings['notifications'] = bool(settings['notifications'])
            settings['sounds'] = bool(settings['sounds'])
            return settings
        
        # Configurações padrão
        return {
            "user_id": user_id,
            "theme": "dark",
            "notifications": True,
            "sounds": True,
            "api_key": None,
            "last_updated": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
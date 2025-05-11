#!/usr/bin/env python3
"""
DocMaster Pro - Script de Configuração do Banco de Dados
Este script cria as tabelas do banco de dados usando a mesma definição
de modelos que o aplicativo Flask usa, garantindo compatibilidade.
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path

def print_status(message, success=None):
    """Imprime uma mensagem de status com formatação"""
    if success is None:
        print(message)
    elif success:
        print(f"{message} [OK]")
    else:
        print(f"{message} [ERRO]")

def main():
    """Função principal para inicializar o banco de dados"""
    print("\n" + "="*70)
    print("    CONFIGURAÇÃO DO BANCO DE DADOS DOCMASTER PRO")
    print("="*70 + "\n")
    
    # Determina o caminho do banco de dados
    instance_dir = Path("instance")
    db_path = instance_dir / "app.sqlite"
    
    # Cria o diretório instance se não existir
    instance_dir.mkdir(exist_ok=True)
    print_status("Diretório instance verificado", True)
    
    # Backup do banco existente (se houver)
    if db_path.exists():
        # Verifica se o banco já tem as tabelas
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if 'document' in tables:
            print_status("Tabela 'document' já existe no banco de dados", True)
            print_status("Nenhuma ação necessária", True)
            return
        
        # Se não tem as tabelas, faz backup e recria
        backup_path = db_path.with_suffix('.sqlite.bak')
        shutil.copy2(db_path, backup_path)
        print_status(f"Backup do banco de dados criado em {backup_path}", True)
    
    # Abre conexão com o banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela document
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category TEXT,
        tags TEXT,
        processed BOOLEAN DEFAULT 0,
        file_hash TEXT,
        user_id INTEGER
    )
    ''')
    print_status("Tabela 'document' criada", True)
    
    # Cria a tabela user
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE,
        active BOOLEAN DEFAULT 1,
        last_login TIMESTAMP
    )
    ''')
    print_status("Tabela 'user' criada", True)
    
    # Cria a tabela processed_document
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_document (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        text_content TEXT,
        metadata TEXT,
        processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES document (id)
    )
    ''')
    print_status("Tabela 'processed_document' criada", True)
    
    # Insere um usuário de teste para garantir que o sistema funcione
    try:
        cursor.execute('''
        INSERT INTO user (username, password, email, active)
        VALUES (?, ?, ?, ?)
        ''', ('admin', 'pbkdf2:sha256:150000$tOZ9akr7$d9de0e1c258f41fd0ad5a3a1162fb3538d4c3d6450412080bb41ed69da15a87c', 'admin@example.com', 1))
        print_status("Usuário de teste 'admin' criado (senha: 'admin')", True)
    except sqlite3.IntegrityError:
        print_status("Usuário 'admin' já existe", True)
    
    # Commit e fecha a conexão
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print("    BANCO DE DADOS CONFIGURADO COM SUCESSO!")
    print("="*70)
    print("\nAgora você pode executar o aplicativo com 'python run.py' e selecionar a opção 2.")

if __name__ == "__main__":
    main()
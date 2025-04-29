#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para inserir usuários administradores no banco de dados do
Sistema de Envio de E-mails para Prefeituras.

Este script adiciona dois administradores:
1. Um para São José (senha: admin@sj123)
2. Um para Florianópolis (senha: admin@fpolis2505)
"""

import sqlite3
import hashlib
import os

# Caminho do banco de dados
DB_FILE = 'prefeituras_email.db'

def inserir_administradores():
    """Insere os usuários administradores no banco de dados."""
    
    # Verifica se o banco de dados existe
    if not os.path.exists(DB_FILE):
        print(f"Erro: Banco de dados '{DB_FILE}' não encontrado.")
        print("Verifique se o sistema já foi inicializado pelo menos uma vez.")
        return False
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verifica se a tabela 'usuarios' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            print("Erro: Tabela 'usuarios' não encontrada no banco de dados.")
            print("Verifique se o sistema já foi inicializado pelo menos uma vez.")
            conn.close()
            return False
        
        # Senhas personalizadas para cada prefeitura
        senha_sj = 'admin@sj123'
        senha_fpolis = 'admin@fpolis2505'
        
        # Gera hash das senhas
        senha_hash_sj = hashlib.sha256(senha_sj.encode()).hexdigest()
        senha_hash_fpolis = hashlib.sha256(senha_fpolis.encode()).hexdigest()
        
        # Verifica se o administrador de SJ já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", ('admin.sj@saojose.sc.gov.br',))
        if cursor.fetchone():
            print("Administrador de São José já existe no banco de dados.")
            # Atualiza a senha caso já exista
            cursor.execute('''
            UPDATE usuarios SET senha = ? WHERE email = ?
            ''', (senha_hash_sj, 'admin.sj@saojose.sc.gov.br'))
            print("Senha do administrador de São José atualizada com sucesso!")
        else:
            # Insere o administrador de São José
            cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, prefeitura, cargo, departamento, nivel_acesso)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Administrador SJ', 'admin.sj@saojose.sc.gov.br', senha_hash_sj, 'sj', 'Administrador', 'TI', 3))
            print("Administrador de São José inserido com sucesso!")
        
        # Verifica se o administrador de Florianópolis já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", ('admin.floripa@pmf.sc.gov.br',))
        if cursor.fetchone():
            print("Administrador de Florianópolis já existe no banco de dados.")
            # Atualiza a senha caso já exista
            cursor.execute('''
            UPDATE usuarios SET senha = ? WHERE email = ?
            ''', (senha_hash_fpolis, 'admin.floripa@pmf.sc.gov.br'))
            print("Senha do administrador de Florianópolis atualizada com sucesso!")
        else:
            # Insere o administrador de Florianópolis
            cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, prefeitura, cargo, departamento, nivel_acesso)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Administrador Floripa', 'admin.floripa@pmf.sc.gov.br', senha_hash_fpolis, 'floripa', 'Administrador', 'TI', 3))
            print("Administrador de Florianópolis inserido com sucesso!")
        
        # Salva as alterações
        conn.commit()
        conn.close()
        
        print("\nOperação concluída com sucesso!")
        print("Senhas dos administradores:")
        print(f"  São José: {senha_sj}")
        print(f"  Florianópolis: {senha_fpolis}")
        
        return True
    
    except Exception as e:
        print(f"Erro ao inserir administradores: {e}")
        return False

if __name__ == "__main__":
    print("===================================================")
    print("  Inserção de Administradores no Banco de Dados")
    print("===================================================")
    print()
    
    inserir_administradores()
    
    print("\nPressione Enter para sair...")
    input()
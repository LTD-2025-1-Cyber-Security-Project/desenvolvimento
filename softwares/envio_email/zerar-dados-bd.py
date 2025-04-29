#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para resetar o banco de dados do Sistema de Envio de E-mails para Prefeituras.
Este script vai apagar todos os dados e reiniciar as sequências de IDs.

Autor: LTD
Data: Abril 2025
"""

import os
import sqlite3
import datetime
import json
import shutil

# Diretório base do aplicativo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'prefeituras_email.db')
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'config.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

def criar_backup_antes_de_resetar():
    """Cria um backup do banco de dados antes de resetá-lo."""
    if not os.path.exists(DB_FILE):
        print("Banco de dados não encontrado. Não é necessário fazer backup.")
        return
    
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"backup_antes_reset_{data_atual}.db"
    caminho_backup = os.path.join(BACKUP_DIR, nome_backup)
    
    shutil.copy2(DB_FILE, caminho_backup)
    print(f"Backup criado em: {caminho_backup}")

def restaurar_configuracoes_padrao():
    """Restaura as configurações padrão do sistema."""
    config_padrao = {
        'prefeitura_padrao': 'sj',
        'smtp': {
            'sj': {
                'servidor': 'smtp.gmail.com',
                'porta': 587,
                'usuario': '',
                'senha': '',
                'tls': True,
                'ssl': False
            },
            'floripa': {
                'servidor': 'smtp.gmail.com',
                'porta': 587,
                'usuario': '',
                'senha': '',
                'tls': True,
                'ssl': False
            }
        },
        'assinaturas': {
            'sj': {
                'padrao': '''
                <p>Atenciosamente,</p>
                <p><strong>{nome}</strong><br>
                {cargo}<br>
                {departamento}<br>
                Prefeitura Municipal de São José<br>
                Telefone: {telefone}</p>
                '''
            },
            'floripa': {
                'padrao': '''
                <p>Atenciosamente,</p>
                <p><strong>{nome}</strong><br>
                {cargo}<br>
                {departamento}<br>
                Prefeitura Municipal de Florianópolis<br>
                Telefone: {telefone}</p>
                '''
            }
        },
        'backup': {
            'automatico': True,
            'intervalo': 'diario',
            'hora': '23:00'
        }
    }
    
    # Garante que o diretório de configuração existe
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    # Salva as configurações padrão
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_padrao, f, ensure_ascii=False, indent=4)
    
    print(f"Configurações restauradas para o padrão: {CONFIG_FILE}")

def resetar_banco_dados():
    """Reseta o banco de dados, apagando todos os dados e reiniciando as sequências de IDs."""
    if os.path.exists(DB_FILE):
        # Primeiro exclui o arquivo existente
        os.remove(DB_FILE)
        print(f"Banco de dados excluído: {DB_FILE}")
    
    # Cria uma nova conexão, o que criará um novo arquivo vazio
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Recria as tabelas
    
    # Tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        prefeitura TEXT NOT NULL,
        cargo TEXT,
        departamento TEXT,
        telefone TEXT,
        nivel_acesso INTEGER NOT NULL DEFAULT 1,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ultimo_acesso TIMESTAMP
    )
    ''')
    
    # Tabela de funcionários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        cargo TEXT,
        departamento TEXT,
        telefone TEXT,
        prefeitura TEXT NOT NULL,
        ativo INTEGER NOT NULL DEFAULT 1
    )
    ''')
    
    # Tabela de grupos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        prefeitura TEXT NOT NULL
    )
    ''')
    
    # Tabela de relacionamento entre grupos e funcionários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grupo_funcionario (
        grupo_id INTEGER,
        funcionario_id INTEGER,
        PRIMARY KEY (grupo_id, funcionario_id),
        FOREIGN KEY (grupo_id) REFERENCES grupos (id),
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
    )
    ''')
    
    # Tabela de templates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        assunto TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        prefeitura TEXT NOT NULL,
        departamento TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ultima_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de e-mails enviados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails_enviados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        assunto TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        destinatarios TEXT NOT NULL,
        data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    
    # Tabela de e-mails agendados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails_agendados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        assunto TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        destinatarios TEXT NOT NULL,
        data_agendada TIMESTAMP NOT NULL,
        recorrencia TEXT,
        anexos TEXT,
        recorrencia_opcoes TEXT,
        status TEXT NOT NULL DEFAULT 'pendente',
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    
    # Tabela de logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        descricao TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    
    # Cria usuário administrador padrão
    # Senha 'admin' com hash SHA-256
    import hashlib
    senha_hash = hashlib.sha256('admin'.encode()).hexdigest()
    
    cursor.execute('''
    INSERT INTO usuarios (nome, email, senha, prefeitura, cargo, departamento, nivel_acesso)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Administrador', 'admin@admin.com', senha_hash, 'sj', 'Administrador', 'TI', 3))
    
    # Cria um registro de log para o reset
    cursor.execute('''
    INSERT INTO logs (acao, descricao)
    VALUES (?, ?)
    ''', ('RESET_SISTEMA', 'Banco de dados resetado completamente'))
    
    conn.commit()
    conn.close()
    
    print("Banco de dados recriado com sucesso.")
    print("Usuário administrador padrão criado:")
    print("  Email: admin@admin.com")
    print("  Senha: admin")

def limpar_anexos_agendados():
    """Limpa a pasta de anexos agendados."""
    anexos_dir = os.path.join(BASE_DIR, 'anexos_agendados')
    if os.path.exists(anexos_dir):
        shutil.rmtree(anexos_dir)
        os.makedirs(anexos_dir)
        print(f"Pasta de anexos agendados limpa: {anexos_dir}")

def main():
    print("=" * 60)
    print("RESET DO BANCO DE DADOS DO SISTEMA DE E-MAILS".center(60))
    print("=" * 60)
    print("\nATENÇÃO: Este script irá apagar todos os dados do sistema!")
    print("Isso inclui usuários, funcionários, templates, e-mails enviados, agendamentos, etc.")
    print("\nUm backup será criado antes do reset.")
    
    confirmacao = input("\nDigite 'CONFIRMAR' para continuar: ")
    
    if confirmacao.upper() != "CONFIRMAR":
        print("Operação cancelada pelo usuário.")
        return
    
    print("\nIniciando processo de reset...\n")
    
    # Cria backup antes de resetar
    criar_backup_antes_de_resetar()
    
    # Restaura configurações padrão
    restaurar_configuracoes_padrao()
    
    # Reseta o banco de dados
    resetar_banco_dados()
    
    # Limpa a pasta de anexos agendados
    limpar_anexos_agendados()
    
    print("\n" + "=" * 60)
    print("RESET CONCLUÍDO COM SUCESSO".center(60))
    print("=" * 60)
    print("\nO sistema foi resetado para o estado inicial.")
    print("Você pode acessar o sistema com as seguintes credenciais:")
    print("  Email: admin@admin.com")
    print("  Senha: admin")

if __name__ == "__main__":
    main()
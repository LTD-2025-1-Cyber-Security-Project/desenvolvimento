from flask import Flask, render_template, request, jsonify, redirect
from url_shortener import shorten_url, get_original_url
import config
import os
import sqlite3
import datetime

app = Flask(__name__)

# Inicializar o banco de dados
def init_db():
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT NOT NULL,
        short_code TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

# Rota principal
@app.route('/')
def index():
    return render_template('index.html', api_key=config.GEMINI_API_KEY)

# API para encurtar URL
@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.json
    long_url = data.get('url')
    
    if not long_url:
        return jsonify({'error': 'URL não fornecida'}), 400
    
    try:
        # Verificar se a URL já existe no banco de dados
        conn = sqlite3.connect('urls.db')
        cursor = conn.cursor()
        cursor.execute('SELECT short_code FROM urls WHERE original_url = ?', (long_url,))
        existing = cursor.fetchone()
        
        if existing:
            short_code = existing[0]
        else:
            # Gerar novo código curto usando IA
            short_code = shorten_url(long_url, config.GEMINI_API_KEY)
            
            # Salvar no banco de dados
            cursor.execute(
                'INSERT INTO urls (original_url, short_code) VALUES (?, ?)',
                (long_url, short_code)
            )
            conn.commit()
        
        conn.close()
        
        # Construir a URL completa
        short_url = request.host_url + short_code
        
        return jsonify({
            'original_url': long_url,
            'short_url': short_url,
            'short_code': short_code
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Redirecionamento de URLs curtas
@app.route('/<short_code>')
def redirect_to_url(short_code):
    try:
        # Buscar URL original
        conn = sqlite3.connect('urls.db')
        cursor = conn.cursor()
        cursor.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()
        
        if result:
            # Incrementar contador de acessos
            cursor.execute('UPDATE urls SET access_count = access_count + 1 WHERE short_code = ?', (short_code,))
            conn.commit()
            conn.close()
            return redirect(result[0])
        else:
            conn.close()
            return render_template('index.html', error='URL não encontrada'), 404
    
    except Exception as e:
        return render_template('index.html', error=str(e)), 500

# Rota para estatísticas
@app.route('/stats')
def stats():
    try:
        conn = sqlite3.connect('urls.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT original_url, short_code, created_at, access_count 
            FROM urls ORDER BY access_count DESC
        ''')
        urls = [
            {
                'original_url': row[0],
                'short_code': row[1],
                'short_url': request.host_url + row[1],
                'created_at': row[2],
                'access_count': row[3]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        
        return render_template('stats.html', urls=urls)
    
    except Exception as e:
        return render_template('index.html', error=str(e)), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
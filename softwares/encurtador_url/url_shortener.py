import requests
import random
import string
import hashlib

def shorten_url(long_url, api_key):
    """
    Encurta uma URL longa usando a API do Google Gemini para gerar códigos inteligentes
    """
    try:
        # Preparar a chamada para a API do Gemini
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Criamos um prompt para a IA gerar um código curto e memorável
        prompt = f"""
        Crie um código curto (5-7 caracteres) para um encurtador de URL com as seguintes características:
        1. Deve ser fácil de lembrar e digitar
        2. Deve estar relacionado ao conteúdo da URL: {long_url}
        3. Forneça apenas o código curto, sem explicações adicionais
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        # Fazer a requisição para a API
        response = requests.post(
            f"{gemini_url}?key={api_key}",
            headers=headers,
            json=payload
        )
        
        # Processar a resposta
        if response.status_code == 200:
            data = response.json()
            
            # Extrair o código sugerido pela IA
            suggested_code = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            # Limpar o código (remover espaços, pontuações e manter apenas caracteres válidos)
            cleaned_code = ''.join(c for c in suggested_code if c.isalnum())[:7]
            
            # Se for muito curto ou vazio, recorremos ao método de hash
            if len(cleaned_code) < 5:
                return fallback_shortener(long_url)
                
            return cleaned_code
        else:
            # Em caso de erro na API, usamos o método de fallback
            return fallback_shortener(long_url)
            
    except Exception as e:
        print(f"Erro ao usar a API Gemini: {str(e)}")
        return fallback_shortener(long_url)

def fallback_shortener(url):
    """
    Método de fallback para gerar códigos curtos quando a API falha
    """
    # Criar um hash da URL
    hash_object = hashlib.md5(url.encode())
    hash_hex = hash_object.hexdigest()
    
    # Usar os primeiros 6 caracteres do hash
    short_code = hash_hex[:6]
    
    return short_code

def get_original_url(short_code, db_connection):
    """
    Recupera a URL original a partir do código curto
    """
    cursor = db_connection.cursor()
    cursor.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        return None
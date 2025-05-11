#!/usr/bin/env python3
"""
Módulo de serviço para integração com a API Gemini.
Responsável por buscar notícias e realizar pesquisas usando IA.
"""

import os
import json
import time
import datetime
import threading
import requests
from pathlib import Path

# Verificar se o módulo google-genai está disponível
try:
    from google import genai
    from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
    USING_NEW_SDK = True
except ImportError:
    try:
        # Tentar o SDK antigo
        import google.generativeai as genai
        USING_NEW_SDK = False
    except ImportError:
        # Falha em ambas as importações
        print("AVISO: Nenhum SDK do Google GenAI encontrado.")
        print("Por favor, instale com: pip install google-genai")
        # Usar uma implementação simulada para demonstração
        USING_NEW_SDK = None

# Diretório para cache de dados
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

class GeminiNewsService:
    """Serviço para busca de notícias usando a API Gemini"""
    
    def __init__(self, api_key=None):
        """Inicializa o serviço Gemini"""
        # Usar a chave fornecida ou tentar obter da variável de ambiente
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or "AIzaSyCY5JQRIAZlq7Re-GNDtwn8b1Hmza_hk8Y"
        
        # Configurar o cliente Gemini se disponível
        if USING_NEW_SDK is not None:
            self._setup_client()
        
        # Cache para resultados de pesquisa
        self.cache = {}
        
        # Tempo limite para atualização do cache (1 hora)
        self.cache_ttl = 3600
    
    def _setup_client(self):
        """Configura o cliente Gemini"""
        if USING_NEW_SDK is True:
            # Usar o novo SDK
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-2.0-flash"  # Modelo padrão
            
        elif USING_NEW_SDK is False:
            # Usar o SDK antigo
            genai.configure(api_key=self.api_key)
    
    def fetch_news(self, query, category=None, use_cache=True):
        """Busca notícias de uma categoria usando a API Gemini"""
        # Criar chave de cache
        cache_key = f"{query}_{category}".lower().replace(" ", "_")
        
        # Verificar se há dados em cache válidos
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Verificar se o cache ainda é válido
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        # Preparar a consulta
        prompt = self._build_news_prompt(query, category)
        
        try:
            if USING_NEW_SDK is True:
                # Usar o novo SDK
                return self._fetch_with_new_sdk(prompt, cache_key)
                
            elif USING_NEW_SDK is False:
                # Usar o SDK antigo
                return self._fetch_with_old_sdk(prompt, cache_key)
                
            else:
                # Modo de demonstração
                return self._fetch_demo_data(query, category, cache_key)
                
        except Exception as e:
            print(f"Erro ao buscar notícias: {str(e)}")
            return None
    
    def _build_news_prompt(self, query, category=None):
        """Constrói o prompt para buscar notícias"""
        if category:
            return f"""
            Busque as notícias mais recentes sobre {query} na categoria {category}.
            
            Formate a resposta como JSON com a seguinte estrutura:
            {{
                "items": [
                    {{
                        "title": "Título da notícia",
                        "source": "Fonte da notícia",
                        "date": "Data de publicação",
                        "content": "Resumo da notícia (1-2 parágrafos)",
                        "url": "URL da notícia (se disponível)"
                    }}
                ]
            }}
            
            Inclua apenas fatos verificados e informações recentes.
            """
        else:
            return f"""
            Busque as notícias mais recentes sobre {query}.
            
            Formate a resposta como JSON com a seguinte estrutura:
            {{
                "items": [
                    {{
                        "title": "Título da notícia",
                        "source": "Fonte da notícia",
                        "date": "Data de publicação",
                        "content": "Resumo da notícia (1-2 parágrafos)",
                        "url": "URL da notícia (se disponível)"
                    }}
                ]
            }}
            
            Inclua apenas fatos verificados e informações recentes.
            """
    
    def _fetch_with_new_sdk(self, prompt, cache_key):
        """Busca notícias usando o novo SDK"""
        # Configurar ferramenta de pesquisa
        google_search_tool = Tool(google_search=GoogleSearch())
        
        # Fazer a consulta
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.2,  # Temperatura baixa para respostas mais precisas
            )
        )
        
        # Extrair texto da resposta
        response_text = ""
        for part in response.candidates[0].content.parts:
            response_text += part.text
        
        # Tentar extrair o JSON da resposta
        try:
            # Limpar a resposta para extrair apenas o JSON
            json_text = self._extract_json(response_text)
            data = json.loads(json_text)
            
            # Armazenar em cache
            self.cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            return data
        except json.JSONDecodeError:
            # Se falhar ao converter para JSON, retornar o texto original
            return {"items": [{"title": "Erro na formatação", "content": response_text}]}
    
    def _fetch_with_old_sdk(self, prompt, cache_key):
        """Busca notícias usando o SDK antigo"""
        # Criar o modelo
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Fazer a consulta
        response = model.generate_content(
            contents=prompt,
            tools='google_search_retrieval'
        )
        
        # Tentar extrair o JSON da resposta
        try:
            # Limpar a resposta para extrair apenas o JSON
            json_text = self._extract_json(response.text)
            data = json.loads(json_text)
            
            # Armazenar em cache
            self.cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            return data
        except json.JSONDecodeError:
            # Se falhar ao converter para JSON, retornar o texto original
            return {"items": [{"title": "Erro na formatação", "content": response.text}]}
    
    def _fetch_demo_data(self, query, category, cache_key):
        """Gera dados de demonstração para uso sem API"""
        # Criar dados simulados para demonstração
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Dados de exemplo
        demo_data = {
            "items": [
                {
                    "title": f"Notícia recente sobre {query}",
                    "source": "TechNews",
                    "date": current_date,
                    "content": f"Este é um artigo detalhado sobre {query}, abordando os desenvolvimentos mais recentes e implicações para o futuro."
                },
                {
                    "title": f"Análise: O impacto de {query} na indústria",
                    "source": "AnalyticsTech",
                    "date": current_date,
                    "content": f"Esta análise aprofundada examina como {query} está transformando a indústria e quais serão os próximos passos."
                },
                {
                    "title": f"Especialistas discutem tendências em {query}",
                    "source": "Tech Insider",
                    "date": current_date,
                    "content": f"Um painel de especialistas discutiu as tendências atuais e futuras relacionadas a {query} durante conferência internacional."
                },
                {
                    "title": f"5 coisas que você precisa saber sobre {query}",
                    "source": "Digital Daily",
                    "date": current_date,
                    "content": f"Este guia rápido explica os cinco pontos mais importantes sobre {query} que todo profissional de tecnologia deveria conhecer."
                },
                {
                    "title": f"Como {query} está mudando o mercado de trabalho",
                    "source": "Future Work",
                    "date": current_date,
                    "content": f"Um estudo recente mostra como {query} está criando novas oportunidades e desafios no mercado de trabalho global."
                }
            ]
        }
        
        # Adicionar categoria se fornecida
        if category:
            for item in demo_data["items"]:
                item["category"] = category
        
        # Armazenar em cache
        self.cache[cache_key] = {
            "data": demo_data,
            "timestamp": time.time()
        }
        
        return demo_data
    
    def search_news(self, query):
        """Pesquisa notícias usando a API Gemini"""
        # Similar à função fetch_news, mas com um prompt diferente
        # Chave de cache para pesquisa
        cache_key = f"search_{query}".lower().replace(" ", "_")
        
        # Preparar o prompt
        prompt = f"""
        Realize uma pesquisa detalhada sobre "{query}" e encontre as informações mais relevantes e recentes.
        
        Formate a resposta como JSON com a seguinte estrutura:
        {{
            "items": [
                {{
                    "title": "Título do resultado",
                    "source": "Fonte da informação",
                    "date": "Data de publicação",
                    "content": "Resumo do conteúdo (1-2 parágrafos)",
                    "url": "URL (se disponível)"
                }}
            ]
        }}
        
        Inclua apenas fatos verificados e informações confiáveis.
        """
        
        try:
            if USING_NEW_SDK is True:
                # Usar o novo SDK
                return self._fetch_with_new_sdk(prompt, cache_key)
                
            elif USING_NEW_SDK is False:
                # Usar o SDK antigo
                return self._fetch_with_old_sdk(prompt, cache_key)
                
            else:
                # Modo de demonstração
                return self._fetch_demo_data(query, None, cache_key)
                
        except Exception as e:
            print(f"Erro ao pesquisar notícias: {str(e)}")
            return None
    
    def _extract_json(self, text):
        """Extrai texto JSON de uma resposta"""
        # Encontrar o início e fim do JSON
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            # Não encontrou formato JSON, retornar um JSON válido
            return '{"items": [{"title": "Resposta sem formato JSON", "content": "' + text.replace('"', '\\"').replace('\n', '\\n') + '"}]}'
        
        # Extrair o JSON
        json_text = text[start_idx:end_idx]
        
        # Verificar se é um JSON válido
        try:
            json.loads(json_text)
            return json_text
        except json.JSONDecodeError:
            # Se não for um JSON válido, retornar um JSON formatado com o texto
            return '{"items": [{"title": "Erro na formatação JSON", "content": "' + text.replace('"', '\\"').replace('\n', '\\n') + '"}]}'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serviço de integração com a API do YouTube.
Este módulo implementa a comunicação com a API do YouTube para busca e exibição de vídeos relacionados.
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class YouTubeService:
    """Classe de serviço para integração com API do YouTube."""
    
    def __init__(self, api_key=None):
        """Inicializa o serviço com a chave da API."""
        self.api_key = api_key
        self.youtube = None
        
    def initialize(self):
        """Inicializa o cliente da API do YouTube."""
        if not self.api_key:
            # Obtém a chave da configuração da aplicação
            self.api_key = current_app.config.get('YOUTUBE_API_KEY')
            
        if not self.api_key:
            raise ValueError("Chave da API do YouTube não configurada")
            
        # Cria o cliente da API
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def get_client(self):
        """Obtém o cliente da API, inicializando-o se necessário."""
        if not self.youtube:
            self.initialize()
        return self.youtube
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_videos(self, query, max_results=5, relevance_language='pt'):
        """
        Busca vídeos relacionados à consulta no YouTube.
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados (padrão: 5)
            relevance_language: Idioma de preferência para relevância (padrão: português)
            
        Returns:
            Lista de dicionários com informações dos vídeos
        """
        try:
            youtube = self.get_client()
            
            # Parâmetros educacionais para melhorar resultados
            educational_query = f"{query} tutorial educação"
            
            # Busca vídeos
            search_response = youtube.search().list(
                q=educational_query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                videoEmbeddable='true',
                safeSearch='strict',
                relevanceLanguage=relevance_language
            ).execute()
            
            # Prepara os dados para retorno
            videos = []
            
            for item in search_response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    video_id = item['id']['videoId']
                    
                    videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'embed_url': f"https://www.youtube.com/embed/{video_id}",
                        'watch_url': f"https://www.youtube.com/watch?v={video_id}"
                    })
            
            return videos
            
        except HttpError as e:
            logger.error(f"Erro na API do YouTube: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar vídeos: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_video_details(self, video_id):
        """
        Obtém detalhes de um vídeo específico.
        
        Args:
            video_id: ID do vídeo no YouTube
            
        Returns:
            Dicionário com informações detalhadas do vídeo
        """
        try:
            youtube = self.get_client()
            
            # Obtém detalhes do vídeo
            video_response = youtube.videos().list(
                id=video_id,
                part='snippet,contentDetails,statistics'
            ).execute()
            
            # Verifica se encontrou o vídeo
            if not video_response.get('items'):
                return None
                
            # Extrai os dados do vídeo
            item = video_response['items'][0]
            snippet = item['snippet']
            content_details = item['contentDetails']
            statistics = item['statistics']
            
            # Formata a duração
            duration = content_details.get('duration', 'PT0S')
            duration = self._format_duration(duration)
            
            # Monta o objeto de resposta
            video = {
                'id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'channel': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'duration': duration,
                'view_count': statistics.get('viewCount', '0'),
                'like_count': statistics.get('likeCount', '0'),
                'embed_url': f"https://www.youtube.com/embed/{video_id}",
                'watch_url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
            return video
            
        except HttpError as e:
            logger.error(f"Erro na API do YouTube: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do vídeo: {str(e)}")
            raise
    
    def _format_duration(self, duration_str):
        """
        Formata a duração do vídeo em formato legível.
        
        Args:
            duration_str: String de duração no formato ISO 8601 (ex: PT1H30M15S)
            
        Returns:
            String formatada (ex: 1:30:15)
        """
        import re
        import datetime
        
        # Expressão regular para extrair horas, minutos e segundos
        hours = re.search(r'(\d+)H', duration_str)
        minutes = re.search(r'(\d+)M', duration_str)
        seconds = re.search(r'(\d+)S', duration_str)
        
        hours = int(hours.group(1)) if hours else 0
        minutes = int(minutes.group(1)) if minutes else 0
        seconds = int(seconds.group(1)) if seconds else 0
        
        # Formata a duração
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_related_videos(self, video_id, max_results=5):
        """
        Obtém vídeos relacionados a um vídeo específico.
        
        Args:
            video_id: ID do vídeo no YouTube
            max_results: Número máximo de resultados (padrão: 5)
            
        Returns:
            Lista de dicionários com informações dos vídeos relacionados
        """
        try:
            youtube = self.get_client()
            
            # Busca vídeos relacionados
            search_response = youtube.search().list(
                relatedToVideoId=video_id,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                safeSearch='strict'
            ).execute()
            
            # Prepara os dados para retorno
            videos = []
            
            for item in search_response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    related_video_id = item['id']['videoId']
                    
                    videos.append({
                        'id': related_video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'embed_url': f"https://www.youtube.com/embed/{related_video_id}",
                        'watch_url': f"https://www.youtube.com/watch?v={related_video_id}"
                    })
            
            return videos
            
        except HttpError as e:
            logger.error(f"Erro na API do YouTube: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar vídeos relacionados: {str(e)}")
            raise
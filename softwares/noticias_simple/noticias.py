#!/usr/bin/env python3
"""
Aplicativo de terminal para consultas ao Gemini com Search Grounding

Este aplicativo permite ao usuário fazer perguntas no terminal e receber
respostas fundamentadas com dados da web através do Gemini e Google Search.
"""

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import os
import sys
import textwrap

# Configurar a API key
API_KEY = "AIzaSyCY5JQRIAZlq7Re-GNDtwn8b1Hmza_hk8Y"

# Definições de cores para o terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Imprime o cabeçalho do aplicativo"""
    header = """
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║    GEMINI SEARCH - CONSULTA COM FUNDAMENTAÇÃO NA WEB       ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.CYAN}{header}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Digite sua pergunta ou 'sair' para encerrar.{Colors.ENDC}\n")

def format_response(text):
    """Formata a resposta para melhor legibilidade no terminal"""
    width = os.get_terminal_size().columns - 10
    paragraphs = text.split('\n')
    formatted_text = ""
    
    for paragraph in paragraphs:
        if paragraph.strip() == "":
            formatted_text += "\n"
            continue
        
        wrapped = textwrap.fill(paragraph, width=width)
        formatted_text += wrapped + "\n"
    
    return formatted_text

def print_sources(grounding_metadata):
    """Imprime as fontes da resposta"""
    if not grounding_metadata or not hasattr(grounding_metadata, "grounding_chunks"):
        return
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Fontes:{Colors.ENDC}")
    
    # Imprime os chunks de fundamentação (fontes)
    seen_urls = set()
    for i, chunk in enumerate(grounding_metadata.grounding_chunks):
        if hasattr(chunk, "web") and hasattr(chunk.web, "uri") and hasattr(chunk.web, "title"):
            url = chunk.web.uri
            title = chunk.web.title
            
            # Evitar duplicatas
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            print(f"{Colors.YELLOW}[{i+1}]{Colors.ENDC} {title} - {url}")

def get_gemini_response(query):
    """Obtém resposta do Gemini com Search Grounding ativado"""
    try:
        # Inicializar o cliente
        client = genai.Client(api_key=API_KEY)
        
        # Definir o modelo e configurar a ferramenta de pesquisa Google
        model_id = "gemini-2.0-flash"  # Modelo estável para produção
        
        # Configurar a ferramenta de pesquisa Google
        google_search_tool = Tool(google_search=GoogleSearch())
        
        # Fazer a consulta
        response = client.models.generate_content(
            model=model_id,
            contents=query,
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
                temperature=0.2,  # Temperatura baixa para respostas mais precisas
            )
        )
        
        # Extrair o texto da resposta
        response_text = ""
        for part in response.candidates[0].content.parts:
            response_text += part.text
        
        # Obter metadados de fundamentação, se disponíveis
        grounding_metadata = None
        if hasattr(response.candidates[0], "grounding_metadata"):
            grounding_metadata = response.candidates[0].grounding_metadata
        
        return response_text, grounding_metadata
    
    except Exception as e:
        return f"Erro ao consultar o Gemini: {str(e)}", None

def main():
    """Função principal do aplicativo"""
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpa o terminal
    print_header()
    
    while True:
        try:
            # Obter a pergunta do usuário
            query = input(f"{Colors.BOLD}> {Colors.ENDC}")
            
            # Verificar se o usuário quer sair
            if query.lower() in ['sair', 'exit', 'quit', 'q']:
                print(f"\n{Colors.YELLOW}Encerrando o aplicativo. Até logo!{Colors.ENDC}")
                sys.exit(0)
            
            # Verificar se a pergunta está vazia
            if not query.strip():
                continue
            
            print(f"\n{Colors.BLUE}Pesquisando...{Colors.ENDC}")
            
            # Obter resposta do Gemini
            response_text, grounding_metadata = get_gemini_response(query)
            
            # Imprimir a resposta formatada
            print(f"\n{Colors.GREEN}Resposta:{Colors.ENDC}")
            print(format_response(response_text))
            
            # Imprimir as fontes, se disponíveis
            if grounding_metadata:
                print_sources(grounding_metadata)
            
            print("\n" + "-" * 70 + "\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Operação cancelada pelo usuário. Digite 'sair' para encerrar.{Colors.ENDC}\n")
        
        except Exception as e:
            print(f"\n{Colors.RED}Erro: {str(e)}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
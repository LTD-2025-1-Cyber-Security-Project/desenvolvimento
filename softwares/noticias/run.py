#!/usr/bin/env python3
"""
Script de inicialização para o aplicativo NexusInfo.
Este arquivo serve como ponto de entrada para a aplicação.
"""

import os
import sys
import argparse
from pathlib import Path

# Diretório base
BASE_DIR = Path(__file__).resolve().parent

# Garantir que o diretório do aplicativo esteja no PYTHONPATH
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Iniciar o aplicativo
if __name__ == "__main__":
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description="NexusInfo - Sistema de Notícias com IA")
    
    parser.add_argument(
        "--theme", 
        type=str, 
        default=None, 
        help="Tema da interface (dark, light, etc.)"
    )
    
    parser.add_argument(
        "--api-key", 
        type=str, 
        default=None, 
        help="Chave da API Gemini"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Ativar modo de depuração"
    )
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Configurar variáveis de ambiente
    if args.api_key:
        os.environ["GOOGLE_API_KEY"] = args.api_key
    
    # Definir o tema como variável de ambiente (se fornecido)
    if args.theme:
        os.environ["NEXUSINFO_THEME"] = args.theme
    
    # Ativar modo debug se solicitado
    if args.debug:
        os.environ["NEXUSINFO_DEBUG"] = "1"
    
    # Importar e iniciar a aplicação (após configurar as variáveis de ambiente)
    from main import main
    main()
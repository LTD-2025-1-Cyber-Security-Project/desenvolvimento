import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações da aplicação"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-para-desenvolvimento')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Limites de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Google Gemini
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    
    # Pastas
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
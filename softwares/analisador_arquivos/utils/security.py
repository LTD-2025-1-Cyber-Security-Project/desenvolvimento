import os
import re
import hashlib
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional, Tuple
import mimetypes
import time
import uuid
import shutil

class SecurityManager:
    """Gerenciador de segurança para uploads e processamento de arquivos"""
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verifica se o arquivo é permitido baseado na extensão"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def secure_save_file(file, folder: str = None) -> Tuple[str, str]:
        """
        Salva arquivo de forma segura
        Returns: (safe_filename, full_path)
        """
        if folder is None:
            folder = current_app.config['UPLOAD_FOLDER']
        
        if not os.path.exists(folder):
            os.makedirs(folder, mode=0o755)
        
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"file_{hashlib.md5(os.urandom(32)).hexdigest()[:8]}"
        
        # Adiciona hash único para evitar conflitos
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{hashlib.md5(os.urandom(32)).hexdigest()[:8]}{ext}"
        
        filepath = os.path.join(folder, unique_filename)
        file.save(filepath)
        
        return unique_filename, filepath
    
    @staticmethod
    def validate_file_type(filepath: str, expected_mime_types: list = None) -> bool:
        """Valida o tipo do arquivo usando mimetypes e extensão"""
        if expected_mime_types is None:
            return True
            
        try:
            # Primeiro tenta usando mimetypes
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type and mime_type in expected_mime_types:
                return True
            
            # Fallback para verificação por extensão
            ext = os.path.splitext(filepath)[1].lower()
            ext_mime_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }
            
            if ext in ext_mime_map and ext_mime_map[ext] in expected_mime_types:
                return True
            
            # Se não encontrou correspondência, mas não há restrições específicas, permite
            return len(expected_mime_types) == 0
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caracteres perigosos do nome do arquivo"""
        # Remove caracteres não-ASCII
        filename = filename.encode('ascii', 'ignore').decode('ascii')
        # Remove caracteres especiais
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Remove múltiplos underscores
        filename = re.sub(r'_+', '_', filename)
        # Limita o tamanho do nome do arquivo
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename
    
    @staticmethod
    def check_file_size(file) -> bool:
        """Verifica se o arquivo está dentro do limite de tamanho"""
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        return size <= current_app.config['MAX_CONTENT_LENGTH']
    
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """Gera hash SHA-256 do arquivo"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def cleanup_old_files(folder: str, max_age_hours: int = 24):
        """Remove arquivos antigos do diretório"""
        import time
        current_time = time.time()
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Gera um nome de arquivo único mantendo a extensão original"""
        name, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = str(int(time.time()))[-6:]
        return f"{secure_filename(name)}_{timestamp}_{unique_id}{ext}"
    
    @staticmethod
    def validate_image_dimensions(filepath: str, max_width: int = 10000, max_height: int = 10000) -> bool:
        """Valida as dimensões de uma imagem"""
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                width, height = img.size
                return width <= max_width and height <= max_height
        except Exception:
            return False
    
    @staticmethod
    def scan_file_content(filepath: str) -> bool:
        """Verifica o conteúdo do arquivo em busca de padrões suspeitos"""
        try:
            suspicious_patterns = [
                b'<?php',  # PHP code
                b'<script',  # JavaScript
                b'eval(',  # Eval function
                b'system(',  # System calls
                b'exec(',  # Exec function
                b'shell_exec(',  # Shell execution
                b'base64_decode(',  # Base64 decode function
            ]
            
            with open(filepath, 'rb') as f:
                content = f.read(1024)  # Lê apenas os primeiros 1KB
                for pattern in suspicious_patterns:
                    if pattern in content:
                        return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_safe_directory(directory_path: str) -> bool:
        """Cria um diretório de forma segura"""
        try:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path, mode=0o755)
            return True
        except Exception:
            return False
    
    @staticmethod
    def backup_file(filepath: str, backup_dir: str = None) -> Optional[str]:
        """Cria um backup de um arquivo"""
        try:
            if backup_dir is None:
                backup_dir = os.path.join(current_app.config.get('BACKUP_FOLDER', 'backups'))
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, mode=0o755)
            
            filename = os.path.basename(filepath)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(filepath, backup_path)
            return backup_path
        except Exception:
            return None
    
    @staticmethod
    def validate_upload_request(request) -> Tuple[bool, str]:
        """Valida uma requisição de upload"""
        # Verifica se há arquivos
        if 'files' not in request.files and 'files[]' not in request.files:
            return False, "Nenhum arquivo enviado"
        
        # Verifica o método HTTP
        if request.method != 'POST':
            return False, "Método HTTP inválido"
        
        # Verifica o tamanho total da requisição
        content_length = request.content_length
        if content_length and content_length > current_app.config['MAX_CONTENT_LENGTH']:
            return False, "Tamanho total da requisição excede o limite permitido"
        
        # Verifica o Content-Type
        if not request.content_type.startswith('multipart/form-data'):
            return False, "Content-Type inválido"
        
        return True, "OK"
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Obtém a extensão do arquivo de forma segura"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    @staticmethod
    def is_safe_path(basedir: str, path: str) -> bool:
        """Verifica se um caminho é seguro (previne directory traversal)"""
        # Resolve o caminho absoluto
        matchpath = os.path.abspath(path)
        basedir = os.path.abspath(basedir)
        
        # Verifica se o caminho está dentro do diretório base
        return basedir == os.path.commonpath([basedir, matchpath])
    
    @staticmethod
    def encrypt_file(filepath: str, password: str) -> bool:
        """Criptografa um arquivo (implementação básica)"""
        try:
            # Esta é uma implementação básica para demonstração
            # Em produção, use uma biblioteca de criptografia robusta
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
            
            # Deriva uma chave da senha
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            f = Fernet(key)
            
            # Lê o arquivo
            with open(filepath, 'rb') as file:
                file_data = file.read()
            
            # Criptografa os dados
            encrypted_data = f.encrypt(file_data)
            
            # Salva os dados criptografados
            with open(filepath + '.encrypted', 'wb') as file:
                file.write(salt + encrypted_data)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_file_token(filepath: str) -> str:
        """Gera um token único para um arquivo"""
        file_info = f"{filepath}{time.time()}{os.urandom(16)}"
        return hashlib.sha256(file_info.encode()).hexdigest()
    
    @staticmethod
    def validate_file_integrity(filepath: str, expected_hash: str) -> bool:
        """Valida a integridade de um arquivo comparando seu hash"""
        current_hash = SecurityManager.get_file_hash(filepath)
        return current_hash == expected_hash
    
    @staticmethod
    def quarantine_file(filepath: str, reason: str = "suspicious") -> bool:
        """Move um arquivo para quarentena"""
        try:
            quarantine_dir = os.path.join(current_app.config.get('QUARANTINE_FOLDER', 'quarantine'))
            if not os.path.exists(quarantine_dir):
                os.makedirs(quarantine_dir, mode=0o755)
            
            filename = os.path.basename(filepath)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            quarantine_filename = f"{timestamp}_{reason}_{filename}"
            quarantine_path = os.path.join(quarantine_dir, quarantine_filename)
            
            shutil.move(filepath, quarantine_path)
            
            # Log da quarentena
            log_entry = f"{timestamp},{filepath},{reason},{quarantine_path}\n"
            log_file = os.path.join(quarantine_dir, "quarantine.log")
            with open(log_file, 'a') as f:
                f.write(log_entry)
            
            return True
        except Exception:
            return False
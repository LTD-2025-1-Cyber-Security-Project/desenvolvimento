import os
import sys

def create_directory(path):
    """Cria um diretório se ele não existir"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Criado diretório: {path}")
    else:
        print(f"Diretório já existe: {path}")

def create_file(file_path):
    """Cria um arquivo vazio se ele não existir"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Verifica se o arquivo já existe para evitar sobrescrever
    if not os.path.exists(file_path):
        # Cria o arquivo vazio
        open(file_path, 'a').close()
        print(f"Criado arquivo: {file_path}")
    else:
        print(f"Arquivo já existe: {file_path}")

def create_edtech_project():
    """Cria a estrutura completa do projeto"""
    # Diretório raiz
    root_dir = "edtech_ia_cyber"
    create_directory(root_dir)
    
    # Arquivos principais na raiz
    create_file(os.path.join(root_dir, "app.py"))
    create_file(os.path.join(root_dir, "requirements.txt"))
    create_file(os.path.join(root_dir, ".env"))
    create_file(os.path.join(root_dir, ".env.example"))
    create_file(os.path.join(root_dir, ".gitignore"))
    create_file(os.path.join(root_dir, "README.md"))
    
    # Diretórios principais
    create_directory(os.path.join(root_dir, "migrations"))
    create_directory(os.path.join(root_dir, "tests"))
    
    # Diretório app e seus arquivos
    app_dir = os.path.join(root_dir, "app")
    create_directory(app_dir)
    create_file(os.path.join(app_dir, "__init__.py"))
    create_file(os.path.join(app_dir, "config.py"))
    
    # Diretório models
    models_dir = os.path.join(app_dir, "models")
    create_directory(models_dir)
    create_file(os.path.join(models_dir, "__init__.py"))
    create_file(os.path.join(models_dir, "user.py"))
    create_file(os.path.join(models_dir, "course.py"))
    create_file(os.path.join(models_dir, "quiz.py"))
    create_file(os.path.join(models_dir, "progress.py"))
    
    # Diretório controllers
    controllers_dir = os.path.join(app_dir, "controllers")
    create_directory(controllers_dir)
    create_file(os.path.join(controllers_dir, "__init__.py"))
    create_file(os.path.join(controllers_dir, "auth.py"))
    create_file(os.path.join(controllers_dir, "courses.py"))
    create_file(os.path.join(controllers_dir, "quizzes.py"))
    create_file(os.path.join(controllers_dir, "admin.py"))
    create_file(os.path.join(controllers_dir, "api.py"))
    
    # Diretório services
    services_dir = os.path.join(app_dir, "services")
    create_directory(services_dir)
    create_file(os.path.join(services_dir, "__init__.py"))
    create_file(os.path.join(services_dir, "ai_service.py"))
    create_file(os.path.join(services_dir, "youtube_service.py"))
    create_file(os.path.join(services_dir, "email_service.py"))
    
    # Diretório views e subdiretorios
    views_dir = os.path.join(app_dir, "views")
    create_directory(views_dir)
    
    # Templates
    templates_dir = os.path.join(views_dir, "templates")
    create_directory(templates_dir)
    create_file(os.path.join(templates_dir, "base.html"))
    
    # Subdiretorios de templates
    create_directory(os.path.join(templates_dir, "auth"))
    create_directory(os.path.join(templates_dir, "courses"))
    create_directory(os.path.join(templates_dir, "quizzes"))
    create_directory(os.path.join(templates_dir, "profile"))
    create_directory(os.path.join(templates_dir, "admin"))
    
    # Static files
    static_dir = os.path.join(views_dir, "static")
    create_directory(static_dir)
    create_directory(os.path.join(static_dir, "css"))
    create_directory(os.path.join(static_dir, "js"))
    create_directory(os.path.join(static_dir, "img"))
    create_directory(os.path.join(static_dir, "scss"))
    
    # Diretório utils
    utils_dir = os.path.join(app_dir, "utils")
    create_directory(utils_dir)
    create_file(os.path.join(utils_dir, "__init__.py"))
    create_file(os.path.join(utils_dir, "security.py"))
    create_file(os.path.join(utils_dir, "validators.py"))
    create_file(os.path.join(utils_dir, "helpers.py"))
    
    print("Estrutura do projeto criada com sucesso!")

if __name__ == "__main__":
    create_edtech_project()
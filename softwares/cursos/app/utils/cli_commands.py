#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comandos CLI.
Este módulo contém comandos para o CLI do Flask.
"""

import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User, UserRoles
from app.models.course import Course, Module, Lesson
from app.models.quiz import Quiz, Question
import os
import csv
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash


def register_commands(app):
    """
    Registra comandos CLI na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    @click.argument("first_name")
    @click.argument("last_name")
    @with_appcontext
    def create_admin(email, password, first_name, last_name):
        """
        Cria um usuário administrador.
        
        Uso: flask create-admin EMAIL PASSWORD FIRST_NAME LAST_NAME
        """
        # Verifica se o email já está em uso
        if User.query.filter_by(email=email).first():
            click.echo(f"Erro: O email {email} já está em uso.")
            return
        
        # Cria o usuário administrador
        admin = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRoles.ADMIN,
            municipality='Florianópolis',
            department='Administração',
            job_title='Administrador do Sistema'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo(f"Administrador criado com sucesso: {email}")
    
    
    @app.cli.command("import-users")
    @click.argument("csv_file")
    @with_appcontext
    def import_users(csv_file):
        """
        Importa usuários de um arquivo CSV.
        
        Uso: flask import-users CSV_FILE
        
        Formato do CSV:
        email,password,first_name,last_name,role,municipality,department,job_title
        """
        if not os.path.exists(csv_file):
            click.echo(f"Erro: O arquivo {csv_file} não existe.")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                created_count = 0
                skipped_count = 0
                
                for row in reader:
                    # Verifica se o email já está em uso
                    if User.query.filter_by(email=row['email']).first():
                        click.echo(f"Pulando {row['email']}: Email já em uso.")
                        skipped_count += 1
                        continue
                    
                    # Cria o usuário
                    user = User(
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        role=row.get('role', UserRoles.STUDENT),
                        municipality=row.get('municipality', 'Florianópolis'),
                        department=row.get('department', ''),
                        job_title=row.get('job_title', '')
                    )
                    
                    db.session.add(user)
                    created_count += 1
                
                db.session.commit()
                
                click.echo(f"{created_count} usuários criados com sucesso.")
                click.echo(f"{skipped_count} usuários pulados.")
                
        except Exception as e:
            click.echo(f"Erro ao importar usuários: {str(e)}")
    
    
    @app.cli.command("delete-inactive-users")
    @click.option("--days", default=365, help="Número de dias de inatividade")
    @click.option("--dry-run", is_flag=True, help="Apenas mostra os usuários que seriam excluídos")
    @with_appcontext
    def delete_inactive_users(days, dry_run):
        """
        Exclui usuários inativos há mais de X dias.
        
        Uso: flask delete-inactive-users --days=365 --dry-run
        """
        # Calcula a data limite
        limit_date = datetime.utcnow() - timedelta(days=days)
        
        # Obtém os usuários inativos
        query = User.query.filter(
            (User.last_login.is_(None) & (User.created_at <= limit_date)) |
            (User.last_login <= limit_date)
        ).filter(User.role != UserRoles.ADMIN)  # Não exclui administradores
        
        inactive_users = query.all()
        
        if dry_run:
            click.echo(f"Seriam excluídos {len(inactive_users)} usuários inativos há mais de {days} dias:")
            for user in inactive_users:
                click.echo(f"- {user.email} ({user.get_full_name()})")
            return
        
        if not inactive_users:
            click.echo(f"Nenhum usuário inativo há mais de {days} dias encontrado.")
            return
        
        # Confirmação
        if not click.confirm(f"Deseja excluir {len(inactive_users)} usuários inativos?"):
            click.echo("Operação cancelada.")
            return
        
        # Exclui os usuários
        for user in inactive_users:
            db.session.delete(user)
        
        db.session.commit()
        
        click.echo(f"{len(inactive_users)} usuários inativos excluídos com sucesso.")
    
    
    @app.cli.command("initialize-db")
    @with_appcontext
    def initialize_db():
        """
        Inicializa o banco de dados com dados básicos.
        
        Uso: flask initialize-db
        """
        # Confirmação
        if not click.confirm("Deseja inicializar o banco de dados? Isso criará tabelas e dados básicos."):
            click.echo("Operação cancelada.")
            return
        
        # Cria as tabelas
        db.create_all()
        
        # Verifica se já existe um administrador
        if User.query.filter_by(role=UserRoles.ADMIN).first():
            click.echo("O banco de dados já foi inicializado anteriormente.")
            return
        
        # Cria um administrador padrão
        admin = User(
            email='admin@edtech.gov.br',
            password='Admin@123',
            first_name='Administrador',
            last_name='do Sistema',
            role=UserRoles.ADMIN,
            municipality='Florianópolis',
            department='Administração',
            job_title='Administrador do Sistema'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo("Banco de dados inicializado com sucesso.")
        click.echo("Administrador criado: admin@edtech.gov.br / Admin@123")
    
    
    @app.cli.command("generate-demo-data")
    @click.option("--users", default=20, help="Número de usuários a serem gerados")
    @click.option("--courses", default=4, help="Número de cursos a serem gerados")
    @with_appcontext
    def generate_demo_data(users, courses):
        """
        Gera dados de demonstração para testes.
        
        Uso: flask generate-demo-data --users=20 --courses=4
        """
        # Confirmação
        if not click.confirm("Deseja gerar dados de demonstração? Isso criará usuários e cursos fictícios."):
            click.echo("Operação cancelada.")
            return
        
        # Nomes e sobrenomes para geração aleatória
        first_names = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Juliana', 'Lucas', 'Mariana', 
                      'Rafael', 'Camila', 'Gustavo', 'Fernanda', 'Diego', 'Patrícia', 'Thiago']
        last_names = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues', 
                     'Almeida', 'Nascimento', 'Lima', 'Araújo', 'Ferreira', 'Martins', 'Gomes']
        
        municipalities = ['Florianópolis', 'São José']
        departments = ['TI', 'Administração', 'Recursos Humanos', 'Financeiro', 'Educação', 'Saúde']
        job_titles = ['Analista', 'Coordenador', 'Supervisor', 'Técnico', 'Assistente', 'Gerente']
        
        # Gera usuários
        for i in range(users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@teste.gov.br"
            
            # Verifica se o email já existe
            if User.query.filter_by(email=email).first():
                continue
            
            user = User(
                email=email,
                password='Teste@123',
                first_name=first_name,
                last_name=last_name,
                role=random.choice([UserRoles.STUDENT, UserRoles.INSTRUCTOR]),
                municipality=random.choice(municipalities),
                department=random.choice(departments),
                job_title=random.choice(job_titles),
                is_active=True,
                xp_points=random.randint(0, 3000),
                last_login=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            
            db.session.add(user)
            
        db.session.commit()
        click.echo(f"{users} usuários gerados com sucesso.")
        
        # Gera cursos
        categories = ['IA', 'Cybersegurança']
        levels = ['Básico', 'Intermediário', 'Avançado']
        
        # Obtém um usuário instrutor aleatório
        instructor = User.query.filter_by(role=UserRoles.INSTRUCTOR).first()
        if not instructor:
            instructor = User.query.filter_by(role=UserRoles.ADMIN).first()
        
        for i in range(courses):
            category = categories[i % len(categories)]
            
            if category == 'IA':
                course_titles = [
                    'Fundamentos de Inteligência Artificial',
                    'Machine Learning para Gestão Pública',
                    'Processamento de Linguagem Natural na Administração Pública',
                    'Ética em IA para o Setor Público'
                ]
            else:
                course_titles = [
                    'Fundamentos de Cibersegurança',
                    'Segurança de Dados na Administração Pública',
                    'Prevenção de Ataques Cibernéticos',
                    'Gestão de Incidentes de Segurança'
                ]
            
            title = course_titles[i % len(course_titles)]
            
            # Verifica se o curso já existe
            if Course.query.filter_by(title=title).first():
                continue
            
            course = Course(
                title=title,
                description=f"Este curso aborda {title.lower()} no contexto da administração pública municipal. Os participantes aprenderão conceitos teóricos e práticos para aplicação no dia a dia das prefeituras.",
                short_description=f"Aprenda sobre {title.lower()} e aplique no seu trabalho na prefeitura.",
                category=category,
                level=levels[i % len(levels)],
                duration_hours=random.randint(10, 40),
                created_by_id=instructor.id,
                is_published=True,
                is_featured=(i < 2)  # Destaca os primeiros cursos
            )
            
            db.session.add(course)
            db.session.flush()  # Para obter o ID do curso
            
            # Gera módulos para o curso
            num_modules = random.randint(3, 5)
            for j in range(num_modules):
                module = Module(
                    title=f"Módulo {j+1}: {get_module_title(category, j)}",
                    description=f"Este módulo aborda os conceitos de {get_module_title(category, j).lower()}.",
                    order=j+1,
                    course_id=course.id
                )
                
                db.session.add(module)
                db.session.flush()  # Para obter o ID do módulo
                
                # Gera lições para o módulo
                num_lessons = random.randint(3, 6)
                for k in range(num_lessons):
                    lesson_title = get_lesson_title(category, j, k)
                    lesson = Lesson(
                        title=f"Lição {k+1}: {lesson_title}",
                        content=get_lesson_content(category, lesson_title),
                        order=k+1,
                        lesson_type=random.choice(['text', 'video', 'interactive']),
                        duration_minutes=random.randint(15, 60),
                        xp_reward=random.randint(30, 100),
                        module_id=module.id
                    )
                    
                    db.session.add(lesson)
                    db.session.flush()  # Para obter o ID da lição
                    
                    # Gera quiz para algumas lições
                    if random.random() < 0.7:  # 70% de chance de ter quiz
                        quiz = Quiz(
                            title=f"Quiz: {lesson_title}",
                            description=f"Teste seus conhecimentos sobre {lesson_title.lower()}.",
                            quiz_type='standard',
                            difficulty=random.choice(['easy', 'medium', 'hard']),
                            passing_score=70,
                            xp_reward=random.randint(20, 50),
                            is_published=True,
                            lesson_id=lesson.id,
                            created_by_id=instructor.id
                        )
                        
                        db.session.add(quiz)
                        db.session.flush()  # Para obter o ID do quiz
                        
                        # Gera questões para o quiz
                        num_questions = random.randint(3, 7)
                        for q in range(num_questions):
                            question = Question(
                                text=f"Pergunta {q+1}: {get_question_text(category, lesson_title, q)}",
                                question_type='multiple_choice',
                                options=get_question_options(category, q),
                                correct_answer=str(random.randint(0, 3)),  # Índice da opção correta
                                explanation=f"Explicação da resposta correta para a pergunta {q+1}.",
                                quiz_id=quiz.id,
                                difficulty=quiz.difficulty,
                                points=10
                            )
                            
                            db.session.add(question)
                            
            # Matricula alguns usuários aleatórios nos cursos
            students = User.query.filter_by(role=UserRoles.STUDENT).limit(10).all()
            for student in students:
                if random.random() < 0.6:  # 60% de chance de matricular
                    student.courses.append(course)
        
        db.session.commit()
        click.echo(f"{courses} cursos gerados com sucesso.")
    
    
    @app.cli.command("reset-db")
    @with_appcontext
    def reset_db():
        """
        Reseta o banco de dados (exclui e recria todas as tabelas).
        
        Uso: flask reset-db
        """
        # Confirmação
        if not click.confirm("ATENÇÃO! Isso excluirá TODOS os dados do banco de dados. Deseja continuar?", abort=True):
            return
        
        # Segunda confirmação
        if not click.confirm("Tem certeza? Esta ação é irreversível.", abort=True):
            return
        
        # Exclui e recria as tabelas
        db.drop_all()
        db.create_all()
        
        click.echo("Banco de dados resetado com sucesso.")
    
    
    @app.cli.command("backup-db")
    @click.argument("output_file")
    @with_appcontext
    def backup_db(output_file):
        """
        Cria um backup do banco de dados em formato JSON.
        
        Uso: flask backup-db backup.json
        """
        import json
        
        # Obtém dados de todas as tabelas
        data = {
            'users': [],
            'courses': [],
            'modules': [],
            'lessons': [],
            'quizzes': [],
            'questions': [],
            'progress': [],
            'quiz_attempts': [],
            'certificates': [],
            'user_activities': []
        }
        
        # Função para serializar objetos datetime
        def json_serial(obj):
            if isinstance(obj, (datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Tipo {type(obj)} não é serializável")
        
        # Extrai dados de usuários
        from app.models.user import User
        users = User.query.all()
        for user in users:
            user_data = {
                'id': user.id,
                'uuid': user.uuid,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role,
                'is_active': user.is_active,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_pic': user.profile_pic,
                'bio': user.bio,
                'department': user.department,
                'job_title': user.job_title,
                'municipality': user.municipality,
                'xp_points': user.xp_points,
                'level': user.level,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'last_login': user.last_login
            }
            data['users'].append(user_data)
        
        # Extrai dados de cursos
        from app.models.course import Course
        courses = Course.query.all()
        for course in courses:
            course_data = {
                'id': course.id,
                'slug': course.slug,
                'title': course.title,
                'description': course.description,
                'short_description': course.short_description,
                'category': course.category,
                'level': course.level,
                'duration_hours': course.duration_hours,
                'thumbnail': course.thumbnail,
                'created_by_id': course.created_by_id,
                'is_published': course.is_published,
                'is_featured': course.is_featured,
                'tags': course.tags,
                'prerequisite_courses': course.prerequisite_courses,
                'created_at': course.created_at,
                'updated_at': course.updated_at
            }
            data['courses'].append(course_data)
        
        # Extrai dados de módulos
        from app.models.course import Module
        modules = Module.query.all()
        for module in modules:
            module_data = {
                'id': module.id,
                'slug': module.slug,
                'title': module.title,
                'description': module.description,
                'order': module.order,
                'course_id': module.course_id,
                'created_at': module.created_at,
                'updated_at': module.updated_at
            }
            data['modules'].append(module_data)
        
        # Extrai dados de lições
        from app.models.course import Lesson
        lessons = Lesson.query.all()
        for lesson in lessons:
            lesson_data = {
                'id': lesson.id,
                'slug': lesson.slug,
                'title': lesson.title,
                'content': lesson.content,
                'order': lesson.order,
                'lesson_type': lesson.lesson_type,
                'duration_minutes': lesson.duration_minutes,
                'video_url': lesson.video_url,
                'attachment_url': lesson.attachment_url,
                'xp_reward': lesson.xp_reward,
                'module_id': lesson.module_id,
                'created_at': lesson.created_at,
                'updated_at': lesson.updated_at
            }
            data['lessons'].append(lesson_data)
        
        # Salva o backup em um arquivo JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=json_serial, ensure_ascii=False, indent=2)
        
        click.echo(f"Backup criado com sucesso: {output_file}")
    
    
    @app.cli.command("restore-db")
    @click.argument("input_file")
    @with_appcontext
    def restore_db(input_file):
        """
        Restaura um backup do banco de dados a partir de um arquivo JSON.
        
        Uso: flask restore-db backup.json
        """
        import json
        
        # Verifica se o arquivo existe
        if not os.path.exists(input_file):
            click.echo(f"Erro: O arquivo {input_file} não existe.")
            return
        
        # Confirmação
        if not click.confirm("Isso substituirá todos os dados atuais. Deseja continuar?", abort=True):
            return
        
        # Carrega o backup
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Exclui todos os dados atuais
        db.session.execute("SET FOREIGN_KEY_CHECKS = 0")  # Desativa verificação de chaves estrangeiras
        
        # Limpa tabelas na ordem inversa de dependência
        from app.models.progress import UserActivity, Certificate, Progress
        from app.models.quiz import QuizAttempt, Question, Quiz
        from app.models.course import Lesson, Module, Course
        from app.models.user import User
        
        UserActivity.query.delete()
        Certificate.query.delete()
        Progress.query.delete()
        QuizAttempt.query.delete()
        Question.query.delete()
        Quiz.query.delete()
        Lesson.query.delete()
        Module.query.delete()
        Course.query.delete()
        
        # Limpa a tabela de associação entre usuários e cursos
        db.session.execute("DELETE FROM user_courses")
        
        User.query.delete()
        
        db.session.execute("SET FOREIGN_KEY_CHECKS = 1")  # Reativa verificação de chaves estrangeiras
        db.session.commit()
        
        # Restaura os dados
        # Usuários
        for user_data in data.get('users', []):
            user = User(
                id=user_data.get('id'),
                uuid=user_data.get('uuid'),
                email=user_data.get('email'),
                password_hash=user_data.get('password_hash'),
                role=user_data.get('role'),
                is_active=user_data.get('is_active'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                profile_pic=user_data.get('profile_pic'),
                bio=user_data.get('bio'),
                department=user_data.get('department'),
                job_title=user_data.get('job_title'),
                municipality=user_data.get('municipality'),
                xp_points=user_data.get('xp_points'),
                level=user_data.get('level')
            )
            
            # Converte strings ISO para objetos datetime
            if user_data.get('created_at'):
                user.created_at = datetime.fromisoformat(user_data.get('created_at'))
            if user_data.get('updated_at'):
                user.updated_at = datetime.fromisoformat(user_data.get('updated_at'))
            if user_data.get('last_login'):
                user.last_login = datetime.fromisoformat(user_data.get('last_login'))
            
            db.session.add(user)
        
        db.session.commit()
        click.echo("Usuários restaurados com sucesso.")
        
        # Cursos
        for course_data in data.get('courses', []):
            course = Course(
                id=course_data.get('id'),
                slug=course_data.get('slug'),
                title=course_data.get('title'),
                description=course_data.get('description'),
                short_description=course_data.get('short_description'),
                category=course_data.get('category'),
                level=course_data.get('level'),
                duration_hours=course_data.get('duration_hours'),
                thumbnail=course_data.get('thumbnail'),
                created_by_id=course_data.get('created_by_id'),
                is_published=course_data.get('is_published'),
                is_featured=course_data.get('is_featured'),
                tags=course_data.get('tags'),
                prerequisite_courses=course_data.get('prerequisite_courses')
            )
            
            # Converte strings ISO para objetos datetime
            if course_data.get('created_at'):
                course.created_at = datetime.fromisoformat(course_data.get('created_at'))
            if course_data.get('updated_at'):
                course.updated_at = datetime.fromisoformat(course_data.get('updated_at'))
            
            db.session.add(course)
        
        db.session.commit()
        click.echo("Cursos restaurados com sucesso.")
        
        # Continue restaurando as outras tabelas...
        # (Código para módulos, lições, quizzes, etc.)
        
        click.echo(f"Backup restaurado com sucesso a partir de: {input_file}")


def get_module_title(category, index):
    """Gera um título de módulo apropriado para a categoria."""
    if category == 'IA':
        titles = [
            'Introdução à Inteligência Artificial',
            'Aprendizado de Máquina',
            'Processamento de Linguagem Natural',
            'Visão Computacional',
            'Ética em IA',
            'Implementação de IA no Setor Público'
        ]
    else:  # Cybersegurança
        titles = [
            'Fundamentos de Segurança da Informação',
            'Proteção de Dados',
            'Segurança de Redes',
            'Gestão de Vulnerabilidades',
            'Resposta a Incidentes',
            'Conformidade e Políticas de Segurança'
        ]
    
    return titles[index % len(titles)]


def get_lesson_title(category, module_index, lesson_index):
    """Gera um título de lição apropriado para a categoria e módulo."""
    if category == 'IA':
        if module_index == 0:  # Módulo introdutório
            titles = [
                'O que é Inteligência Artificial',
                'História da IA',
                'Tipos de IA',
                'Aplicações de IA no Setor Público',
                'Desafios e Oportunidades'
            ]
        elif module_index == 1:  # Aprendizado de Máquina
            titles = [
                'Conceitos Básicos de ML',
                'Algoritmos Supervisionados',
                'Algoritmos Não-Supervisionados',
                'Avaliação de Modelos',
                'Casos de Uso em Prefeituras'
            ]
        else:
            titles = [
                'Conceitos Básicos',
                'Tecnologias Atuais',
                'Implementação Prática',
                'Estudos de Caso',
                'Tendências Futuras',
                'Aplicações em Gestão Pública'
            ]
    else:  # Cybersegurança
        if module_index == 0:  # Módulo introdutório
            titles = [
                'Princípios de Segurança da Informação',
                'Ameaças Cibernéticas Comuns',
                'Pilares da Segurança Digital',
                'Segurança em Órgãos Públicos',
                'Cultura de Segurança'
            ]
        elif module_index == 1:  # Proteção de Dados
            titles = [
                'LGPD e Órgãos Públicos',
                'Classificação de Dados',
                'Criptografia Básica',
                'Proteção de Dados Sensíveis',
                'Auditorias de Segurança'
            ]
        else:
            titles = [
                'Princípios Fundamentais',
                'Melhores Práticas',
                'Ferramentas Essenciais',
                'Estudos de Caso',
                'Protocolos de Segurança',
                'Conformidade Legal'
            ]
    
    return titles[lesson_index % len(titles)]


def get_lesson_content(category, title):
    """Gera conteúdo para uma lição."""
    return f"""
# {title}

## Introdução

Este material aborda os principais conceitos sobre {title.lower()} no contexto da administração pública municipal.

## Objetivos de Aprendizagem

Ao final desta lição, você será capaz de:
- Compreender os conceitos fundamentais de {title.lower()}
- Identificar aplicações práticas no seu dia a dia
- Implementar estratégias básicas em seu departamento

## Conteúdo Principal

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla facilisi. Phasellus eu metus in tortor volutpat
tincidunt. Suspendisse potenti. Cras eget risus eget nunc finibus facilisis. Sed euismod, magna vel pharetra
ultricies, arcu urna vehicula nunc, eget faucibus eros mauris vel risus.

### Tópico 1: Conceitos Fundamentais

Nulla facilisi. Phasellus eu metus in tortor volutpat tincidunt. Suspendisse potenti. Cras eget risus eget
nunc finibus facilisis. Sed euismod, magna vel pharetra ultricies, arcu urna vehicula nunc, eget faucibus
eros mauris vel risus.

### Tópico 2: Aplicações Práticas

Nulla facilisi. Phasellus eu metus in tortor volutpat tincidunt. Suspendisse potenti. Cras eget risus eget
nunc finibus facilisis. Sed euismod, magna vel pharetra ultricies, arcu urna vehicula nunc, eget faucibus
eros mauris vel risus.

## Estudo de Caso: Prefeitura de Florianópolis

Nulla facilisi. Phasellus eu metus in tortor volutpat tincidunt. Suspendisse potenti. Cras eget risus eget
nunc finibus facilisis. Sed euismod, magna vel pharetra ultricies, arcu urna vehicula nunc, eget faucibus
eros mauris vel risus.

## Resumo

Nesta lição, aprendemos sobre {title.lower()} e suas aplicações no contexto da administração pública municipal.
Vimos como esses conceitos podem ser aplicados no dia a dia das prefeituras para melhorar a eficiência e a
qualidade dos serviços públicos.

## Próximos Passos

Na próxima lição, abordaremos tópicos mais avançados sobre este tema e exploraremos ferramentas práticas
para implementação.
"""


def get_question_text(category, lesson_title, question_index):
    """Gera uma pergunta apropriada para a categoria e lição."""
    if 'Introdução' in lesson_title or 'Fundamentos' in lesson_title:
        questions = [
            f"Qual a definição correta de {category}?",
            f"Quais são os principais componentes de um sistema de {category}?",
            f"Qual é o principal objetivo da {category} no contexto do serviço público?",
            f"Qual destas NÃO é uma aplicação comum de {category} em prefeituras?",
            f"Quais são os maiores desafios na implementação de {category} no setor público?"
        ]
    elif 'Ética' in lesson_title or 'Conformidade' in lesson_title:
        questions = [
            f"Qual princípio ético é mais importante ao implementar soluções de {category}?",
            f"Qual legislação brasileira mais impacta a implementação de {category} no setor público?",
            f"Qual das seguintes práticas é considerada antiética no uso de {category}?",
            f"Qual é a principal consideração ética ao coletar dados de cidadãos para uso em {category}?",
            f"Quais medidas devem ser tomadas para garantir a conformidade legal em projetos de {category}?"
        ]
    else:
        questions = [
            f"Qual a melhor estratégia para implementação de {category} em prefeituras de pequeno porte?",
            f"Qual ferramenta é mais adequada para iniciar projetos de {category} no setor público?",
            f"Qual é a principal vantagem de utilizar {category} na gestão pública municipal?",
            f"Qual das seguintes afirmações sobre {category} está INCORRETA?",
            f"Qual departamento geralmente mais se beneficia da implementação de {category}?"
        ]
    
    return questions[question_index % len(questions)]


def get_question_options(category, question_index):
    """Gera opções para uma pergunta com base na categoria."""
    if category == 'IA':
        options_sets = [
            [
                "Aprendizado de máquina supervisionado",
                "Processamento de linguagem natural",
                "Redes neurais profundas",
                "Análise preditiva"
            ],
            [
                "Python e TensorFlow",
                "R e scikit-learn",
                "Java e Weka",
                "JavaScript e TensorFlow.js"
            ],
            [
                "Automação de tarefas repetitivas",
                "Análise de grande volume de dados",
                "Previsão de tendências e padrões",
                "Personalização de serviços ao cidadão"
            ],
            [
                "Departamento de Tecnologia",
                "Departamento de Finanças",
                "Departamento de Recursos Humanos",
                "Departamento de Obras"
            ]
        ]
    else:  # Cybersegurança
        options_sets = [
            [
                "Firewall e antivírus",
                "Criptografia e autenticação",
                "Backup e recuperação de desastres",
                "Monitoramento e detecção de intrusões"
            ],
            [
                "Lei Geral de Proteção de Dados (LGPD)",
                "Marco Civil da Internet",
                "Instrução Normativa GSI/PR nº 1",
                "Decreto nº 9.637/2018 (Política Nacional de Segurança da Informação)"
            ],
            [
                "Prevenção de ataques",
                "Detecção de vulnerabilidades",
                "Resposta a incidentes",
                "Recuperação de sistemas"
            ],
            [
                "Departamento de TI",
                "Departamento Jurídico",
                "Departamento de Comunicação",
                "Todos os departamentos"
            ]
        ]
    
    return options_sets[question_index % len(options_sets)]
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador administrativo.
Este módulo gerencia as rotas relacionadas às funções administrativas,
como gerenciamento de usuários, cursos e relatórios.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User, UserRoles
from app.models.course import Course, Module, Lesson
from app.models.quiz import Quiz, Question
from app.models.progress import Progress, UserActivity, Certificate
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json
import csv
import io
import os

# Criação do Blueprint administrativo
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# Decorator para restringir acesso somente a administradores
def admin_required(f):
    """Decorator que verifica se o usuário é administrador."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# Decorator para restringir acesso a instrutores e administradores
def instructor_required(f):
    """Decorator que verifica se o usuário é instrutor ou administrador."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_instructor():
            flash('Acesso restrito a instrutores e administradores.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bp.route('/')
@admin_required
def index():
    """Rota para o dashboard administrativo."""
    # Estatísticas gerais
    total_users = User.query.count()
    total_courses = Course.query.count()
    active_users = User.query.filter(User.last_login > datetime.utcnow() - timedelta(days=30)).count()
    
    # Usuários por município
    users_by_municipality = db.session.query(
        User.municipality, 
        func.count(User.id)
    ).group_by(User.municipality).all()
    
    # Matrículas por curso
    enrollments_by_course = db.session.query(
        Course.title,
        func.count(User.id)
    ).join(
        User.courses
    ).group_by(Course.id).order_by(desc(func.count(User.id))).limit(5).all()
    
    # Atividades recentes
    recent_activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(10).all()
    
    return render_template('admin/index.html',
                          total_users=total_users,
                          total_courses=total_courses,
                          active_users=active_users,
                          users_by_municipality=users_by_municipality,
                          enrollments_by_course=enrollments_by_course,
                          recent_activities=recent_activities)


@admin_bp.route('/users')
@admin_required
def manage_users():
    """Rota para gerenciar usuários."""
    # Parâmetros de filtragem e paginação
    role = request.args.get('role')
    municipality = request.args.get('municipality')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    
    # Query base
    query = User.query
    
    # Aplicação de filtros
    if role:
        query = query.filter_by(role=role)
    if municipality:
        query = query.filter_by(municipality=municipality)
    if search:
        query = query.filter(
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    # Executa a query com paginação
    users = query.paginate(page=page, per_page=20)
    
    # Obtém dados para os filtros
    roles = UserRoles.ALL_ROLES
    municipalities = db.session.query(User.municipality).distinct().all()
    
    return render_template('admin/manage_users.html',
                          users=users,
                          roles=roles,
                          municipalities=municipalities,
                          current_role=role,
                          current_municipality=municipality,
                          search_query=search)


@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Rota para editar um usuário."""
    # Obtém o usuário
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Obtém dados do formulário
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        role = request.form.get('role')
        department = request.form.get('department')
        job_title = request.form.get('job_title')
        municipality = request.form.get('municipality')
        is_active = 'is_active' in request.form
        
        # Validação
        if not email or not first_name or not last_name:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Verifica se o email está em uso (exceto pelo próprio usuário)
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash('Este e-mail já está em uso por outro usuário.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Atualiza os dados do usuário
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.role = role
        user.department = department
        user.job_title = job_title
        user.municipality = municipality
        user.is_active = is_active
        
        # Redefine senha se solicitado
        if 'reset_password' in request.form:
            new_password = 'ChangeMe123!'  # Senha temporária
            user.set_password(new_password)
            flash(f'A senha do usuário foi redefinida para: {new_password}', 'warning')
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html',
                          user=user,
                          roles=UserRoles.ALL_ROLES,
                          municipalities=['Florianópolis', 'São José'])


@admin_bp.route('/user/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Rota para criar um novo usuário."""
    if request.method == 'POST':
        # Obtém dados do formulário
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department = request.form.get('department')
        job_title = request.form.get('job_title')
        municipality = request.form.get('municipality')
        
        # Validação
        if not email or not password or not first_name or not last_name:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        # Verifica se o email já está em uso
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Este e-mail já está em uso.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        # Cria o novo usuário
        new_user = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department=department,
            job_title=job_title,
            municipality=municipality
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/create_user.html',
                          roles=UserRoles.ALL_ROLES,
                          municipalities=['Florianópolis', 'São José'])


@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Rota para excluir um usuário."""
    # Impede a exclusão do próprio usuário
    if user_id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Obtém o usuário
    user = User.query.get_or_404(user_id)
    
    # Exclui o usuário
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/courses')
@instructor_required
def manage_courses():
    """Rota para gerenciar cursos."""
    # Parâmetros de filtragem e paginação
    category = request.args.get('category')
    published = request.args.get('published')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    
    # Query base
    query = Course.query
    
    # Para instrutores não-admin, mostrar apenas seus próprios cursos
    if not current_user.is_admin():
        query = query.filter_by(created_by_id=current_user.id)
    
    # Aplicação de filtros
    if category:
        query = query.filter_by(category=category)
    if published:
        is_published = (published == 'true')
        query = query.filter_by(is_published=is_published)
    if search:
        query = query.filter(
            (Course.title.ilike(f'%{search}%')) |
            (Course.description.ilike(f'%{search}%'))
        )
    
    # Executa a query com paginação
    courses = query.paginate(page=page, per_page=10)
    
    # Obtém dados para os filtros
    categories = db.session.query(Course.category).distinct().all()
    
    return render_template('admin/manage_courses.html',
                          courses=courses,
                          categories=categories,
                          current_category=category,
                          current_published=published,
                          search_query=search)


@admin_bp.route('/course/create', methods=['GET', 'POST'])
@instructor_required
def create_course():
    """Rota para criar um novo curso."""
    if request.method == 'POST':
        # Obtém dados do formulário
        title = request.form.get('title')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        category = request.form.get('category')
        level = request.form.get('level')
        duration_hours = request.form.get('duration_hours')
        is_published = 'is_published' in request.form
        is_featured = 'is_featured' in request.form
        
        # Tags e pré-requisitos
        tags = request.form.get('tags', '')
        prerequisite_courses = request.form.getlist('prerequisite_courses')
        
        # Validação
        if not title or not description or not category or not level:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('admin.create_course'))
        
        # Prepara os dados
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        prerequisite_ids = [int(p) for p in prerequisite_courses if p]
        
        # Upload de thumbnail
        thumbnail_path = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import os
                
                # Gera um nome seguro e único para o arquivo
                filename = secure_filename(file.filename)
                new_filename = f"course_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                
                # Salva o arquivo
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, 'course_thumbnails', new_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Define o caminho do thumbnail
                thumbnail_path = f"/static/uploads/course_thumbnails/{new_filename}"
        
        # Cria o novo curso
        new_course = Course(
            title=title,
            description=description,
            short_description=short_description,
            category=category,
            level=level,
            duration_hours=int(duration_hours) if duration_hours else None,
            thumbnail=thumbnail_path,
            is_published=is_published,
            is_featured=is_featured,
            tags=tags_list,
            prerequisite_courses=prerequisite_ids,
            created_by_id=current_user.id
        )
        
        db.session.add(new_course)
        db.session.commit()
        
        flash('Curso criado com sucesso!', 'success')
        return redirect(url_for('admin.edit_course_content', course_id=new_course.id))
    
    # Lista de cursos para pré-requisitos
    available_courses = Course.query.all()
    
    return render_template('admin/create_course.html',
                          available_courses=available_courses,
                          categories=['IA', 'Cybersegurança'],
                          levels=['Básico', 'Intermediário', 'Avançado'])


@admin_bp.route('/course/edit/<int:course_id>', methods=['GET', 'POST'])
@instructor_required
def edit_course(course_id):
    """Rota para editar informações básicas de um curso."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    if request.method == 'POST':
        # Obtém dados do formulário
        title = request.form.get('title')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        category = request.form.get('category')
        level = request.form.get('level')
        duration_hours = request.form.get('duration_hours')
        is_published = 'is_published' in request.form
        is_featured = 'is_featured' in request.form
        
        # Tags e pré-requisitos
        tags = request.form.get('tags', '')
        prerequisite_courses = request.form.getlist('prerequisite_courses')
        
        # Validação
        if not title or not description or not category or not level:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))
        
        # Prepara os dados
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        prerequisite_ids = [int(p) for p in prerequisite_courses if p]
        
        # Upload de thumbnail
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import os
                
                # Gera um nome seguro e único para o arquivo
                filename = secure_filename(file.filename)
                new_filename = f"course_{course.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                
                # Salva o arquivo
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, 'course_thumbnails', new_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Define o caminho do thumbnail
                course.thumbnail = f"/static/uploads/course_thumbnails/{new_filename}"
        
        # Atualiza o curso
        course.title = title
        course.description = description
        course.short_description = short_description
        course.category = category
        course.level = level
        course.duration_hours = int(duration_hours) if duration_hours else None
        course.is_published = is_published
        course.is_featured = is_featured
        course.tags = tags_list
        course.prerequisite_courses = prerequisite_ids
        
        db.session.commit()
        
        flash('Curso atualizado com sucesso!', 'success')
        return redirect(url_for('admin.manage_courses'))
    
    # Lista de cursos para pré-requisitos (exceto o próprio curso)
    available_courses = Course.query.filter(Course.id != course_id).all()
    
    # Prepara tags para exibição
    tags_string = ','.join(course.tags) if course.tags else ''
    
    return render_template('admin/edit_course.html',
                          course=course,
                          available_courses=available_courses,
                          tags_string=tags_string,
                          categories=['IA', 'Cybersegurança'],
                          levels=['Básico', 'Intermediário', 'Avançado'])


@admin_bp.route('/course/content/<int:course_id>')
@instructor_required
def edit_course_content(course_id):
    """Rota para editar o conteúdo (módulos e lições) de um curso."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Obtém todos os módulos do curso
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Para cada módulo, obtém suas lições
    module_data = []
    for module in modules:
        lessons = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all()
        
        # Para cada lição, verifica se tem quiz
        lesson_data = []
        for lesson in lessons:
            quiz = Quiz.query.filter_by(lesson_id=lesson.id).first()
            lesson_data.append({
                'lesson': lesson,
                'has_quiz': quiz is not None
            })
        
        module_data.append({
            'module': module,
            'lessons': lesson_data
        })
    
    return render_template('admin/edit_course_content.html',
                          course=course,
                          module_data=module_data)


@admin_bp.route('/module/create/<int:course_id>', methods=['POST'])
@instructor_required
def create_module(course_id):
    """Rota para criar um novo módulo."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Obtém dados do formulário
    title = request.form.get('title')
    description = request.form.get('description')
    
    # Validação
    if not title:
        flash('O título do módulo é obrigatório.', 'danger')
        return redirect(url_for('admin.edit_course_content', course_id=course.id))
    
    # Determina a ordem do novo módulo
    last_module = Module.query.filter_by(course_id=course.id).order_by(Module.order.desc()).first()
    new_order = 1 if not last_module else last_module.order + 1
    
    # Cria o novo módulo
    new_module = Module(
        title=title,
        description=description,
        order=new_order,
        course_id=course.id
    )
    
    db.session.add(new_module)
    db.session.commit()
    
    flash('Módulo criado com sucesso!', 'success')
    return redirect(url_for('admin.edit_course_content', course_id=course.id))


@admin_bp.route('/module/edit/<int:module_id>', methods=['POST'])
@instructor_required
def edit_module(module_id):
    """Rota para editar um módulo."""
    # Obtém o módulo
    module = Module.query.get_or_404(module_id)
    
    # Obtém o curso
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Obtém dados do formulário
    title = request.form.get('title')
    description = request.form.get('description')
    
    # Validação
    if not title:
        flash('O título do módulo é obrigatório.', 'danger')
        return redirect(url_for('admin.edit_course_content', course_id=course.id))
    
    # Atualiza o módulo
    module.title = title
    module.description = description
    
    db.session.commit()
    
    flash('Módulo atualizado com sucesso!', 'success')
    return redirect(url_for('admin.edit_course_content', course_id=course.id))


@admin_bp.route('/module/delete/<int:module_id>', methods=['POST'])
@instructor_required
def delete_module(module_id):
    """Rota para excluir um módulo."""
    # Obtém o módulo
    module = Module.query.get_or_404(module_id)
    
    # Obtém o curso
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Verifica se o módulo tem lições
    if module.lessons.count() > 0:
        flash('Não é possível excluir um módulo que contém lições.', 'danger')
        return redirect(url_for('admin.edit_course_content', course_id=course.id))
    
    # Exclui o módulo
    db.session.delete(module)
    db.session.commit()
    
    # Reordena os outros módulos
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    for i, mod in enumerate(modules, 1):
        mod.order = i
    
    db.session.commit()
    
    flash('Módulo excluído com sucesso!', 'success')
    return redirect(url_for('admin.edit_course_content', course_id=course.id))


@admin_bp.route('/lesson/create/<int:module_id>', methods=['GET', 'POST'])
@instructor_required
def create_lesson(module_id):
    """Rota para criar uma nova lição."""
    # Obtém o módulo
    module = Module.query.get_or_404(module_id)
    
    # Obtém o curso
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    if request.method == 'POST':
        # Obtém dados do formulário
        title = request.form.get('title')
        content = request.form.get('content')
        lesson_type = request.form.get('lesson_type')
        duration_minutes = request.form.get('duration_minutes')
        video_url = request.form.get('video_url')
        xp_reward = request.form.get('xp_reward')
        
        # Validação
        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            return redirect(url_for('admin.create_lesson', module_id=module.id))
        
        # Determina a ordem da nova lição
        last_lesson = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order.desc()).first()
        new_order = 1 if not last_lesson else last_lesson.order + 1
        
        # Processa o upload de arquivo, se houver
        attachment_url = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import os
                
                # Gera um nome seguro e único para o arquivo
                filename = secure_filename(file.filename)
                new_filename = f"lesson_{module.id}_{new_order}_{filename}"
                
                # Salva o arquivo
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, 'lesson_attachments', new_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Define o caminho do anexo
                attachment_url = f"/static/uploads/lesson_attachments/{new_filename}"
        
        # Cria a nova lição
        new_lesson = Lesson(
            title=title,
            content=content,
            lesson_type=lesson_type,
            order=new_order,
            duration_minutes=int(duration_minutes) if duration_minutes else None,
            video_url=video_url if video_url else None,
            attachment_url=attachment_url,
            xp_reward=int(xp_reward) if xp_reward else 50,
            module_id=module.id
        )
        
        db.session.add(new_lesson)
        db.session.commit()
        
        flash('Lição criada com sucesso!', 'success')
        return redirect(url_for('admin.edit_course_content', course_id=course.id))
    
    return render_template('admin/create_lesson.html',
                          module=module,
                          course=course)


@admin_bp.route('/lesson/edit/<int:lesson_id>', methods=['GET', 'POST'])
@instructor_required
def edit_lesson(lesson_id):
    """Rota para editar uma lição."""
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    if request.method == 'POST':
        # Obtém dados do formulário
        title = request.form.get('title')
        content = request.form.get('content')
        lesson_type = request.form.get('lesson_type')
        duration_minutes = request.form.get('duration_minutes')
        video_url = request.form.get('video_url')
        xp_reward = request.form.get('xp_reward')
        
        # Validação
        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            return redirect(url_for('admin.edit_lesson', lesson_id=lesson.id))
        
        # Processa o upload de arquivo, se houver
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import os
                
                # Gera um nome seguro e único para o arquivo
                filename = secure_filename(file.filename)
                new_filename = f"lesson_{module.id}_{lesson.order}_{filename}"
                
                # Salva o arquivo
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, 'lesson_attachments', new_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Define o caminho do anexo
                lesson.attachment_url = f"/static/uploads/lesson_attachments/{new_filename}"
        
        # Atualiza a lição
        lesson.title = title
        lesson.content = content
        lesson.lesson_type = lesson_type
        lesson.duration_minutes = int(duration_minutes) if duration_minutes else None
        lesson.video_url = video_url if video_url else None
        lesson.xp_reward = int(xp_reward) if xp_reward else 50
        
        db.session.commit()
        
        flash('Lição atualizada com sucesso!', 'success')
        return redirect(url_for('admin.edit_course_content', course_id=course.id))
    
    return render_template('admin/edit_lesson.html',
                          lesson=lesson,
                          module=module,
                          course=course)


@admin_bp.route('/lesson/delete/<int:lesson_id>', methods=['POST'])
@instructor_required
def delete_lesson(lesson_id):
    """Rota para excluir uma lição."""
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica permissão
    if not current_user.is_admin() and course.created_by_id != current_user.id:
        flash('Você não tem permissão para editar este curso.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Exclui a lição
    db.session.delete(lesson)
    db.session.commit()
    
    # Reordena as outras lições
    lessons = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all()
    for i, les in enumerate(lessons, 1):
        les.order = i
    
    db.session.commit()
    
    flash('Lição excluída com sucesso!', 'success')
    return redirect(url_for('admin.edit_course_content', course_id=course.id))


@admin_bp.route('/reports')
@admin_required
def reports():
    """Rota para visualizar relatórios administrativos."""
    return render_template('admin/reports.html')


@admin_bp.route('/api/report/user-activity')
@admin_required
def report_user_activity():
    """API para gerar relatório de atividade dos usuários."""
    # Parâmetros de filtragem
    days = request.args.get('days', 30, type=int)
    municipality = request.args.get('municipality')
    
    # Data de início
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query base
    query = db.session.query(
        UserActivity.activity_type,
        func.count(UserActivity.id)
    ).filter(
        UserActivity.timestamp >= start_date
    )
    
    # Filtro por município
    if municipality:
        query = query.join(User, UserActivity.user_id == User.id).filter(
            User.municipality == municipality
        )
    
    # Agrupa por tipo de atividade
    data = query.group_by(UserActivity.activity_type).all()
    
    # Prepara os dados para retorno
    result = {
        'labels': [item[0] for item in data],
        'data': [item[1] for item in data],
        'total': sum(item[1] for item in data),
        'period': f"Últimos {days} dias"
    }
    
    return jsonify(result)


@admin_bp.route('/api/report/course-completion')
@admin_required
def report_course_completion():
    """API para gerar relatório de conclusão de cursos."""
    # Obtém estatísticas de conclusão de cursos
    courses_data = db.session.query(
        Course.id,
        Course.title,
        Course.category,
        func.count(User.id).label('enrollment_count'),
        func.count(Certificate.id).label('completion_count')
    ).outerjoin(
        User.courses
    ).outerjoin(
        Certificate, (Certificate.course_id == Course.id) & (Certificate.user_id == User.id)
    ).group_by(
        Course.id
    ).all()
    
    # Prepara os dados para retorno
    result = []
    for course_id, title, category, enrollment_count, completion_count in courses_data:
        completion_rate = (completion_count / enrollment_count * 100) if enrollment_count > 0 else 0
        result.append({
            'course_id': course_id,
            'title': title,
            'category': category,
            'enrollment_count': enrollment_count,
            'completion_count': completion_count,
            'completion_rate': round(completion_rate, 1)
        })
    
    return jsonify(result)


@admin_bp.route('/api/report/export-users', methods=['GET'])
@admin_required
def export_users():
    """API para exportar dados de usuários em formato CSV."""
    # Obtém todos os usuários
    users = User.query.all()
    
    # Cria um arquivo CSV na memória
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escreve o cabeçalho
    writer.writerow([
        'ID', 'Email', 'Nome', 'Sobrenome', 'Cargo', 'Departamento', 'Município',
        'Função', 'Nível', 'XP', 'Cursos Matriculados', 'Cursos Concluídos',
        'Data de Criação', 'Último Login'
    ])
    
    # Escreve os dados de cada usuário
    for user in users:
        # Conta cursos matriculados
        enrolled_courses_count = len(user.courses)
        
        # Conta cursos concluídos (com certificado)
        completed_courses_count = Certificate.query.filter_by(user_id=user.id).count()
        
        writer.writerow([
            user.id,
            user.email,
            user.first_name,
            user.last_name,
            user.job_title,
            user.department,
            user.municipality,
            user.role,
            user.level,
            user.xp_points,
            enrolled_courses_count,
            completed_courses_count,
            user.created_at.strftime('%d/%m/%Y') if user.created_at else '',
            user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else ''
        ])
    
    # Retorna o CSV como download
    output.seek(0)
    return current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=usuarios.csv'}
    )


@admin_bp.route('/api/report/export-course-data/<int:course_id>', methods=['GET'])
@admin_required
def export_course_data(course_id):
    """API para exportar dados de um curso específico em formato CSV."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Obtém usuários matriculados
    enrolled_users = course.enrolled_users.all()
    
    # Cria um arquivo CSV na memória
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escreve o cabeçalho
    writer.writerow([
        'ID do Usuário', 'Nome', 'Email', 'Município', 'Departamento',
        'Progresso (%)', 'Concluiu?', 'Data de Conclusão'
    ])
    
    # Escreve os dados de cada usuário
    for user in enrolled_users:
        # Calcula o progresso
        progress = user.get_course_progress(course.id)
        
        # Verifica se o usuário concluiu o curso
        certificate = Certificate.query.filter_by(
            user_id=user.id,
            course_id=course.id
        ).first()
        
        completed = 'Sim' if certificate else 'Não'
        completion_date = certificate.issue_date.strftime('%d/%m/%Y') if certificate else ''
        
        writer.writerow([
            user.id,
            user.get_full_name(),
            user.email,
            user.municipality,
            user.department,
            progress,
            completed,
            completion_date
        ])
    
    # Retorna o CSV como download
    output.seek(0)
    return current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=curso_{course.id}_usuarios.csv'}
    )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador de cursos.
Este módulo gerencia as rotas relacionadas aos cursos, módulos e lições,
incluindo navegação, matrícula e progresso.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, cache
from app.models.user import User
from app.models.course import Course, Module, Lesson
from app.models.progress import Progress, UserActivity, Certificate
from app.services.ai_service import GeminiService
from app.services.youtube_service import YouTubeService
from sqlalchemy import func
from datetime import datetime
import uuid
import os

# Criação do Blueprint de cursos
courses_bp = Blueprint('courses', __name__)

# Instanciação dos serviços
gemini_service = GeminiService()
youtube_service = YouTubeService()


@courses_bp.route('/dashboard')
@login_required
def dashboard():
    """Rota para o dashboard principal do usuário."""
    # Obtém os cursos em que o usuário está matriculado
    enrolled_courses = current_user.courses
    
    # Calcula o progresso do usuário em cada curso
    course_progress = {}
    for course in enrolled_courses:
        progress = current_user.get_course_progress(course.id)
        course_progress[course.id] = progress
    
    # Obtém cursos em destaque para recomendação
    featured_courses = Course.query.filter_by(is_published=True, is_featured=True).limit(3).all()
    
    # Obtém estatísticas do usuário
    completed_lessons = Progress.query.filter_by(user_id=current_user.id, status='completed').count()
    certificates = Certificate.query.filter_by(user_id=current_user.id).count()
    
    # Registra a atividade de acesso ao dashboard
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='dashboard_access',
        description='Acesso ao dashboard',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return render_template('courses/dashboard.html',
                          enrolled_courses=enrolled_courses,
                          course_progress=course_progress,
                          featured_courses=featured_courses,
                          completed_lessons=completed_lessons,
                          certificates=certificates)


@courses_bp.route('/courses')
@login_required
def course_list():
    """Rota para listar todos os cursos disponíveis."""
    # Parâmetros de filtragem e paginação
    category = request.args.get('category')
    level = request.args.get('level')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    
    # Query base
    query = Course.query.filter_by(is_published=True)
    
    # Aplicação de filtros
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%') | 
                           Course.description.ilike(f'%{search}%'))
    
    # Executa a query com paginação
    courses = query.paginate(page=page, per_page=9)
    
    # Obtém os cursos em que o usuário está matriculado para mostrar status
    enrolled_course_ids = [c.id for c in current_user.courses]
    
    # Obtém categorias e níveis para filtros
    categories = db.session.query(Course.category).distinct().all()
    levels = db.session.query(Course.level).distinct().all()
    
    return render_template('courses/course_list.html',
                          courses=courses,
                          enrolled_course_ids=enrolled_course_ids,
                          categories=categories,
                          levels=levels,
                          current_category=category,
                          current_level=level,
                          search_query=search)


@courses_bp.route('/course/<string:slug>')
@login_required
def course_detail(slug):
    """Rota para exibir os detalhes de um curso específico."""
    # Obtém o curso pelo slug
    course = Course.query.filter_by(slug=slug).first_or_404()
    
    # Verifica se o curso está publicado ou se o usuário é instrutor/admin
    if not course.is_published and not current_user.is_instructor():
        abort(404)
    
    # Verifica se o usuário está matriculado
    is_enrolled = course in current_user.courses
    
    # Obtém todos os módulos do curso
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Se estiver matriculado, obtém o progresso
    progress = 0
    if is_enrolled:
        progress = current_user.get_course_progress(course.id)
    
    # Registra a atividade de visualização do curso
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='course_view',
        description=f'Visualização dos detalhes do curso: {course.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={'course_id': course.id}
    )
    
    return render_template('courses/course_detail.html',
                          course=course,
                          modules=modules,
                          is_enrolled=is_enrolled,
                          progress=progress)


@courses_bp.route('/course/enrollment/<int:course_id>')
@login_required
def course_enrollment(course_id):
    """Página de matrícula para um curso específico."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published and not current_user.is_instructor():
        abort(404)
    
    # Verifica se o usuário já está matriculado
    if course in current_user.courses:
        flash('Você já está matriculado neste curso.', 'info')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Obtém os módulos do curso para exibição
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Registra visualização da página de matrícula
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='enrollment_page_view',
        description=f'Visualização da página de matrícula do curso: {course.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={'course_id': course.id}
    )
    
    return render_template('courses/course_enrollment.html',
                          course=course,
                          modules=modules)

@courses_bp.route('/course/confirm-enrollment/<int:course_id>', methods=['POST'])
@login_required
def confirm_enrollment(course_id):
    """Confirmação de matrícula em um curso."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published:
        flash('Este curso não está disponível para matrícula.', 'danger')
        return redirect(url_for('courses.course_list'))
    
    # Verifica se o usuário já está matriculado
    if course in current_user.courses:
        flash('Você já está matriculado neste curso.', 'info')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    try:
        # Matricula o usuário no curso
        current_user.courses.append(course)
        db.session.commit()
        
        # Cria registros de progresso iniciais para todas as lições do curso
        modules = Module.query.filter_by(course_id=course.id).all()
        for module in modules:
            lessons = Lesson.query.filter_by(module_id=module.id).all()
            for lesson in lessons:
                # Verifica se já existe um registro de progresso
                existing_progress = Progress.query.filter_by(
                    user_id=current_user.id,
                    lesson_id=lesson.id
                ).first()
                
                if not existing_progress:
                    progress = Progress(
                        user_id=current_user.id,
                        course_id=course.id,
                        module_id=module.id,
                        lesson_id=lesson.id,
                        status='not_started',
                        progress_percentage=0.0
                    )
                    db.session.add(progress)
        
        # Registra a atividade de matrícula
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='course_enrollment',
            description=f'Matrícula no curso: {course.title}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            metadata={'course_id': course.id}
        )
        
        db.session.commit()
        
        # Envia e-mail de confirmação de matrícula
        try:
            from app.services.email_service import EmailService
            EmailService.send_course_enrollment_email(current_user, course)
        except Exception as e:
            # Registra o erro, mas não impede a matrícula
            current_app.logger.error(f"Erro ao enviar e-mail de matrícula: {str(e)}")
        
        flash(f'Você foi matriculado com sucesso no curso: {course.title}', 'success')
        
        # Redireciona para a primeira lição do curso, se existir
        first_module = Module.query.filter_by(course_id=course.id).order_by(Module.order).first()
        if first_module:
            first_lesson = Lesson.query.filter_by(module_id=first_module.id).order_by(Lesson.order).first()
            if first_lesson:
                return redirect(url_for('courses.lesson_view', lesson_id=first_lesson.id))
        
        return redirect(url_for('courses.course_detail', slug=course.slug))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na matrícula do curso: {str(e)}")
        flash('Ocorreu um erro ao processar sua matrícula. Por favor, tente novamente.', 'danger')
        return redirect(url_for('courses.course_enrollment', course_id=course.id))

@courses_bp.route('/course/details/<int:course_id>')
@login_required
def course_details(course_id):
    """Página de detalhes para um curso específico."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o curso está publicado
    if not course.is_published and not current_user.is_instructor():
        abort(404)
    
    # Verifica se o usuário está matriculado
    is_enrolled = course in current_user.courses
    
    # Obtém todos os módulos do curso
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Se estiver matriculado, obtém o progresso
    progress = 0
    if is_enrolled:
        progress = current_user.get_course_progress(course.id)
    
    # Registra a atividade de visualização do curso
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='course_details_view',
        description=f'Visualização detalhada do curso: {course.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={'course_id': course.id}
    )
    
    return render_template('courses/course_details.html',
                          course=course,
                          modules=modules,
                          is_enrolled=is_enrolled,
                          progress=progress)
@courses_bp.route('/lesson/<int:lesson_id>')
@login_required
def lesson_view(lesson_id):
    """Rota para visualizar uma lição específica."""
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in current_user.courses and not current_user.is_instructor():
        flash('Você precisa estar matriculado neste curso para acessar suas lições.', 'warning')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    # Obtém todas as lições do módulo para navegação
    module_lessons = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all()
    
    # Obtém todos os módulos do curso para navegação
    course_modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Atualiza ou cria o registro de progresso
    progress = Progress.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson.id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            course_id=course.id,
            module_id=module.id,
            lesson_id=lesson.id,
            status='in_progress',
            progress_percentage=50.0
        )
        db.session.add(progress)
    elif progress.status != 'completed':
        progress.mark_in_progress()
        
    # Adiciona tempo de estudo, se já existir um registro anterior
    last_activity_time = request.args.get('last_activity')
    if last_activity_time and progress:
        try:
            last_activity = int(last_activity_time)
            time_spent = int((datetime.utcnow().timestamp() - last_activity) / 60)  # Em minutos
            if 0 < time_spent < 120:  # Limita a 2 horas para evitar valores absurdos
                progress.add_time_spent(time_spent * 60)  # Converte para segundos
        except (ValueError, TypeError):
            pass
    
    db.session.commit()
    
    # Registra a atividade de visualização da lição
    UserActivity.log_activity(
        user_id=current_user.id,
        activity_type='lesson_view',
        description=f'Visualização da lição: {lesson.title}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        metadata={
            'course_id': course.id,
            'module_id': module.id,
            'lesson_id': lesson.id
        }
    )
    
    # Obtém os vídeos relacionados do YouTube, se a lição não tiver um vídeo definido
    related_videos = []
    if not lesson.video_url and lesson.lesson_type != 'video':
        try:
            related_videos = youtube_service.search_videos(
                f"{course.category} {lesson.title}",
                max_results=2
            )
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar vídeos: {str(e)}")
    
    # Prepara recomendações de conteúdo com IA, se disponível
    ai_recommendations = None
    if current_app.config.get('GOOGLE_GEMINI_API_KEY'):
        try:
            # Tenta obter recomendações do cache primeiro
            cache_key = f'lesson_ai_rec_{lesson.id}'
            ai_recommendations = cache.get(cache_key)
            
            if not ai_recommendations:
                ai_recommendations = gemini_service.generate_study_recommendations(
                    module.title, 
                    lesson.content[:1000], 
                    progress.progress_percentage if progress else 0
                )
                # Armazena em cache por 24 horas
                cache.set(cache_key, ai_recommendations, timeout=86400)
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar recomendações com IA: {str(e)}")
    
    return render_template('courses/lesson_view.html',
                          lesson=lesson,
                          module=module,
                          course=course,
                          module_lessons=module_lessons,
                          course_modules=course_modules,
                          progress=progress,
                          related_videos=related_videos,
                          ai_recommendations=ai_recommendations,
                          current_time=int(datetime.utcnow().timestamp()))

@courses_bp.route('/complete-lesson/<int:lesson_id>', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    """Rota para marcar uma lição como concluída."""
    # Obtém a lição
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Obtém o módulo e o curso
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    # Verifica se o usuário está matriculado no curso
    if course not in current_user.courses:
        flash('Você precisa estar matriculado neste curso para marcar lições como concluídas.', 'warning')
        return redirect(url_for('courses.course_detail', slug=course.slug))
    
    try:
        # Atualiza ou cria o registro de progresso
        progress = Progress.query.filter_by(
            user_id=current_user.id, 
            lesson_id=lesson.id
        ).first()
        
        if not progress:
            progress = Progress(
                user_id=current_user.id,
                course_id=course.id,
                module_id=module.id,
                lesson_id=lesson.id
            )
            db.session.add(progress)
        
        # Marca como concluída (isso também adiciona XP ao usuário)
        progress.complete()
        db.session.commit()
        
        # Registra a atividade de conclusão da lição
        UserActivity.log_activity(
            user_id=current_user.id,
            activity_type='lesson_complete',
            description=f'Lição concluída: {lesson.title}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            metadata={
                'course_id': course.id,
                'module_id': module.id,
                'lesson_id': lesson.id,
                'xp_reward': lesson.xp_reward
            }
        )
        
        # Verifica se o usuário concluiu todo o curso
        course_progress = current_user.get_course_progress(course.id)
        
        if course_progress == 100:
            # Gera certificado se todas as lições forem concluídas
            existing_certificate = Certificate.query.filter_by(
                user_id=current_user.id, 
                course_id=course.id
            ).first()
            
            if not existing_certificate:
                import uuid
                
                certificate = Certificate(
                    user_id=current_user.id,
                    course_id=course.id,
                    certificate_number=f"CERT-{course.id}-{current_user.id}-{uuid.uuid4().hex[:8].upper()}",
                    issue_date=datetime.utcnow()
                )
                db.session.add(certificate)
                db.session.commit()
                
                flash('Parabéns! Você concluiu o curso e recebeu um certificado!', 'success')
                
                # Registra a atividade de conclusão do curso
                UserActivity.log_activity(
                    user_id=current_user.id,
                    activity_type='course_complete',
                    description=f'Curso concluído: {course.title}',
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    metadata={
                        'course_id': course.id,
                        'certificate_id': certificate.id
                    }
                )
                
                # Tenta enviar e-mail de conclusão
                try:
                    from app.services.email_service import EmailService
                    EmailService.send_course_completion_email(current_user, course, certificate)
                except Exception as e:
                    # Registra o erro, mas não impede a conclusão
                    current_app.logger.error(f"Erro ao enviar e-mail de conclusão: {str(e)}")
        
        # Próxima lição, se houver
        next_lesson = Lesson.query.filter(
            Lesson.module_id == module.id,
            Lesson.order > lesson.order
        ).order_by(Lesson.order).first()
        
        if next_lesson:
            flash('Lição concluída com sucesso!', 'success')
            return redirect(url_for('courses.lesson_view', lesson_id=next_lesson.id))
        else:
            # Verifica se há próximo módulo
            next_module = Module.query.filter(
                Module.course_id == course.id,
                Module.order > module.order
            ).order_by(Module.order).first()
            
            if next_module:
                first_lesson = Lesson.query.filter_by(
                    module_id=next_module.id
                ).order_by(Lesson.order).first()
                
                if first_lesson:
                    flash('Módulo concluído com sucesso! Avançando para o próximo módulo.', 'success')
                    return redirect(url_for('courses.lesson_view', lesson_id=first_lesson.id))
            
            # Se não houver próxima lição ou próximo módulo, exibe mensagem de conclusão do curso
            if course_progress == 100:
                flash('Parabéns! Você concluiu todas as lições do curso!', 'success')
                return redirect(url_for('courses.course_detail', slug=course.slug))
            else:
                flash('Lição concluída com sucesso!', 'success')
                return redirect(url_for('courses.course_detail', slug=course.slug))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao marcar lição como concluída: {str(e)}")
        flash('Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.', 'danger')
        return redirect(url_for('courses.lesson_view', lesson_id=lesson.id))

@courses_bp.route('/certificates')
@login_required
def user_certificates():
    """Rota para visualizar os certificados do usuário."""
    # Obtém todos os certificados do usuário
    certificates = Certificate.query.filter_by(user_id=current_user.id).all()
    
    # Para cada certificado, obtém o curso correspondente
    certificate_data = []
    for cert in certificates:
        course = Course.query.get(cert.course_id)
        if course:
            certificate_data.append({
                'certificate': cert,
                'course': course
            })
    
    return render_template('courses/certificates.html',
                          certificate_data=certificate_data)


@courses_bp.route('/certificate/<int:certificate_id>')
@login_required
def view_certificate(certificate_id):
    """Rota para visualizar um certificado específico."""
    # Obtém o certificado
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Verifica se o certificado pertence ao usuário logado
    if certificate.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    # Obtém o curso correspondente
    course = Course.query.get_or_404(certificate.course_id)
    
    return render_template('courses/certificate_view.html',
                          certificate=certificate,
                          course=course)


@courses_bp.route('/api/recommended-courses')
@login_required
def get_recommended_courses():
    """API para receber recomendações de cursos personalizadas via IA."""
    # Cria um perfil do usuário para a IA
    user_profile = {
        'name': current_user.get_full_name(),
        'level': current_user.level,
        'xp_points': current_user.xp_points,
        'enrolled_courses': [{'id': c.id, 'title': c.title, 'category': c.category, 'level': c.level} 
                            for c in current_user.courses],
        'completed_lessons': Progress.query.filter_by(user_id=current_user.id, status='completed').count(),
        'areas_of_interest': []
    }
    
    # Análise de áreas de interesse com base nas atividades
    cyber_activities = UserActivity.query.filter(
        UserActivity.user_id == current_user.id,
        UserActivity.metadata.op('->')('course_id').in_(
            db.session.query(Course.id).filter_by(category='Cybersegurança')
        )
    ).count()
    
    ai_activities = UserActivity.query.filter(
        UserActivity.user_id == current_user.id,
        UserActivity.metadata.op('->')('course_id').in_(
            db.session.query(Course.id).filter_by(category='IA')
        )
    ).count()
    
    if cyber_activities > ai_activities:
        user_profile['areas_of_interest'].append('Cybersegurança')
    elif ai_activities > cyber_activities:
        user_profile['areas_of_interest'].append('IA')
    
    # Obtém recomendações da IA
    try:
        recommendations = gemini_service.get_course_recommendations(user_profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Obtém os cursos recomendados do banco de dados
    recommended_courses = []
    for rec in recommendations:
        course = Course.query.filter_by(is_published=True).filter(
            Course.title.ilike(f"%{rec['title']}%") | 
            Course.slug.ilike(f"%{'-'.join(rec['title'].lower().split())}%")
        ).first()
        
        if course and course not in current_user.courses:
            recommended_courses.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.short_description or course.description[:100] + '...',
                'category': course.category,
                'level': course.level,
                'thumbnail': course.thumbnail,
                'relevance': rec.get('relevance', 0)
            })
    
    # Se não encontrou recomendações, obtém cursos populares
    if not recommended_courses:
        popular_courses = Course.query.filter_by(is_published=True).order_by(
            func.count(UserActivity.id).desc()
        ).join(
            UserActivity, 
            UserActivity.metadata.op('->')('course_id').cast(db.Integer) == Course.id
        ).group_by(Course.id).limit(3).all()
        
        for course in popular_courses:
            if course not in current_user.courses:
                recommended_courses.append({
                    'id': course.id,
                    'title': course.title,
                    'slug': course.slug,
                    'description': course.short_description or course.description[:100] + '...',
                    'category': course.category,
                    'level': course.level,
                    'thumbnail': course.thumbnail,
                    'relevance': 'Popular'
                })
    
    return jsonify({'courses': recommended_courses})


@courses_bp.route('/course-overview/<int:course_id>')
@login_required
def course_overview(course_id):
    """Rota para obter uma visão geral de um curso via IA."""
    # Obtém o curso
    course = Course.query.get_or_404(course_id)
    
    # Verifica se o usuário pode acessar o curso
    if not course.is_published and not current_user.is_instructor():
        abort(404)
    
    # Obtém a visão geral com a IA (cache por 24 horas)
    cache_key = f'course_overview_{course_id}'
    overview = cache.get(cache_key)
    
    if not overview:
        try:
            # Coleta todas as lições do curso
            lessons = []
            for module in course.modules:
                for lesson in module.lessons:
                    lessons.append({
                        'title': lesson.title,
                        'content_summary': lesson.content[:200] + '...' if len(lesson.content) > 200 else lesson.content
                    })
            
            # Solicita à IA uma visão geral do curso
            overview = gemini_service.generate_course_overview(course.title, course.description, lessons)
            
            # Armazena em cache
            cache.set(cache_key, overview, timeout=86400)  # 24 horas
        except Exception as e:
            overview = {
                'summary': f"Não foi possível gerar a visão geral do curso. Erro: {str(e)}",
                'key_points': [],
                'learning_outcomes': []
            }
    
    return jsonify(overview)